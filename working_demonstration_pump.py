"""Import the neighbouring pump-holder project and route its hose in world mm."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import trimesh
import yaml
from shapely.geometry import Point

from working_pump_lifter import get_layout
from working_oomp_populate import get_options, build_oomp_id
from working_split_parts import halves, mesh_path


PUMP_PLACEMENT = {
    'project_folder': 'oomlout_oobb_holder_motor_pump_submersible_jt_500',
    'axial_position_mm': 285.0,
    'rear_riser_position_mm': 125.0,
    'hose_socket_above_body_mm': 8.0,
    'hose_side_control_mm': -175.0,
    'pump_rotation_degrees': 180.0,
    'pump_rotation_in_holder_degrees': 180.0,
}


def sweep_hose(points, outer_radius, inner_radius):
    """Closed annular mesh with parallel-transport frames and open bore ends."""
    points = np.asarray(points, dtype=float)
    tangents = np.gradient(points, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1)[:, None]
    normal = np.cross(tangents[0], [1, 0, 0])
    normal /= np.linalg.norm(normal)
    rings = []
    angles = np.arange(64) * (2 * np.pi / 64)
    for i, tangent in enumerate(tangents):
        if i:
            previous = tangents[i - 1]
            axis = np.cross(previous, tangent)
            sine = np.linalg.norm(axis)
            if sine > 1e-10:
                axis /= sine
                cosine = np.dot(previous, tangent)
                normal = normal * cosine + np.cross(axis, normal) * sine + axis * np.dot(axis, normal) * (1 - cosine)
        binormal = np.cross(tangent, normal)
        radial = np.cos(angles)[:, None] * normal + np.sin(angles)[:, None] * binormal
        rings.append(np.concatenate([points[i] + outer_radius * radial,
                                     points[i] + inner_radius * radial]))
    faces = []
    for i in range(len(points) - 1):
        for layer in (0, 64):
            for j in range(64):
                a, b = i * 128 + layer + j, i * 128 + layer + (j + 1) % 64
                c, d = a + 128, b + 128
                faces.extend([(a, b, d), (a, d, c)] if layer == 0 else [(a, d, b), (a, c, d)])
    for index in (0, len(points) - 1):
        for j in range(64):
            a, b = index * 128 + j, index * 128 + (j + 1) % 64
            faces.extend([(a, b, b + 64), (a, b + 64, a + 64)])
    mesh = trimesh.Trimesh(vertices=np.concatenate(rings), faces=faces)
    mesh.fix_normals()
    assert mesh.is_watertight and mesh.is_volume
    return mesh


def prepare(root, assets, riser, sections):
    project = root.parent / PUMP_PLACEMENT['project_folder']
    cache = root / 'source_file/pump_holder'
    cache.mkdir(parents=True, exist_ok=True)
    files = {
        'print_set': 'parts/oobb_holder_motor_pump_submersible_jt_500/3dpr.stl',
        'pump': 'source_file/pump_reference.stl',
        'parameters': 'parts/oobb_holder_motor_pump_submersible_jt_500/working.yaml',
    }
    provenance = {}
    for key, relative in files.items():
        target = cache / (key + ('.yaml' if key == 'parameters' else '.stl'))
        source = project / relative
        if source.exists():
            shutil.copyfile(source, target)
        if not target.exists():
            raise FileNotFoundError(f'Missing pump-holder source and cached copy: {source}')
        provenance[key] = {
            'source_project': PUMP_PLACEMENT['project_folder'],
            'source_file': relative,
            'cached_file': target.relative_to(root).as_posix(),
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        }
    p = yaml.safe_load((cache / 'parameters.yaml').read_text())
    # The current holder exports one plate containing base, top and nut-retaining lid.
    pieces = trimesh.load_mesh(cache / 'print_set.stl').split()
    assert len(pieces) == 3, 'Expected current offset holder with captive-nut lid'
    offsets = {
        'base': [-(p['width'] * 15 - 1)/2 - p['print_gap']/2, 0, 0],
        'top': [max((p['top_width']*15-1)/2, p['tab_outer_x'], p.get('lid_ear_outer_x', 0)) + p['print_gap']/2,
                (p['pump_body_length']+p['axial_clearance']+p['top_depth'])/2, 0],
    }
    offsets['lid'] = [offsets['top'][0], -offsets['top'][1]-p['print_gap']-22, 0]
    for mesh in pieces:
        name = 'base' if mesh.bounds[1, 0] < 0 else ('lid' if mesh.extents[2] < 4 else 'top')
        mesh.apply_translation(-np.asarray(offsets[name]))
        mesh.export(cache / f'{name}.stl')
    # Current holder datum is its base plate plus feet, not the pump fin length.
    base_top = p['depth'] + p['base_foot_height']
    base = trimesh.load_mesh(cache / 'base.stl')
    base.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    base.apply_translation([0, 0, base_top])
    top = trimesh.load_mesh(cache / 'top.stl')
    top.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    top.apply_translation([0, -(p['top_height'] * 15 - 1) / 2 + p['pump_offset_y'], base_top])
    lid = trimesh.load_mesh(cache / 'lid.stl')
    lid.apply_translation([0, p['pump_offset_y'], base_top+p['pump_body_length']+p['top_depth']])
    pump = trimesh.load_mesh(cache / 'pump.stl')
    pump_rotation = PUMP_PLACEMENT['pump_rotation_in_holder_degrees']
    pump.apply_transform(trimesh.transformations.rotation_matrix(np.radians(pump_rotation), [0, 0, 1]))
    pump.apply_translation([0, p['pump_offset_y'], base_top])
    # Two identical ribs support all four feet at a common height.
    floor = riser['gutter_wall_mm']
    cradle = next(o for o in get_options() if o['oobb_type']=='pump_support_cradle')
    seat = cradle['holder_seat_height_mm']
    shift = cradle['holder_offset_toward_edge_mm']
    assert p['foot_pitch'] == cradle['foot_pitch_mm'] and p['foot_size'] < cradle['foot_pocket_width_mm']
    origin = [PUMP_PLACEMENT['axial_position_mm'], -shift, seat]
    models = {'pump_holder_base': base, 'pump_holder_top': top, 'pump_holder_lid': lid, 'pump_reference': pump}
    for mesh in models.values():
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))
        mesh.apply_translation(origin)
    # Holder metadata describes its own chosen pump rotation; the reference
    # mesh stays canonical. Match the holder's current inward-facing outlet.
    port_rotation = trimesh.transformations.rotation_matrix(
        np.radians(pump_rotation - p.get('pump_rotation_z', 0)), [0, 0, 1])
    outlet_xy = (port_rotation @ [*p['pump_outlet_xy'], 0, 1])[:2]
    socket = np.array([origin[0] - outlet_xy[0], origin[1]-p['pump_offset_y']-outlet_xy[1],
                       seat + base_top + p['pump_body_length'] + PUMP_PLACEMENT['hose_socket_above_body_mm']])
    tip = socket.copy()
    tip[2] += p['pump_outlet_projection'] - PUMP_PLACEMENT['hose_socket_above_body_mm']
    # Match the actual top clamp's R40 quarter bend before the free side loop.
    from working_pump_top_clamp import get_layout as clamp_layout
    clamp_options = halves(next(o for o in get_options() if o['oobb_type']=='pump_hose_clamp'))
    clamp = clamp_options[0]
    mount_height = seat + base_top + p['pump_body_length'] + p['top_depth'] + p['lid_depth']
    assert np.allclose(outlet_xy, [0, clamp['outlet_offset_mm']]), 'Pump outlet must align with the bender inlet'
    assert mount_height + clamp['bend_start_above_mount_mm'] - tip[2] >= 9, 'Leave straight hose beyond the rigid outlet'
    assert tip[2]-mount_height <= clamp['rigid_outlet_above_mount_mm'], 'Rigid outlet exceeds the configured clearance height'
    assert p['pump_offset_y'] == 15
    assert {(-15, clamp['mount_row_offset_mm']), (15, clamp['mount_row_offset_mm'])} <= {(n['pos'][0], n['pos'][1]) for n in p['attachment_nuts'] if n['radius_name']=='m6'}
    half = clamp['half_thickness_mm']
    for option in clamp_options:
        mesh = trimesh.load_mesh(root / mesh_path(option))
        if option['clamp_half'] == 'a':
            transform = [[0,0,-1,origin[0]+half],[-1,0,0,origin[1]-p['pump_offset_y']],[0,1,0,mount_height],[0,0,0,1]]
        else:
            transform = [[0,0,1,origin[0]-half],[1,0,0,origin[1]-p['pump_offset_y']],[0,1,0,mount_height],[0,0,0,1]]
        mesh.apply_transform(transform)
        models['pump_top_clamp_'+option['clamp_half']] = mesh
    for side, offset in [('front', -cradle['foot_pitch_mm']/2), ('rear', cradle['foot_pitch_mm']/2)]:
        rib = trimesh.load_mesh(root / mesh_path(cradle))
        rib.apply_transform([[0,0,1,origin[0]+offset-cradle['support_thickness_mm']/2],
                             [1,0,0,0],[0,1,0,0],[0,0,0,1]])
        models['pump_cradle_'+side] = rib
    bend_points = [[origin[0], origin[1]-p['pump_offset_y']-s, mount_height+h]
                   for s,h in list(clamp_layout(**clamp)['path'].coords)[1:]]
    start = np.asarray(bend_points[-1])
    layout = get_layout(**riser)
    end = np.array([PUMP_PLACEMENT['rear_riser_position_mm'], -70, layout['entry_y']])
    controls = [start, [start[0], PUMP_PLACEMENT['hose_side_control_mm'], start[2]],
                [end[0], PUMP_PLACEMENT['hose_side_control_mm'], end[2]], end]
    p0, p1, p2, p3 = map(np.asarray, controls)
    points = [socket.tolist(), *bend_points[:-1]]
    points.extend(((1-t)**3*p0 + 3*(1-t)**2*t*p1 + 3*(1-t)*t*t*p2 + t**3*p3).tolist()
                  for t in np.linspace(0, 1, 161))
    points.extend([end[0], x, y] for x, y in list(layout['path'].coords)[1:])
    hose = sweep_hose(points, riser['tube_od_mm'] / 2, riser['tube_id_mm'] / 2)
    models['pump_hose'] = hose
    # Assets use the same width/height/length CAD axes as the tank exports.
    world_to_cad = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]])
    for name, mesh in models.items():
        exported = mesh.copy()
        exported.apply_transform(world_to_cad)
        exported.export(assets / f'{name}.stl')
    data = {
        'source_files': provenance,
        'position_world_mm': origin,
        'bounds_world_mm': {name: mesh.bounds.tolist() for name, mesh in models.items()},
        'tube_id_mm': riser['tube_id_mm'],
        'tube_od_mm': riser['tube_od_mm'],
        'tube_wall_mm': riser['tube_wall_mm'],
        'hose_centreline_world_mm': points,
        'pump_outlet_tip_world_mm': tip.tolist(),
        'hose_socket_overlap_mm': p['pump_outlet_projection'] - PUMP_PLACEMENT['hose_socket_above_body_mm'],
        'rear_riser_position_mm': end[0],
        'pump_offset_toward_edge_mm': p['pump_offset_y'] + shift,
        'holder_offset_toward_edge_mm': shift,
        'holder_foot_seat_height_mm': seat,
        'cradle_part_id': build_oomp_id(cradle),
        'cradle_count': 2,
        'pump_rotation_degrees': PUMP_PLACEMENT['pump_rotation_degrees'],
        'pump_rotation_in_holder_degrees': pump_rotation,
        'holder_base_top_mm': base_top,
        'top_clamp_mount_height_mm': mount_height,
        'top_clamp_mount_holes_world_mm': [[origin[0]+x, origin[1]-p['pump_offset_y']-clamp['mount_row_offset_mm'], mount_height] for x in (-15,15)],
        'top_clamp_bend_radius_mm': clamp['tube_bend_radius_mm'],
        'bend_straight_above_rigid_tip_mm': mount_height + clamp['bend_start_above_mount_mm'] - tip[2],
        'outlet_above_inside_floor_mm': layout['outlet_y'] - floor,
        'notes': ['Holder meshes imported without shape changes; print transforms reversed for assembly.',
                  'Pump matches the holder outlet orientation. Two locating cradle ribs keep the holder level, shifted 11 mm toward the visible edge.',
                  'Pump reference and its port positions are nominal, as supplied by the holder project.',
                  'Hose ends in the lower trough; this route does not supply the upper trough.',
                  'Half-full water is retained for illustration, not an operating submersion specification.'],
    }
    (cache / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return data
