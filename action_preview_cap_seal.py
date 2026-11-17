"""Render the two mating seal faces and save an editable assembled SCAD."""
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from shapely import affinity

from working_oomp_populate import get_options, build_oomp_id
from working_scad import get_cap_seal_geometry


def main():
    options = get_options()
    cap = next(o for o in options if o['oobb_type'] == 'cap_end_open' and o['total_depth_mm'] == 15)
    cover = next(o for o in options if o['oobb_type'] == 'cap_cover')
    destination = Path('preview')
    destination.mkdir(exist_ok=True)
    cap_path = f"../parts/{build_oomp_id(cap)}/3dpr.scad"
    cover_path = f"../parts/{build_oomp_id(cover)}/3dpr.scad"
    centre_y = cap['profile_height_mm'] + cap['outer_lip_mm'] - cap['hole_pattern_top_offset_mm']
    assembly = (
        '// Cover is inside the cap; mating faces meet at Z=3 around one 2 mm cord.\n'
        f'color([0.20,0.53,0.59]) {{ include <{cap_path}>; }}\n'
        f'translate([0,{centre_y},{cap["front_plate_mm"] + cover["cover_thickness_mm"]}]) rotate([0,180,0]) '
        f'color([0.82,0.66,0.35]) {{ include <{cover_path}>; }}\n'
    )
    (destination / 'cap_seal_assembly.scad').write_text(assembly, encoding='utf-8')
    figure = plt.figure(figsize=(12, 10), layout='constrained', facecolor='#faf9f5')
    figure.suptitle('Cooling tank / cover and matching U seal', fontsize=22, color='#253944', fontweight='bold')
    render_jobs = [
        ('cap_seal_face', f'include <{cap_path}>;',
         'Open cap / inside sealing face'),
        ('cap_cover_face', f'include <{cover_path}>;',
         '3 x 3 cover / groove faces the cap'),
    ]
    for index, (name, geometry, title) in enumerate(render_jobs):
        source = destination / f'{name}.scad'
        png = source.with_suffix('.png')
        source.write_text('color([0.20,0.53,0.59]) {\n' + geometry + '\n}\n', encoding='utf-8')
        result = subprocess.run(['openscad', '--render', '--autocenter', '--viewall',
                                 '--projection=o', '--camera=0,0,0,25,0,15,500',
                                 '--colorscheme=Tomorrow', '--imgsize=1100,750',
                                 '-o', str(png), str(source)], capture_output=True, text=True, check=True)
        if 'WARNING:' in result.stderr or 'ERROR:' in result.stderr:
            raise RuntimeError(result.stderr)
        ax = figure.add_subplot(2, 2, index + 1)
        ax.imshow(plt.imread(png))
        ax.set_axis_off()
        ax.set_title(title, fontsize=15, color='#253944')

    ax = figure.add_subplot(2, 2, 3, facecolor='#faf9f5')
    seal = get_cap_seal_geometry(**cover)
    groove = affinity.translate(seal['groove'], yoff=-centre_y)
    # Top view of cover: all holes explicit, no unwanted side-midpoint holes.
    from shapely.geometry import box
    outline = box(-17, -17, 17, 17).buffer(5, quad_segs=90)
    ax.add_patch(Polygon(outline.exterior.coords, facecolor='#c7dce0', edgecolor='#253944'))
    clipped = groove.intersection(outline)
    ax.add_patch(Polygon(clipped.exterior.coords, facecolor='#ce8a39', edgecolor='none'))
    for x, y in [(-15, -15), (-15, 15), (15, -15), (15, 15), (0, 0)]:
        ax.add_patch(Circle((x, y), 3.25, facecolor='#faf9f5', edgecolor='#253944'))
    ax.annotate('Both cord ends\nexit the top', xy=(9.375, 21.5), xytext=(0, 30), ha='center',
                arrowprops={'arrowstyle': '->', 'color': '#253944'}, fontsize=11)
    ax.set(xlim=(-26, 26), ylim=(-26, 38), aspect='equal')
    ax.set_axis_off()
    ax.set_title('Matching groove / five M6 holes', fontsize=15, color='#253944')

    ax = figure.add_subplot(2, 2, 4)
    ax.set_axis_off()
    ax.text(0.02, 0.92, 'One 2 mm rubber cord / inside cover', fontsize=16, fontweight='bold', color='#253944')
    ax.text(0.02, 0.81,
            'Groove: 2.4 mm wide x 0.8 mm deep per face\n'
            'Faces together: 1.6 mm combined groove height\n'
            'Nominal compression: 20%\n'
            'Cord path to top: 93.2 mm; trim ends to suit\n\n'
            'Cover: 44 x 44 x 3 mm, R5 outline corners\n'
            'Straight sides; no edge fillet or chamfer\n'
            'Four corner M6 holes plus central M6 port\n\n'
            'Opening stays 14 x 38 mm\n'
            'Minimum nominal land beside slot: 1.175 mm\n'
            'Material beneath either groove: 2.2 mm\n\n'
            'Trial-fit the cord; sealing is not yet tested.',
            fontsize=12, linespacing=1.55, va='top', color='#253944')
    figure.savefig(destination / 'cap_seal_overview.png', dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)
    print(destination / 'cap_seal_overview.png')


if __name__ == '__main__':
    main()
