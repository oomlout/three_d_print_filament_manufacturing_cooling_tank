"""Inspect the saved Blender demonstration without rerendering it."""
from pathlib import Path
import json

import bpy
from mathutils import Vector

root = Path(__file__).resolve().parent


def bounds_mm(name):
    obj = bpy.data.objects[name]
    corners = [obj.matrix_world @ Vector(point) for point in obj.bound_box]
    return [[min(c[i] for c in corners) * 1000 for i in range(3)],
            [max(c[i] for c in corners) * 1000 for i in range(3)]]


lower = bounds_mm('Lower gutter - 600 mm with rear pump bay')
upper = bounds_mm('Upper gutter - 400 mm')
assert abs(lower[0][0] + 250) < 0.01
assert abs(lower[1][0] - 350) < 0.01
assert abs(upper[0][0] + 200) < 0.01
assert abs(upper[1][0] - 200) < 0.01
assert abs(upper[0][2] - 75) < 0.01
lower_water = bounds_mm('Lower water - half internal depth')
upper_water = bounds_mm('Upper water - 5 mm below rim')
assert abs(lower_water[1][2] - 30.375) < 0.01
assert abs(upper_water[1][2] - 128.5) < 0.01
filament = bpy.data.objects['Continuous filament through both central M6 holes']
assert abs(filament.data.bevel_depth * 2000 - 1.75) < 0.001
assert filament.data.materials[0].name == 'Black filament - diameter 1.75 mm'
filament_points = filament.data.splines[0].points
assert abs(filament_points[0].co.x * 1000 + 350) < 0.01
assert abs(filament_points[-1].co.x * 1000 - 450) < 0.01
assert all(abs(p.co.z * 1000 - 117.5) < 0.01 for p in filament_points)
assert len([o for o in bpy.data.objects if o.name.startswith('Lifter at ')]) == 4
assert len([o for o in bpy.data.objects if o.name.startswith('Cover INSIDE upper cap')]) == 2
assert bpy.data.objects['Lower gutter - 600 mm with rear pump bay'].data.materials[0].name == 'Black uPVC gutter'
report = {
    'status': 'passed',
    'lower_bounds_mm': lower,
    'upper_bounds_mm': upper,
    'lower_water_surface_mm': lower_water[1][2],
    'upper_water_surface_mm': upper_water[1][2],
    'filament_diameter_mm': filament.data.bevel_depth * 2000,
    'filament_colour': 'black',
    'filament_extents_mm': [-350, 450],
    'rear_clear_space_mm': lower[1][0] - upper[1][0],
    'rear_extension_from_previous_layout_mm': 100,
    'gutter_material': 'black',
    'lifter_halves': 4,
    'inside_covers': 2,
    'render_pixels': [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
}
(root / 'verification/demonstration_scene.json').write_text(json.dumps(report, indent=2) + '\n')
print('DEMONSTRATION_CHECK_PASSED')
