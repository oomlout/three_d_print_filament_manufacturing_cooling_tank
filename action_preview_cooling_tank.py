"""Reproducible cap overview rendered directly from the generated SCAD."""
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from working_oomp_populate import get_options, build_oomp_id


def main():
    destination = Path('preview')
    destination.mkdir(exist_ok=True)
    figure = plt.figure(figsize=(12, 10), facecolor='#faf9f5', layout='constrained')
    figure.suptitle('Cooling tank / solid and grooved open caps',
                   fontsize=21, fontweight='bold', color='#253944')
    options = [o for o in get_options() if o['oobb_type'].startswith('cap_end_')]
    for index, option in enumerate(options):
        variant = 'open' if option['oobb_type'] == 'cap_end_open' else 'solid'
        source = destination / f"cap_{variant}_{option['total_depth_mm']}_render.scad"
        png = source.with_suffix('.png')
        source.write_text('color([0.20, 0.53, 0.59]) {\n'
                          f"include <../parts/{build_oomp_id(option)}/3dpr.scad>;\n"
                          '}\n', encoding='utf-8')
        result = subprocess.run(
            ['openscad', '--render', '--autocenter', '--viewall',
             '--projection=o', '--camera=0,0,0,35,0,15,500',
             '--colorscheme=Tomorrow', '--imgsize=1100,700',
             '-o', str(png), str(source)], check=True, capture_output=True, text=True)
        if 'WARNING:' in result.stderr or 'ERROR:' in result.stderr:
            raise RuntimeError(result.stderr)
        ax = figure.add_subplot(3, 2, index + 1, facecolor='#faf9f5')
        ax.imshow(plt.imread(png))
        ax.set_axis_off()
        ax.set_title(f"{variant.capitalize()} / {option['total_depth_mm']} mm overall\n"
                     f"3 mm face + {option['insertion_depth_mm']:g} mm insertion",
                     fontsize=14, color='#253944')

    ax = figure.add_subplot(3, 1, 3, facecolor='#faf9f5')
    ax.set_axis_off()
    ax.text(0.03, 0.9, '6 mm lip around the entire outside', fontsize=16,
            fontweight='bold', color='#253944', va='top')
    ax.text(0.03, 0.72, 'Face: 126 x 70.5 mm, 3 mm thick\n'
            'Insertion ledge: 3 mm wall, 5.5 mm inside bottom radius\n'
            'Flat ledge ends: 9.5 mm below the gutter rim',
            fontsize=12, linespacing=1.6, va='top', color='#253944')
    ax.text(0.55, 0.9, 'Open variant', fontsize=16, fontweight='bold',
            color='#253944', va='top')
    ax.text(0.55, 0.72, 'Slot: 14 mm wide x 38 mm down from enlarged top\n'
            'Bottom corners: R5; top mouth: square\n'
            '4 x M6: 30 x 30 mm pattern on the 15 mm OOBB grid\n'
            'Fixed hole pattern / 6 mm cover overlap below slot',
            fontsize=12, linespacing=1.6, va='top', color='#253944')
    figure.savefig(destination / 'cooling_tank_caps.png', dpi=180, facecolor=figure.get_facecolor())
    plt.close(figure)
    print(destination / 'cooling_tank_caps.png')


if __name__ == '__main__':
    main()
