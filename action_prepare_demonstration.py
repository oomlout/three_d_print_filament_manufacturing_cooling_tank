"""Export current CAD and dimensioned water volumes for the Blender demo."""
import json
from pathlib import Path
import shutil

import trimesh
from shapely.geometry import box
from working_oomp_populate import get_options, build_oomp_id
from working_scad import get_gutter_sections


def main():
    root = Path(__file__).resolve().parent
    destination = root / 'demonstration'
    assets = destination / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    options = get_options()
    selected = {
        'solid_cap': next(o for o in options if o['oobb_type'] == 'cap_end_solide' and o['total_depth_mm'] == 15),
        'open_cap': next(o for o in options if o['oobb_type'] == 'cap_end_open' and o['total_depth_mm'] == 15),
        'cover': next(o for o in options if o['oobb_type'] == 'cap_cover'),
        'lifter_half': next(o for o in options if o['oobb_type'] == 'lifter'),
        'pump_lifter_a': next(o for o in options if o['oobb_type'] == 'lifter_pump_inlet' and o['pump_half'] == 'a'),
        'pump_lifter_b': next(o for o in options if o['oobb_type'] == 'lifter_pump_inlet' and o['pump_half'] == 'b'),
        'lower_gutter': next(o for o in options if o['oobb_type'] == 'gutter_square' and o['length_mm'] == 500),
    }
    sources = {}
    for name, option in selected.items():
        source = root / 'parts' / build_oomp_id(option) / '3dpr.stl'
        shutil.copyfile(source, assets / f'{name}.stl')
        sources[name] = source.relative_to(root).as_posix()
    profile = selected['lower_gutter']
    sections = get_gutter_sections(**profile)
    from working_demonstration_pump import prepare
    pump_data = prepare(root, assets, selected['pump_lifter_a'], sections)
    # Cut lengths for this assembly; profile is taken from the catalogue reference.
    trimesh.creation.extrude_polygon(sections['gutter'], 600).export(assets / 'lower_gutter.stl')
    trimesh.creation.extrude_polygon(sections['gutter'], 400).export(assets / 'upper_gutter.stl')
    lower_level = profile['gutter_wall_mm'] + (profile['profile_height_mm'] - profile['gutter_wall_mm']) / 2
    upper_level = profile['profile_height_mm'] - 5
    def placed(asset, y=0, z=0, flip=False):
        mesh = trimesh.load_mesh(assets / f'{asset}.stl')
        if flip:
            mesh.apply_transform([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        mesh.apply_translation([0, y, z])
        return mesh

    for name, length, level in [('lower_water', 600, lower_level), ('upper_water', 400, upper_level)]:
        section = sections['cavity'].intersection(box(-100, 0, 100, level))
        is_upper = name == 'upper_water'
        volume = trimesh.creation.extrude_polygon(section, length + (6 if is_upper else 0))
        if is_upper:
            volume.apply_translation([0, 0, -3])
        cutters = []
        shift = 200 if is_upper else 250
        height_shift = -75 if is_upper else 0
        for flip in (False, True):
            cutters.append(placed('lifter_half', y=height_shift, z=-125 + shift, flip=flip))
        cutters.extend([placed('pump_lifter_a', y=height_shift, z=110 + shift),
                        placed('pump_lifter_b', y=height_shift, z=140 + shift, flip=True)])
        for asset in ('pump_holder_base', 'pump_holder_top', 'pump_reference', 'pump_hose'):
            cutters.append(placed(asset, y=height_shift, z=shift))
        cap_asset = 'open_cap' if is_upper else 'solid_cap'
        cutters.extend([placed(cap_asset, z=-3), placed(cap_asset, z=length + 3, flip=True)])
        if is_upper:
            cutters.extend([placed('cover', y=42.5, z=3, flip=True),
                            placed('cover', y=42.5, z=length - 3)])
        volume = trimesh.boolean.difference([volume, *cutters], engine='manifold')
        assert volume.is_watertight and volume.volume > 0
        volume.export(assets / f'{name}.stl')
    data = {
        'units': 'millimetres',
        'lower_length': 600,
        'lower_start': -250,
        'lower_end': 350,
        'rear_extension': 100,
        'upper_length': 400,
        'lift': 75,
        'lower_water_level': lower_level,
        'upper_water_level': upper_level + 75,
        'filament_diameter': 1.75,
        'filament_colour': 'black',
        'filament_start': -350,
        'filament_end': 450,
        'filament_axis_height': 75 + 42.5,
        'support_positions': [-125, 125],
        'pump': pump_data,
        'cover_inside_mating_plane': 3,
        'sources': sources,
        'notes': [
            'Actual current printable CAD meshes, no geometry approximations for printed parts.',
            'Front support uses identical halves; rear support uses pump-inlet halves A and B.',
            'Both upper ends have slotted caps and inside covers for a continuous filament path.',
            'Lower front remains at -250 mm; rear extends to +350 mm with the JT-500 holder in its rear bay.',
            'Lower trough is half the internal depth; upper surface is 5 mm below the rim.',
            'Water streams and ripples are illustrative, not a fluid simulation.',
            'Pump hose feeds the lower trough through the rear riser; an upper-trough feed is not shown.',
        ],
    }
    (destination / 'scene_data.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(destination / 'scene_data.json')


if __name__ == '__main__':
    main()
