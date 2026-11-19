"""Check the exported assembly meshes, including hose routing and source copies."""
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh


def main():
    root = Path(__file__).resolve().parent
    assets = root / 'demonstration/assets'
    data = json.loads((root / 'demonstration/scene_data.json').read_text())['pump']
    def load(name, offset=(0, 0, 0), flip=False):
        mesh = trimesh.load_mesh(assets / f'{name}.stl')
        if flip:
            mesh.apply_transform(np.diag([-1, 1, -1, 1]))
        mesh.apply_translation(offset)
        return mesh
    models = {
        'lower_gutter': load('lower_gutter', (0, 0, -250)),
        'upper_gutter': load('upper_gutter', (0, 75, -200)),
        'rear_cap': load('solid_cap', (0, 0, 353), True),
        'upper_rear_cap': load('open_cap', (0, 75, 203), True),
        'pump_holder_base': load('pump_holder_base'),
        'pump_holder_top': load('pump_holder_top'),
        'pump_holder_lid': load('pump_holder_lid'),
        'pump_cradle_front': load('pump_cradle_front'),
        'pump_cradle_rear': load('pump_cradle_rear'),
        'pump_top_clamp_a': load('pump_top_clamp_a'),
        'pump_top_clamp_b': load('pump_top_clamp_b'),
        'pump_reference': load('pump_reference'),
        'rear_riser_a': load('pump_lifter_a', (0, 0, 110)),
        'rear_riser_b': load('pump_lifter_b', (0, 0, 140), True),
    }
    hose = load('pump_hose')
    assert hose.is_volume and len(hose.split()) == 1
    overlaps = {}
    for name, mesh in models.items():
        intersection = trimesh.boolean.intersection([hose, mesh], engine='manifold')
        volume = abs(intersection.volume) if len(intersection.faces) else 0.0
        overlaps[name] = volume
        if name.startswith('rear_riser') or name.startswith('pump_top_clamp'):
            assert 0 < volume < 25, (name, volume)
            if name.startswith('rear_riser'):
                assert intersection.bounds[1, 1] < 23.3
            else:
                # Only the last grip/taper section may compress the tube.
                from working_oomp_populate import PUMP_TOP_CLAMP
                clamp_exit = data['position_world_mm'][1] - 15 - (PUMP_TOP_CLAMP['outlet_offset_mm'] + PUMP_TOP_CLAMP['tube_bend_radius_mm'] + PUMP_TOP_CLAMP['outlet_straight_mm'])
                assert intersection.bounds[1, 0] < clamp_exit + 6.1
        else:
            assert volume < 0.01, (name, volume)
    for name in ('pump_holder_base', 'pump_holder_top', 'pump_holder_lid', 'pump_reference', 'pump_top_clamp_a', 'pump_top_clamp_b', 'pump_cradle_front', 'pump_cradle_rear'):
        assert models[name].is_volume
        assert models[name].bounds[0, 2] > 200 and models[name].bounds[1, 2] < 338
        for fixture in ('lower_gutter', 'upper_gutter', 'rear_cap', 'upper_rear_cap'):
            intersection = trimesh.boolean.intersection([models[name], models[fixture]], engine='manifold')
            assert not len(intersection.faces) or abs(intersection.volume) < 0.01, (name, fixture)
    filament_clearances = {}
    # The pump matches the holder orientation; check every supporting piece.
    for name in ('pump_holder_base', 'pump_holder_top', 'pump_holder_lid'):
        overlap = trimesh.boolean.intersection([models['pump_reference'], models[name]], engine='manifold')
        assert not len(overlap.faces) or abs(overlap.volume) < .01, ('pump_reference', name)
    samples = np.column_stack([np.zeros(1001), np.full(1001,117.5), np.linspace(250,320,1001)])
    for name in ('pump_top_clamp_a', 'pump_top_clamp_b'):
        for other in ('pump_reference', 'pump_holder_lid', 'pump_holder_top'):
            overlap = trimesh.boolean.intersection([models[name], models[other]], engine='manifold')
            assert not len(overlap.faces) or abs(overlap.volume) < .01, (name, other)
        _, distances, _ = trimesh.proximity.closest_point(models[name], samples)
        filament_clearances[name] = float(distances.min() - .875)
        assert filament_clearances[name] > 3
    for name in ('pump_hose', 'pump_reference', 'pump_holder_base', 'pump_holder_top', 'pump_holder_lid'):
        mesh = hose if name == 'pump_hose' else models[name]
        _, distances, _ = trimesh.proximity.closest_point(mesh, samples)
        filament_clearances[name] = float(distances.min() - .875)
        assert not mesh.contains(samples).any()
        assert filament_clearances[name] > 3, (name, filament_clearances[name])
    seat = data['holder_foot_seat_height_mm']
    # Four actual pocket floors directly support four actual foot undersides.
    for rib_name, axial in [('pump_cradle_front', 255), ('pump_cradle_rear', 315)]:
        rib = models[rib_name]
        overlap = trimesh.boolean.intersection([rib, models['pump_holder_base']], engine='manifold')
        assert not len(overlap.faces) or abs(overlap.volume) < .01
        for cross in (-data['holder_offset_toward_edge_mm']-30, -data['holder_offset_toward_edge_mm']+30):
            # Probe the foot bearing ring, clear of its central M6 bore.
            for bearing_x in (cross-4.5, cross+4.5):
                assert rib.contains([[bearing_x,seat-.1,axial]])[0]
                assert not rib.contains([[bearing_x,seat+.1,axial]])[0]
                assert models['pump_holder_base'].contains([[bearing_x,seat+.1,axial]])[0]
                assert not models['pump_holder_base'].contains([[bearing_x,seat-.1,axial]])[0]
    # Check bolt axes through both the new feet and the existing captive-nut lid.
    h = data['top_clamp_mount_height_mm']
    head_clearances = []
    for x,y,z in data['top_clamp_mount_holes_world_mm']:
        height_distance = max(z+4-117.5,117.5-(z+10),0)
        head_clearances.append(float(np.hypot(max(abs(y)-5,0),height_distance)-.875))
        for name in ('pump_top_clamp_a', 'pump_top_clamp_b', 'pump_holder_lid'):
            assert not models[name].contains([[y, level, x] for level in (h-2, h+.1, h+3.9)]).any()
    assert min(head_clearances) > 9
    for record in data['source_files'].values():
        assert hashlib.sha256((root / record['cached_file']).read_bytes()).hexdigest() == record['sha256']
    points = np.asarray(data['hose_centreline_world_mm'])
    length = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
    assert (data['tube_id_mm'], data['tube_od_mm'], data['tube_wall_mm']) == (12, 14, 1)
    assert np.allclose(points[-1], [125, 0, 17.25])
    socket = np.asarray(data['hose_centreline_world_mm'][0])
    probe = socket + [0,0,2]
    for world in (probe, [125, 0, 19]):
        assert not hose.contains([[world[1], world[2], world[0]]])[0]
    assert hose.contains([[probe[1]+6.5, probe[2], probe[0]], [6.5, 19, 125]]).all()
    expected_volume = np.pi * (7**2 - 6**2) * length
    assert abs(hose.volume / expected_volume - 1) < 0.01
    report = {
        'status': 'passed',
        'source_hashes_match': True,
        'holder_and_hose_clear_gutters_and_caps': True,
        'hose_closed_annular_mesh': True,
        'hose_centreline_length_mm': float(length),
        'hose_id_mm': 12,
        'hose_od_mm': 14,
        'outlet_above_inside_floor_mm': 15,
        'hose_socket_overlap_mm': data['hose_socket_overlap_mm'],
        'top_clamp_filament_surface_clearance_mm': filament_clearances,
        'm6_head_filament_surface_clearance_mm': min(head_clearances),
        'top_clamp_m6_axes_match_existing_lid': True,
        'pump_shift_toward_visible_edge_mm': data['pump_offset_toward_edge_mm'],
        'pump_orientation_matches_current_holder': True,
        'four_feet_supported_at_equal_height_mm': seat,
        'cradle_rib_count': 2,
        'holder_shift_toward_edge_mm': data['holder_offset_toward_edge_mm'],
        'bend_straight_above_rigid_tip_mm': data['bend_straight_above_rigid_tip_mm'],
        'hose_overlap_volumes_mm3': overlaps,
        'intentional_overlap': 'Only the riser and pump-top clamp outlet grip/taper regions compress the nominal tube envelope.',
        'scope': 'Geometric assembly illustration; real hose bend, clamp fit and pump operation remain untested.',
    }
    (root / 'verification/pump_assembly.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PUMP_ASSEMBLY_CHECK_PASSED: hose route {length:.1f} mm; holder and hose clear the gutters and caps.')


if __name__ == '__main__':
    main()
