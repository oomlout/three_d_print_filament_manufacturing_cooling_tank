"""Render both printable pump-inlet halves and a dimensioned tube section."""
from pathlib import Path
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle

from action_preview_lifter import render
from working_oomp_populate import get_options, build_oomp_id
from working_pump_lifter import get_layout
from working_scad import get_gutter_sections


def main():
    options = [p for p in get_options() if p['oobb_type'] == 'lifter_pump_inlet']
    assets = Path('preview/pump_lifter_assets')
    assets.mkdir(parents=True, exist_ok=True)
    images = []
    for option in options:
        side = option['pump_half']
        shutil.copyfile(Path('parts') / build_oomp_id(option) / '3dpr.stl', assets / f'half_{side}.stl')
        scad = assets / f'half_{side}.scad'
        color = '[0.20,0.53,0.59]' if side == 'a' else '[0.85,0.57,0.26]'
        scad.write_text(f'color({color}) import("half_{side}.stl");\n', encoding='utf-8')
        images.append(render(scad, '0,0,0,30,0,20,500'))
    p = options[0]
    layout = get_layout(**p)
    depth = layout['half_depth']
    entry, cy, outlet = layout['entry_y'], layout['bend_centre_y'], layout['outlet_y']
    radius = p['tube_bend_radius_mm']
    tube = f'''module tube() {{
        translate([-80,{entry},{depth}]) rotate([0,90,0]) cylinder(h={80-radius},r=7,$fn=64);
        translate([{-radius},{cy},{depth}]) rotate_extrude(angle=90,$fn=180) translate([{radius},0,0]) circle(r=7,$fn=64);
        translate([0,{outlet},{depth}]) rotate([-90,0,0]) cylinder(h={cy-outlet},r=7,$fn=64);
    }}
    '''
    assembly = '''// Source axes: Y upright, Z along the gutter. Set gap=0 to assemble.
gap=12;
module a() { import("pump_lifter_assets/half_a.stl"); }
module b() { import("pump_lifter_assets/half_b.stl"); }
'''+tube+f'''
color([0.20,0.53,0.59]) translate([0,0,-gap]) a();
color([0.85,0.57,0.26]) translate([0,0,{2*depth}+gap]) rotate([0,180,0]) b();
// OD envelope only; actual tube has {p['tube_id_mm']:g} mm ID and {p['tube_wall_mm']:g} mm wall.
color([0.9,0.65,0.55,0.65]) tube();
'''
    Path('preview/pump_lifter_assembly.scad').write_text(assembly, encoding='utf-8')
    fig = plt.figure(figsize=(16, 8), facecolor='#faf9f5', layout='constrained')
    fig.suptitle('Pump inlet riser / one A + one B', fontsize=24, color='#253944')
    grid = fig.add_gridspec(2, 3, height_ratios=[4, 1])
    for index, png in enumerate(images):
        ax = fig.add_subplot(grid[0, index])
        ax.imshow(plt.imread(png))
        ax.set_axis_off()
        ax.set_title(('Half A / countersinks on underside', 'Half B / nut pockets on underside')[index], fontsize=13)
    ax = fig.add_subplot(grid[0, 2])
    ax.add_patch(Polygon(list(layout['outline'].exterior.coords), color='#338796'))
    for hole in layout['flow_holes']:
        ax.add_patch(Circle((hole['x'], hole['y']), hole['radius'], color='#faf9f5'))
    for hole in layout['fasteners']:
        ax.add_patch(Circle((hole['x'], hole['y']), 1.7, color='#faf9f5'))
    gutter = get_gutter_sections(**p)['gutter']
    for dy in (0, p['lift_height_mm']):
        ax.add_patch(Polygon([(x, y + dy) for x, y in gutter.exterior.coords], color='#303538'))
    envelope = layout['path'].buffer(7, cap_style='flat')
    ax.add_patch(Polygon(list(envelope.exterior.coords), color='#efbeab', alpha=0.95))
    ax.plot(*layout['path'].xy, color='#714b3a', linestyle='--', linewidth=0.8)
    ax.annotate('Side entry', xy=(-60, entry), xytext=(-82, 90), fontsize=11,
                arrowprops={'arrowstyle': '->'})
    ax.annotate('R40 bend', xy=(-12, 54), xytext=(23, 64), fontsize=11,
                arrowprops={'arrowstyle': '->'})
    ax.annotate('', xy=(12, outlet), xytext=(12, p['gutter_wall_mm']),
                arrowprops={'arrowstyle': '|-|', 'color': '#253944'})
    ax.text(17, 9, '15 mm', fontsize=10, va='center')
    ax.annotate('Water outlet', xy=(0, outlet), xytext=(-65, -15), fontsize=11,
                arrowprops={'arrowstyle': '->'})
    ax.set(aspect='equal', xlim=(-86, 80), ylim=(-22, 140))
    ax.set_axis_off()
    ax.set_title('Tube route / section across both gutters', fontsize=13)
    footer = fig.add_subplot(grid[1, :])
    footer.set_axis_off()
    footer.text(0.01, 0.9,
                '75 mm lift • 30 mm assembled thickness • each half 15 mm\n'
                '12 mm ID / 14 mm OD tube • 14.4 mm guide • 13.6 mm grip\n'
                'Six 12 mm flow holes + open outlet window • four M3 joints',
                va='top', fontsize=13, linespacing=1.6, color='#253944')
    footer.text(0.99, 0.9,
                'Print flat, channels upward. Fit one of each half.\n'
                'Outlet datum: 15 mm above the lower inside floor.\n'
                '1 mm tube wall confirmed; physical grip and bend fit pending.',
                ha='right', va='top', fontsize=12, linespacing=1.7, color='#785633')
    fig.savefig('preview/pump_lifter_overview.png', dpi=150)
    plt.close(fig)
    for option in options:
        shutil.copyfile('preview/pump_lifter_overview.png', Path('parts') / build_oomp_id(option) / 'pump_lifter_overview.png')
    print('preview/pump_lifter_overview.png')


if __name__ == '__main__':
    main()
