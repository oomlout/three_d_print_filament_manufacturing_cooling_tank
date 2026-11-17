"""Check actual generated meshes and save a small, repeatable evidence report."""
import json
import math
from pathlib import Path

import numpy as np
import trimesh
import yaml

from working_oomp_populate import build_oomp_id, get_options
from working_scad import get_gutter_sections, get_lifter_sections, get_lifter_hole_layout, get_cap_sections, get_cap_opening_layout, get_cap_seal_geometry


def facet_circle(x, y, radius):
    from shapely.geometry import Polygon
    return Polygon([(x + radius * math.cos(2 * math.pi * i / 50),
                     y + radius * math.sin(2 * math.pi * i / 50)) for i in range(50)])


def verify_cover_mesh(mesh, option):
    from shapely import affinity
    from shapely.ops import unary_union
    import oobb
    width, height = option['width_mm'], option['height_mm']
    radius = option['cover_corner_radius_mm']
    face = unary_union([facet_circle(x, y, radius)
                        for x in (-width / 2 + radius, width / 2 - radius)
                        for y in (-height / 2 + radius, height / 2 - radius)]).convex_hull
    bounds = face.bounds
    pitch = option['hole_grid_pitch_mm']
    holes = [(-pitch, -pitch), (-pitch, pitch), (pitch, -pitch), (pitch, pitch), (0, 0)]
    thickness = option['cover_thickness_mm']
    depth = option['seal_groove_depth_mm']
    for x, y in holes:
        face = face.difference(facet_circle(x, y, oobb.gv('hole_radius_m6', '3dpr')))
        assert not mesh.contains([[x, y, z] for z in (0.1, thickness / 2, thickness - 0.1)]).any()
    centre_y = option['profile_height_mm'] + option['outer_lip_mm'] - option['hole_pattern_top_offset_mm']
    seal = get_cap_seal_geometry(**option)
    groove = affinity.translate(seal['groove'], yoff=-centre_y)
    for x, y in [(seal['side_x'], 0), (-seal['side_x'], 21.5), (0, seal['bottom'] - centre_y)]:
        assert not mesh.contains([[x, y, thickness - 0.1], [x, y, thickness - depth + 0.01]]).any()
        assert mesh.contains([[x, y, thickness - depth - 0.01]])[0]
    assert mesh.contains([[21, 0, 0.1], [21, 0, thickness - 0.1]]).all()
    return {
        'expected_volume': face.area * thickness - face.intersection(groove).area * depth,
        'expected_extents': [bounds[2] - bounds[0], bounds[3] - bounds[1], thickness],
        'expected_minimum': [bounds[0], bounds[1], 0],
    }


def verify_cap_mesh(mesh, option):
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    import oobb

    sections = get_cap_sections(**option)
    plate = option['front_plate_mm']
    face = sections['face']
    ledge = sections['ledge']
    if option['oobb_type'] == 'cap_end_open':
        layout = get_cap_opening_layout(**option)

        def circle(x, y, radius):
            return Polygon([(x + radius * math.cos(2 * math.pi * i / 50),
                             y + radius * math.sin(2 * math.pi * i / 50)) for i in range(50)])

        radius = layout['radius']
        half_width = layout['width'] / 2
        rounded = unary_union([
            circle(x, y, radius)
            for x in (-half_width + radius, half_width - radius)
            for y in (layout['bottom'] + radius, layout['top'] - radius)
        ]).convex_hull
        mouth = box(-half_width, layout['top'] - radius, half_width, layout['top'] + 0.01)
        bores = [circle(h['x'], h['y'], oobb.gv('hole_radius_' + option['hole_size'], '3dpr'))
                 for h in layout['holes']]
        cuts = unary_union([rounded, mouth, *bores])
        face = face.difference(cuts)
        ledge = ledge.difference(cuts)
        for hole in layout['holes']:
            assert not mesh.contains([[hole['x'], hole['y'], z] for z in (0.1, plate / 2, plate - 0.1)]).any()
            assert mesh.contains([[hole['x'] + 3.5, hole['y'], plate / 2]])[0]
        # Open right through the face, with square mouth and rounded bottom.
        assert not mesh.contains([[x, y, z] for x, y in
                                 [(0, 26.6), (0, 42.5), (6.9, 64.4), (-6.9, 64.4)]
                                 for z in (0.1, plate / 2, plate - 0.1)]).any()
        assert mesh.contains([[6.9, 26.6, plate / 2], [-6.9, 26.6, plate / 2], [0, 26.4, plate / 2]]).all()
        # A 44 mm cover centred at Y=42.5 now overlaps the slot floor by 6 mm.
        assert mesh.contains([[x, y, plate / 2] for x in (-7, 0, 7)
                              for y in (20.6, 23.5, 26.4)]).all()

    groove_volume = 0
    if 'seal_groove_depth_mm' in option:
        seal = get_cap_seal_geometry(**option)
        depth = option['seal_groove_depth_mm']
        groove_volume = face.intersection(seal['groove']).area * depth
        for x, y in [(seal['side_x'], 42.5), (-seal['side_x'], 64.4), (0, seal['bottom'])]:
            assert not mesh.contains([[x, y, plate - 0.1], [x, y, plate - depth + 0.01]]).any()
            assert mesh.contains([[x, y, 0.1], [x, y, plate - depth - 0.01]]).all()
    x_min, y_min, x_max, y_max = sections['face'].bounds
    return {
        'expected_volume': face.area * plate + ledge.area * option['insertion_depth_mm'] - groove_volume,
        'expected_extents': [x_max - x_min, y_max - y_min, option['total_depth_mm']],
        'expected_minimum': [x_min, y_min, 0],
    }


def verify_lifter_mesh(mesh, option):
    """Independently check actual bores, recesses, shoes and half-turn assembly."""
    from shapely.geometry import Polygon
    import oobb

    sections = get_lifter_sections(**option)
    layout = get_lifter_hole_layout(**option)
    half_web = option['thickness_mm'] / 2
    half_support = option['support_thickness_mm'] / 2
    expected_volume = sections['web'].area * half_web
    expected_volume += (sections['lower_shoe'].area + sections['upper_shoe'].area) * (half_support - half_web)

    # SCAD uses 50 facets for circular cutters. Integrate their intersections
    # through the web and shoes instead of treating every bore as infinitely long.
    facet_count = 50
    circular_area_factor = facet_count / 2 * math.sin(2 * math.pi / facet_count)
    for hole in layout['flow_holes']:
        points = []
        for i in range(facet_count):
            angle = 2 * math.pi * i / facet_count
            points.append((hole['x'] + hole['radius'] * math.cos(angle),
                           hole['y'] + hole['radius'] * math.sin(angle)))
        bore = Polygon(points)
        expected_volume -= sections['web'].intersection(bore).area * half_web
        expected_volume -= sections['lower_shoe'].intersection(bore).area * (half_support - half_web)
        assert not mesh.contains([[hole['x'], hole['y'], z]
                                  for z in (0.25, half_web, half_support - 0.25)]).any()

    shaft_radius = oobb.gv('hole_radius_m3', '3dpr')
    head_radius = oobb.gv('screw_countersunk_radius_m3', '3dpr')
    head_depth = oobb.gv('screw_countersunk_depth_m3', '3dpr')
    nut_radius = oobb.gv('nut_radius_m3', '3dpr')
    nut_depth = oobb.gv('nut_depth_m3', '3dpr')
    shaft_area = circular_area_factor * shaft_radius ** 2
    head_volume = circular_area_factor * head_depth / 3 * (shaft_radius**2 + shaft_radius*head_radius + head_radius**2)
    nut_area = 3 * math.sqrt(3) / 2 * nut_radius ** 2
    for fastener in layout['fasteners']:
        expected_volume -= shaft_area * half_web
        if fastener['role'] == 'countersink':
            expected_volume -= head_volume - shaft_area * head_depth
        else:
            expected_volume -= (nut_area - shaft_area) * nut_depth
        x, y = fastener['x'], fastener['y']
        assert not mesh.contains([[x, y, 0.25], [x, y, half_web - 0.25]]).any()
        assert mesh.contains([[x + 2.4, y, 0.25]])[0]
        assert not mesh.contains([[x + 2.4, y, half_web - 0.25]])[0]

    # Probe physical material, not just metadata, to establish web/shoe depths.
    assert mesh.contains([[0, 40, half_web - 0.1]])[0]
    assert not mesh.contains([[0, 40, half_web + 0.1]])[0]
    assert mesh.contains([[0, 3.25, half_support - 0.1]])[0]
    assert mesh.contains([[0, option['lift_height_mm'] - 3, half_support - 0.1]])[0]
    assert not mesh.contains([[0, 3.25, half_support + 0.1]])[0]

    second = mesh.copy()
    second.apply_transform(np.diag([-1, 1, -1, 1]))
    combined = trimesh.util.concatenate([mesh, second])
    assert np.isclose(combined.extents[2], option['support_thickness_mm'])
    assert np.isclose(second.bounds[1, 2], 0)
    assert np.isclose(mesh.bounds[0, 2], 0)
    for fastener in layout['fasteners']:
        assert not second.contains([[fastener['x'], fastener['y'], -0.25]])[0]
    for hole in layout['flow_holes']:
        assert not second.contains([[hole['x'], hole['y'], -0.25],
                                    [hole['x'], hole['y'], -half_web + 0.1]]).any()

    x_min, y_min, x_max, y_max = sections['web'].bounds
    return {
        'expected_volume': expected_volume,
        'expected_extents': [x_max - x_min, y_max - y_min, half_support],
        'expected_minimum': [x_min, y_min, 0],
    }


def verify_pump_lifter_mesh(mesh, option):
    from working_pump_lifter import get_layout
    layout = get_layout(**option)
    depth = layout['half_depth']
    sign = layout['side_sign']
    # Probe the exported channel around the whole bend, including backing.
    for x, y in list(layout['path'].coords)[1:]:
        assert not mesh.contains([[x, y, depth - 0.1]])[0], (x, y, 'channel')
        if y > layout['outlet_y'] + 6:
            assert mesh.contains([[x, y, depth - 7.3]])[0], (x, y, 'backing')
    # Separate the 13.6 mm grip from the 14.4 mm guide in the real STL.
    y = layout['outlet_y'] + 2
    assert mesh.contains([[0, y, depth - 6.9]])[0]
    assert not mesh.contains([[0, y, depth - 6.7]])[0]
    y = layout['bend_centre_y'] - 0.5
    assert mesh.contains([[0, y, depth - 7.3]])[0]
    assert not mesh.contains([[0, y, depth - 7.1]])[0]
    assert not mesh.contains([[0, 10, z] for z in (0.1, 7, depth - 0.1)]).any()
    assert mesh.contains([[x, 5, depth - 0.1] for x in (-30, 30)]).all()
    for hole in layout['flow_holes'] + layout['fasteners']:
        assert not mesh.contains([[hole['x'], hole['y'], z] for z in (0.1, depth / 2, depth - 0.1)]).any()
    for hole in layout['fasteners']:
        x, y = hole['x'], hole['y']
        assert not mesh.contains([[x + sign * 2.4, y, 0.1]])[0]
        assert mesh.contains([[x + sign * 2.4, y, 4]])[0]
    bounds = layout['outline'].bounds
    return {
        'expected_volume': None,  # Curved channel verified with section probes.
        'expected_extents': [bounds[2] - bounds[0], bounds[3] - bounds[1], depth],
        'expected_minimum': [bounds[0], bounds[1], 0],
    }


def main():
    results = []
    for option in get_options():
        part_id = build_oomp_id(option)
        folder = Path('parts') / part_id
        mesh = trimesh.load_mesh(folder / '3dpr.stl')
        sections = get_gutter_sections(**option)
        expected_minimum = [-57, 0, 0]
        if option['oobb_type'] == 'lifter_pump_inlet':
            evidence = verify_pump_lifter_mesh(mesh, option)
            expected_volume = evidence['expected_volume']
            expected_extents = evidence['expected_extents']
            expected_minimum = evidence['expected_minimum']
        elif option['oobb_type'] == 'lifter':
            evidence = verify_lifter_mesh(mesh, option)
            expected_volume = evidence['expected_volume']
            expected_extents = evidence['expected_extents']
            expected_minimum = evidence['expected_minimum']
        elif option['oobb_type'] == 'cap_cover':
            evidence = verify_cover_mesh(mesh, option)
            expected_volume = evidence['expected_volume']
            expected_extents = evidence['expected_extents']
            expected_minimum = evidence['expected_minimum']
        elif option['oobb_type'].startswith('cap_end_'):
            evidence = verify_cap_mesh(mesh, option)
            expected_volume = evidence['expected_volume']
            expected_extents = evidence['expected_extents']
            expected_minimum = evidence['expected_minimum']
        else:
            depth = option['length_mm']
            expected_volume = sections['gutter'].area * depth
        if option['oobb_type'] == 'gutter_square':
            expected_extents = [option['profile_width_mm'], option['profile_height_mm'], depth]
        assert mesh.is_watertight, part_id
        assert mesh.is_winding_consistent, part_id
        assert len(mesh.split()) == 1, part_id
        assert mesh.volume > 0, part_id
        assert np.allclose(mesh.bounds[0], expected_minimum, atol=1e-5), part_id
        assert np.allclose(mesh.extents, expected_extents, atol=1e-5), part_id
        if expected_volume is not None:
            assert abs(mesh.volume - expected_volume) / expected_volume < 1e-5, part_id
        for parent in ('parts_source', 'parts'):
            metadata = yaml.safe_load((Path(parent) / part_id / 'working.yaml').read_text(encoding='utf-8'))
            for key in ('gutter_wall_mm', 'profile_width_mm', 'profile_height_mm', 'oobb_type'):
                assert metadata[key] == option[key], (part_id, key)
        results.append({'id': part_id, 'extents_mm': mesh.extents.tolist(),
                        'volume_mm3': float(mesh.volume), 'expected_volume_mm3': expected_volume,
                        'closed_mesh': True, 'consistent_winding': True, 'connected_bodies': 1})
    pump = [o for o in get_options() if o['oobb_type'] == 'lifter_pump_inlet']
    from working_pump_lifter import get_layout
    a, b = [trimesh.load_mesh(Path('parts') / build_oomp_id(o) / '3dpr.stl') for o in pump]
    b.apply_transform(np.diag([-1, 1, -1, 1]))
    b.apply_translation([0, 0, pump[0]['thickness_mm']])
    seam = pump[0]['thickness_mm'] / 2
    assert np.isclose(a.bounds[1, 2], seam) and np.isclose(b.bounds[0, 2], seam)
    for x, y in list(get_layout(**pump[0])['path'].coords)[1:]:
        assert not a.contains([[x, y, seam - 0.1]])[0]
        assert not b.contains([[x, y, seam + 0.1]])[0]
    for hole in get_layout(**pump[0])['fasteners']:
        assert not b.contains([[hole['x'], hole['y'], seam + 0.1],
                               [hole['x'], hole['y'], 2 * seam - 0.1]]).any()
    for o in pump:
        source = (Path('parts') / build_oomp_id(o) / '3dpr.scad').read_text(encoding='utf-8')
        assert 'use <../scad_reference/' not in source
        assert f"module pump_tube_channel_half_{o['pump_half']}()" in source
    cap = next(o for o in get_options() if o['oobb_type'] == 'cap_end_open' and o['total_depth_mm'] == 15)
    cover = next(o for o in get_options() if o['oobb_type'] == 'cap_cover')
    cover_mesh = trimesh.load_mesh(Path('parts') / build_oomp_id(cover) / '3dpr.stl')
    centre_y = cap['profile_height_mm'] + cap['outer_lip_mm'] - cap['hole_pattern_top_offset_mm']
    cover_mesh.apply_transform(np.diag([-1, 1, -1, 1]))
    mating_z = cap['front_plate_mm']
    cover_mesh.apply_translation([0, centre_y, mating_z + cover['cover_thickness_mm']])
    cap_mesh = trimesh.load_mesh(Path('parts') / build_oomp_id(cap) / '3dpr.stl')
    seal = get_cap_seal_geometry(**cap)
    for x, y in [(seal['side_x'], 42.5), (-seal['side_x'], 64.4), (0, seal['bottom'])]:
        assert not cap_mesh.contains([[x, y, mating_z - 0.1]])[0]
        assert not cover_mesh.contains([[x, y, mating_z + 0.1]])[0]
        depth = cap['seal_groove_depth_mm']
        assert cap_mesh.contains([[x, y, mating_z - depth - 0.01], [x, y, 0.1]]).all()
        assert cover_mesh.contains([[x, y, mating_z + depth + 0.01]])[0]
    assert np.isclose(cover_mesh.bounds[0, 2], mating_z)
    from shapely.geometry import box
    cover_envelope = box(-cover['width_mm'] / 2, centre_y - cover['height_mm'] / 2,
                         cover['width_mm'] / 2, centre_y + cover['height_mm'] / 2)
    assert get_cap_sections(**cap)['ledge'].intersection(cover_envelope).area == 0
    seal_report = {
        'matching_faces_checked_in_assembly': True,
        'cap_groove_face': 'inside',
        'mating_plane_z_mm': mating_z,
        'cord_diameter_mm': cap['seal_cord_diameter_mm'],
        'groove_width_mm': cap['seal_groove_width_mm'],
        'groove_depth_per_face_mm': cap['seal_groove_depth_mm'],
        'nominal_compression_percent': 100 * (1 - 2 * cap['seal_groove_depth_mm'] / cap['seal_cord_diameter_mm']),
        'nominal_gland_fill_percent': 100 * math.pi * (cap['seal_cord_diameter_mm'] / 2)**2 / (2 * cap['seal_groove_depth_mm'] * cap['seal_groove_width_mm']),
        'cord_length_to_top_mm': seal['cord_length_to_rim_mm'],
    }
    report = {'status': 'passed', 'part_count': len(results), 'parts': results, 'seal': seal_report,
              'pump_inlet': {'assembled_channel_and_joints_aligned': True,
                             'tube_guide_and_grip_probed': True,
                             'scad_modules_self_contained': True,
                             'outlet_above_inside_floor_mm': pump[0]['tube_outlet_above_floor_mm'],
                             'physical_tube_fit_tested': False},
              'scope': 'Digital geometry only; actual gutter fit, lifter load capacity and water sealing are untested.'}
    destination = Path('verification/cooling_tank_meshes.json')
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"Verified {len(results)} meshes: dimensions, volume, closure, winding, connectivity and part metadata.")


if __name__ == '__main__':
    main()
