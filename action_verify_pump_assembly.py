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
        if name.startswith('rear_riser'):
            assert 0 < volume < 25, (name, volume)
            assert intersection.bounds[1, 1] < 23.3  # Grip and taper only.
        else:
            assert volume < 0.01, (name, volume)
    for name in ('pump_holder_base', 'pump_holder_top', 'pump_reference'):
        assert models[name].is_volume
        assert models[name].bounds[0, 2] > 200 and models[name].bounds[1, 2] < 338
        for fixture in ('lower_gutter', 'upper_gutter', 'rear_cap', 'upper_rear_cap'):
            intersection = trimesh.boolean.intersection([models[name], models[fixture]], engine='manifold')
            assert not len(intersection.faces) or abs(intersection.volume) < 0.01, (name, fixture)
    for record in data['source_files'].values():
        assert hashlib.sha256((root / record['cached_file']).read_bytes()).hexdigest() == record['sha256']
    points = np.asarray(data['hose_centreline_world_mm'])
    length = np.linalg.norm(np.diff(points, axis=0), axis=1).sum()
    assert (data['tube_id_mm'], data['tube_od_mm'], data['tube_wall_mm']) == (12, 14, 1)
    assert np.allclose(points[-1], [125, 0, 17.25])
    for world in ([285, 9, 105], [125, 0, 19]):
        assert not hose.contains([[world[1], world[2], world[0]]])[0]
    assert hose.contains([[15.5, 105, 285], [6.5, 19, 125]]).all()
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
        'hose_overlap_volumes_mm3': overlaps,
        'intentional_overlap': 'Only the two riser grip/taper regions compress the nominal tube envelope.',
        'scope': 'Geometric assembly illustration; real hose bend, clamp fit and pump operation remain untested.',
    }
    (root / 'verification/pump_assembly.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PUMP_ASSEMBLY_CHECK_PASSED: hose route {length:.1f} mm; holder and hose clear the gutters and caps.')


if __name__ == '__main__':
    main()
