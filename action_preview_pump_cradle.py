"""Render the actual cradle STL and its installed supporting arrangement."""
from pathlib import Path
import shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from action_preview_lifter import render
from working_oomp_populate import get_options, build_oomp_id
from working_split_parts import mesh_path


def main():
    p = next(o for o in get_options() if o['oobb_type']=='pump_support_cradle')
    assets = Path('preview/pump_cradle_assets')
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(mesh_path(p), assets/'rib.stl')
    for name in ('pump_holder_base', 'pump_cradle_front', 'pump_cradle_rear', 'lower_gutter'):
        shutil.copyfile(Path('demonstration/assets')/f'{name}.stl', assets/f'{name}.stl')
    scenes = [
        'color([0.02,0.55,0.62]) import("rib.stl");',
        '''color([0.02,0.55,0.62]) {
            import("pump_cradle_front.stl"); import("pump_cradle_rear.stl");
        }
        color([0.12,0.12,0.12]) import("pump_holder_base.stl");
        color([0.2,0.2,0.2,0.16]) intersection() {
            translate([0,0,-250]) import("lower_gutter.stl");
            translate([-100,-1,239]) cube([200,70,92]);
        }''',
    ]
    fig, axes = plt.subplots(1,2,figsize=(13,7),facecolor='#faf9f5')
    for index, (scene, ax) in enumerate(zip(scenes, axes)):
        if index == 1:
            scene = 'multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) {\n' + scene + '\n}'
        source = assets/f'view_{index}.scad'
        source.write_text(scene)
        png = render(source, '0,0,0,55,0,210,500' if index == 0 else '0,0,0,65,0,25,500')
        ax.imshow(plt.imread(png))
        ax.axis('off')
        ax.set_title(['One rib / print two identical copies', 'Two level ribs under all four holder feet'][index],fontsize=13)
    fig.suptitle('Pump support cradle / 11 mm toward the visible edge',fontsize=19)
    fig.text(.5,.07,'26 mm foot-seat height above gutter outside bottom • 18 mm thick • 60 mm rib spacing\n'
             'Four 10 mm flow holes per rib • 12.6 mm foot pockets • No change to the pump-holder meshes',
             ha='center',fontsize=11,linespacing=1.6)
    fig.subplots_adjust(left=.02,right=.98,bottom=.18,top=.88,wspace=.02)
    target = Path('preview/pump_cradle_overview.png')
    fig.savefig(target,dpi=160)
    plt.close(fig)
    shutil.copyfile(target, Path('parts')/build_oomp_id(p)/'pump_cradle_overview.png')
    print(target)


if __name__ == '__main__':
    main()
