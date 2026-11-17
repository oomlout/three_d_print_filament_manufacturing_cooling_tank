"""Render the printable half and its mid-span placement in continuous gutters."""
from pathlib import Path
import subprocess
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from working_oomp_populate import get_options, build_oomp_id


def render(source, camera):
    source = source.resolve()
    output = source.with_suffix(".png")
    command = [
        "openscad",
        "--render",
        "--autocenter",
        "--viewall",
        "--projection=o",
        f"--camera={camera}",
        "--colorscheme=Tomorrow",
        "--imgsize=1200,1000",
        "-o",
        str(output),
        str(source),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    if "WARNING:" in result.stderr or "ERROR:" in result.stderr:
        raise RuntimeError(result.stderr)
    return output


def main():
    options = get_options()
    gutter = next(o for o in options if o["oobb_type"] == "gutter_square" and o["length_mm"] == 300)
    for option in options:
        if option["oobb_type"] != "lifter":
            continue
        part_id = build_oomp_id(option)
        folder = Path("parts") / part_id
        # A short local include also avoids legacy Windows include-path limits.
        shutil.copyfile(
            Path("parts") / build_oomp_id(gutter) / "3dpr.scad",
            folder / "gutter_reference.scad",
        )
        single = folder / "preview_half.scad"
        single.write_text(
            'color([0.20, 0.53, 0.59]) { include <3dpr.scad>; }\n',
            encoding="utf-8",
        )
        half_png = render(single, "0,0,0,35,0,25,500")

        # Rotation is about the upright profile Y axis, NOT a mirror operation.
        # The gutters are cut at the joining plane to reveal the bearing surfaces.
        assembly = folder / "assembly_cutaway.scad"
        assembly.write_text(
            'module half() { include <3dpr.scad>; }\n'
            'module gutter_cutaway() {\n'
            '  intersection() {\n'
            '    translate([0,0,-300]) { include <gutter_reference.scad>; }\n'
            '    translate([-100,-1,-60]) cube([200,160,60]);\n'
            '  }\n'
            '}\n'
            'rotate([90,0,0]) {\n'
            '  color([0.20,0.53,0.59]) half();\n'
            '  color([0.85,0.57,0.26]) rotate([0,180,0]) half();\n'
            '  color([0.74,0.77,0.79]) gutter_cutaway();\n'
            f'  color([0.74,0.77,0.79]) translate([0,{option["lift_height_mm"]},0]) gutter_cutaway();\n'
            '}\n',
            encoding="utf-8",
        )
        render(assembly, "180,-240,180,0,0,65")

        mid_span = folder / "assembly_mid_span.scad"
        mid_span.write_text(
            '// Both 300 mm gutters continue 150 mm each way past the support.\n'
            'module half() { include <3dpr.scad>; }\n'
            'module gutter_span() {\n'
            '  translate([0,0,-150]) { include <gutter_reference.scad>; }\n'
            '}\n'
            'rotate([90,0,0]) {\n'
            '  color([0.20,0.53,0.59]) half();\n'
            '  color([0.85,0.57,0.26]) rotate([0,180,0]) half();\n'
            '  color([0.74,0.77,0.79,0.35]) gutter_span();\n'
            f'  color([0.74,0.77,0.79,0.35]) translate([0,{option["lift_height_mm"]},0]) gutter_span();\n'
            '}\n',
            encoding="utf-8",
        )
        assembly_png = render(mid_span, "240,-320,240,0,0,65")

        # An editable exploded assembly also shows exactly how the copies meet.
        exploded = folder / "assembly_exploded.scad"
        exploded.write_text(
            'module half() { include <3dpr.scad>; }\n'
            'color([0.20,0.53,0.59]) translate([0,0,10]) half();\n'
            'color([0.85,0.57,0.26]) translate([0,0,-10]) rotate([0,180,0]) half();\n',
            encoding="utf-8",
        )

        figure = plt.figure(figsize=(14, 7.8), facecolor="#faf9f5", layout="constrained")
        figure.suptitle("Cooling tank / mid-span lifter", fontsize=22, fontweight="bold", color="#253944")
        grid = figure.add_gridspec(2, 3, height_ratios=[4, 1])
        for index, png, title in [
            (0, half_png, "Print this half twice"),
            (1, assembly_png, "Both gutters continue past the lifter"),
        ]:
            ax = figure.add_subplot(grid[0, index])
            ax.imshow(plt.imread(png))
            ax.set_axis_off()
            ax.set_title(title, fontsize=15, color="#253944")

        ax = figure.add_subplot(grid[0, 2])
        ax.set_facecolor("#faf9f5")
        # Side elevation: axial direction horizontal; heights use real datums.
        lift = option["lift_height_mm"]
        wall = option["gutter_wall_mm"]
        support_depth = option["support_thickness_mm"]
        web_depth = option["thickness_mm"]
        top = lift + option["upper_cradle_height_mm"]
        ax.add_patch(Rectangle((-web_depth / 2, wall), web_depth, top - wall, color="#338796"))
        ax.add_patch(Rectangle((-support_depth / 2, wall), support_depth,
                              option["lower_shoe_height_mm"], color="#338796"))
        ax.add_patch(Rectangle((-support_depth / 2, lift - option["upper_shoe_below_seat_mm"]),
                              support_depth, option["upper_shoe_below_seat_mm"] + option["upper_cradle_height_mm"],
                              color="#338796"))
        for y in (0, option["lift_height_mm"]):
            ax.add_patch(Rectangle((-150, y), 300, option["profile_height_mm"],
                                  fill=False, edgecolor="#737b82", linewidth=2))
            ax.plot([-150, 150], [y, y], color="#737b82", linewidth=3)
        ax.annotate("", xy=(165, 0), xytext=(165, option["lift_height_mm"]),
                    arrowprops={"arrowstyle": "|-|", "color": "#253944"})
        ax.text(173, option["lift_height_mm"] / 2, f'{option["lift_height_mm"]:g} mm lift',
                rotation=90, va="center", fontsize=12)
        ax.annotate('Lifter at mid-span', xy=(0, 40), xytext=(-140, -40), fontsize=11,
                    arrowprops={"arrowstyle": "->", "color": "#253944"})
        ax.set(aspect="equal", xlim=(-155, 195), ylim=(-50, option["lift_height_mm"] + 65))
        ax.set_axis_off()
        ax.set_title("Side elevation / continuous spans", fontsize=15, color="#253944")

        footer = figure.add_subplot(grid[1, :])
        footer.set_axis_off()
        footer.text(0.02, 0.85,
                    f'{option["thickness_mm"]:g} mm assembled web / {option["support_thickness_mm"]:g} mm assembled supports\n'
                    '9 x 12 mm flow holes / 4 x M3 countersunk screws and nuts\n'
                    'Upper saddle 5 mm narrower / side contact stops 7.5 mm below rim\n'
                    'Lower foot: 5 mm inside radius; no additional width.',
                    va="top", fontsize=13, linespacing=1.65, color="#253944")
        footer.text(0.98, 0.85, 'One STL, two copies\nProfile fit and load capacity\nrequire a physical check.',
                    ha="right", va="top", fontsize=12, linespacing=1.65, color="#785633")
        figure.savefig(folder / "lifter_overview.png", dpi=160)
        plt.close(figure)
        print(folder / "lifter_overview.png")


if __name__ == "__main__":
    main()
