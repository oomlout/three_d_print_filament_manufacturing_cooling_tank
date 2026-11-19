"""Printable views of the two pump-top hose-clamp halves."""
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from action_preview_lifter import render
from working_oomp_populate import get_options, build_oomp_id
from working_split_parts import halves, mesh_path


def main():
    options = halves(next(o for o in get_options() if o['oobb_type']=='pump_hose_clamp'))
    assets = Path('preview/pump_top_clamp_assets')
    assets.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 2, figsize=(13, 11), facecolor='#faf9f5')
    for column, option in enumerate(options):
        side = option['clamp_half']
        shutil.copyfile(mesh_path(option), assets/f'half_{side}.stl')
        for row in (0, 1):
            ax = axes[row, column]
            scad = assets/f'half_{side}_{row}.scad'
            transform = '' if row == 0 else 'rotate([0,180,0]) '
            scad.write_text(f'color([0.85,0.57,0.26]) {transform}import("half_{side}.stl");\n')
            png = render(scad, '0,0,0,30,0,20,500')
            ax.imshow(plt.imread(png))
            ax.set_axis_off()
            detail = 'hose channel' if row == 0 else ('10 mm recessed countersinks' if side == 'a' else '10 mm recessed nut access')
            ax.set_title(f'Half {side.upper()} / {detail}', fontsize=13)
    figure.suptitle('Pump-top hose clamp / R40 bend toward the gutter edge', fontsize=19)
    figure.text(.5,.035,'Print one A and one B • 2 × M6 mounting holes, 30 mm apart • 4 mm mounting feet\n'
                 '12 mm ID / 14 mm OD tube • 14.4 mm guide • 13.6 mm outlet grip • 3 × M3×25 countersunk screws\n'
                 'Flat outer faces on bed; check supports for transverse M6 holes and driver openings.',
                 ha='center',fontsize=11,linespacing=1.6)
    figure.subplots_adjust(left=.02,right=.98,bottom=.12,top=.93,wspace=.02,hspace=.10)
    target = Path('preview/pump_top_clamp_overview.png')
    figure.savefig(target,dpi=160)
    plt.close(figure)
    for option in options:
        shutil.copyfile(target,Path('parts')/build_oomp_id(option)/'pump_top_clamp_overview.png')
    print(target)


if __name__ == '__main__':
    main()
