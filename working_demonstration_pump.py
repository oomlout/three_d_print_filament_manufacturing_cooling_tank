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


PUMP_PLACEMENT = {
    'project_folder': 'oomlout_oobb_holder_motor_pump_submersible_jt_500',
    'axial_position_mm': 285.0,
    'rear_riser_position_mm': 125.0,
    'hose_socket_above_body_mm': 8.0,
    'hose_control_rise_mm': 120.0,
    'hose_side_control_mm': -190.0,
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
        'base': 'parts/oobb_holder_motor_pump_submersible_jt_500_base/3dpr.stl',
        'top': 'parts/oobb_holder_motor_pump_submersible_jt_500_top/3dpr.stl',
        'pump': 'source_file/pump_reference.stl',
        'parameters': 'parts/oobb_holder_motor_pump_submersible_jt_500_top/working.yaml',
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
    base = trimesh.load_mesh(cache / 'base.stl')
    base.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    base.apply_translation([0, 0, p['pump_fin_projection']])
    top = trimesh.load_mesh(cache / 'top.stl')
    top.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    top.apply_translation([0, -(p['top_height'] * 15 - 1) / 2, p['pump_fin_projection']])
    pump = trimesh.load_mesh(cache / 'pump.stl')
    pump.apply_translation([0, 0, p['pump_fin_projection']])
    # The wide feet settle slightly above the centre floor on its corner curves.
    floor = riser['gutter_wall_mm']
    seat = None
    for height in np.arange(floor, floor + 6, 0.05):
        if all(sections['cavity'].buffer(1e-5).covers(Point(v[1], v[2] + height)) for v in base.vertices):
            seat = float(height)
            break
    if seat is None:
        raise ValueError('Pump holder feet do not fit the lower gutter')
    origin = [PUMP_PLACEMENT['axial_position_mm'], 0, seat]
    models = {'pump_holder_base': base, 'pump_holder_top': top, 'pump_reference': pump}
    for mesh in models.values():
        mesh.apply_translation(origin)
    outlet_xy = p['pump_outlet_xy']
    socket = np.array([origin[0] + outlet_xy[0], outlet_xy[1],
                       seat + p['pump_fin_projection'] + p['pump_body_length'] + PUMP_PLACEMENT['hose_socket_above_body_mm']])
    tip = socket.copy()
    tip[2] += p['pump_outlet_projection'] - PUMP_PLACEMENT['hose_socket_above_body_mm']
    # Start with a straight socket overlap, then a broad cubic route outside the rims.
    start = tip + [0, 0, 5]
    layout = get_layout(**riser)
    end = np.array([PUMP_PLACEMENT['rear_riser_position_mm'], -70, layout['entry_y']])
    controls = [start, start + [0, 0, PUMP_PLACEMENT['hose_control_rise_mm']],
                [end[0], PUMP_PLACEMENT['hose_side_control_mm'], end[2]], end]
    p0, p1, p2, p3 = map(np.asarray, controls)
    points = [socket.tolist()]
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
        'outlet_above_inside_floor_mm': layout['outlet_y'] - floor,
        'notes': ['Holder meshes imported without shape changes; print transforms reversed for assembly.',
                  'Pump reference and its port positions are nominal, as supplied by the holder project.',
                  'Hose ends in the lower trough; this route does not supply the upper trough.',
                  'Half-full water is retained for illustration, not an operating submersion specification.'],
    }
    (cache / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    return data
