"""Run with Blender --background --factory-startup --python this_file.py.

Use -- --draft for a quick render; the final render also saves the .blend scene.
All object placement is expressed in mm and converted to metres at import.
"""
from pathlib import Path
import json
import math
import sys

import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'demonstration'
DATA = json.loads((DEST / 'scene_data.json').read_text())
SCALE = 0.001
DRAFT = '--draft' in sys.argv


def material(name, colour, roughness=0.3, metal=0, transmission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Transmission Weight'].default_value = transmission
    if transmission:
        bsdf.inputs['IOR'].default_value = 1.333
    return mat


def mesh_part(name, asset, offset, mat, flip=False, length_scale=1):
    bpy.ops.wm.stl_import(filepath=str(DEST / 'assets' / f'{asset}.stl'))
    obj = bpy.context.object
    obj.name = name
    # CAD = [cross-width, height, axial length]; world = [length, width, height].
    sign = -1 if flip else 1
    obj.matrix_world = Matrix((
        (0, 0, sign * SCALE * length_scale, offset[0] * SCALE),
        (sign * SCALE, 0, 0, offset[1] * SCALE),
        (0, SCALE, 0, offset[2] * SCALE),
        (0, 0, 0, 1),
    ))
    obj.data.materials.append(mat)
    return obj


def tube(name, points, radius_mm, mat):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 2
    curve.bevel_depth = radius_mm * SCALE
    curve.bevel_resolution = 4
    curve.use_fill_caps = True
    line = curve.splines.new('POLY')
    line.points.add(len(points) - 1)
    for target, point in zip(line.points, points):
        target.co = (*[c * SCALE for c in point], 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def sphere(name, centre, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=radius * SCALE,
                                        location=tuple(v * SCALE for v in centre))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def bolt(name, x, cross_y, height, direction):
    tube(name + ' shaft', [(x, cross_y, height), (x + direction * 8, cross_y, height)], 3, steel)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=5 * SCALE, depth=3.2 * SCALE,
                                       location=((x - direction * 1.6) * SCALE, cross_y * SCALE, height * SCALE),
                                       rotation=(0, math.pi / 2, 0))
    obj = bpy.context.object
    obj.name = name + ' hex head'
    obj.data.materials.append(steel)


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def area_light(name, pos, energy, size, colour):
    bpy.ops.object.light_add(type='AREA', location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.energy = energy
    obj.data.shape = 'DISK'
    obj.data.size = size
    obj.data.color = colour
    aim(obj, (0, 0, 0.06))


# This file is launched into a fresh, isolated Blender process.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24 if DRAFT else 96
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 12
scene.cycles.transmission_bounces = 8
scene.render.resolution_x = 1100 if DRAFT else 2200
scene.render.resolution_y = 800 if DRAFT else 1600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world.color = (0.35, 0.35, 0.35)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -1.5

gutter_material = material('Black uPVC gutter', (0.009, 0.012, 0.015), 0.28)
teal = material('Teal printed cap and lifter', (0.018, 0.33, 0.39), 0.3)
gold = material('Warm gold inside cover', (0.68, 0.35, 0.09), 0.32)
filament_material = material('Black filament - diameter 1.75 mm', (0.004, 0.005, 0.006), 0.25)
water = material('Clear blue cooling water', (0.12, 0.48, 0.65), 0.035, transmission=0.98)
water.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value = 0.15
steel = material('Stainless mounting hardware', (0.63, 0.68, 0.70), 0.25, metal=0.85)
rubber = material('2 mm seal cord', (0.015, 0.02, 0.022), 0.7)
ground = material('Warm studio ground', (0.64, 0.65, 0.64), 0.85)
silicone = material('Silicone hose - 12 mm ID 14 mm OD', (0.72, 0.83, 0.82), 0.3, transmission=0.2)
silicone.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value = 1.41
pump_grey = material('Nominal JT-500 pump housing', (0.18, 0.22, 0.24), 0.45)

mesh_part('Lower gutter - 600 mm with rear pump bay', 'lower_gutter', (-250, 0, 0), gutter_material)
mesh_part('Lower solid cap - outlet end', 'solid_cap', (-253, 0, 0), teal)
mesh_part('Lower solid cap - far end', 'solid_cap', (353, 0, 0), teal, flip=True)
mesh_part('Upper gutter - 400 mm', 'upper_gutter', (-200, 0, 75), gutter_material)
for x, flip, label in [(-203, False, 'front'), (203, True, 'rear')]:
    direction = -1 if flip else 1
    mesh_part(f'Upper slotted cap - {label}', 'open_cap', (x, 0, 75), teal, flip=flip)
    # Printed groove is at local Z=3; reverse the plate to mate at cap local Z=3.
    mesh_part(f'Cover INSIDE upper cap - {label}', 'cover',
              (x + direction * 6, 0, 117.5), gold, flip=not flip)
    for cross_y in (-15, 15):
        for relative_z in (27.5, 57.5):
            bolt(f'M6 {label} {cross_y} {relative_z}', x, cross_y, 75 + relative_z, direction)
    for cross_y in (-9.375, 9.375):
        tube(f'Cord top end {label} {cross_y}',
             [(x + direction * 3, cross_y, 132), (x + direction * 3, cross_y, 135)], 1, rubber)

for x in DATA['support_positions']:
    if x == DATA['pump']['rear_riser_position_mm']:
        mesh_part(f'Lifter at {x} - pump half A', 'pump_lifter_a', (x - 15, 0, 0), teal)
        mesh_part(f'Lifter at {x} - pump half B', 'pump_lifter_b', (x + 15, 0, 0), teal, flip=True)
    else:
        mesh_part(f'Lifter at {x} - half A', 'lifter_half', (x, 0, 0), teal)
        mesh_part(f'Lifter at {x} - half B', 'lifter_half', (x, 0, 0), teal, flip=True)

mesh_part('JT-500 holder base in rear bay', 'pump_holder_base', (0, 0, 0), gutter_material)
mesh_part('JT-500 holder top in rear bay', 'pump_holder_top', (0, 0, 0), teal)
mesh_part('JT-500 nominal pump in holder', 'pump_reference', (0, 0, 0), pump_grey)
mesh_part('Hose from pump through rear riser - 12 ID 14 OD', 'pump_hose', (0, 0, 0), silicone)

mesh_part('Lower water - half internal depth', 'lower_water', (-250, 0, 0), water)
mesh_part('Upper water - 5 mm below rim', 'upper_water', (-200, 0, 75), water)
tube('Continuous filament through both central M6 holes',
     [(DATA['filament_start'], 0, DATA['filament_axis_height']),
      (DATA['filament_end'], 0, DATA['filament_axis_height'])],
     DATA['filament_diameter'] / 2, filament_material)

for sign in (-1, 1):
    points = []
    for index in range(61):
        t = index / 60
        points.append((sign * (203 + 35 * t), 0.4 * math.sin(t * 10),
                       DATA['filament_axis_height'] - (DATA['filament_axis_height'] - DATA['lower_water_level']) * t * t))
    tube(f'Draining water stream {sign}', points, 2.05, water)
    impact = sign * 238
    for radius in (3, 5.5, 8.5):
        # Ripples are clipped to the small exposed landing zone near each end.
        ring = [(impact + radius * math.cos(a * math.pi / 40),
                 radius * math.sin(a * math.pi / 40), DATA['lower_water_level'] + 0.2)
                for a in range(81)]
        tube(f'Water ripple {sign} {radius}', ring, 0.18, water)
    for k in range(5):
        angle = k * 2.4
        sphere(f'Splash drop {sign} {k}',
               (impact + 4 * math.cos(angle), 4 * math.sin(angle), DATA['lower_water_level'] + 2 + k % 3),
               0.35 + (k % 2) * 0.15, water)

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.0065))
bpy.context.object.name = 'Studio ground'
bpy.context.object.data.materials.append(ground)
area_light('Large softbox', (-0.4, -0.5, 0.85), 100, 0.7, (1.0, 0.95, 0.87))
# Keep the fill lights on the camera side of the water's reflection direction.
# Rear-facing softboxes produced a large white reflection over the filament.
area_light('Side fill', (0.35, -0.5, 0.55), 30, 0.35, (0.78, 0.9, 1.0))
area_light('Front fill', (-0.55, -0.3, 0.4), 35, 0.45, (1, 1, 1))
bpy.ops.object.camera_add(location=(-0.72, -0.9, 0.65))
camera = bpy.context.object
camera.name = 'Demonstration camera'
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 0.78
camera.data.clip_start = 0.001
aim(camera, (0.035, 0, 0.067))
scene.camera = camera
bpy.ops.object.camera_add(location=(0.45, -0.65, 0.50))
detail_camera = bpy.context.object
detail_camera.name = 'Rear pump and hose detail camera'
detail_camera.data.type = 'ORTHO'
detail_camera.data.ortho_scale = 0.43
detail_camera.data.clip_start = 0.001
aim(detail_camera, (0.22, -0.02, 0.075))
scene.render.filepath = str(DEST / ('cooling_tank_draft.png' if DRAFT else 'cooling_tank_render.png'))
if not DRAFT:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST / 'cooling_tank_demonstration.blend'))
bpy.ops.render.render(write_still=True)
print('DEMONSTRATION_RENDER_COMPLETE', scene.render.filepath)
if not DRAFT:
    scene.camera = detail_camera
    scene.render.filepath = str(DEST / 'pump_hose_detail.png')
    bpy.ops.render.render(write_still=True)
    print('PUMP_DETAIL_RENDER_COMPLETE', scene.render.filepath)
