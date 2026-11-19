"""Flat-print split R40 hose guide, bolted to the offset JT-500 top."""
import math
import oobb
from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union


def get_layout(**p):
    r, start = p['tube_bend_radius_mm'], p['bend_start_above_mount_mm']
    inlet = p['outlet_offset_mm']
    cx = inlet + r
    end = cx + p['outlet_straight_mm']
    points = [(inlet, 0), (inlet, start)]
    points.extend((cx - r * math.cos(math.radians(a)), start + r * math.sin(math.radians(a))) for a in range(1, 91))
    points.append((end, start + r))
    path = LineString(points)
    joints = [(p['lower_joint']['x'], p['lower_joint']['y'])]
    joints.extend((cx - (r + p['joint_radial_offset_mm']) * math.cos(math.radians(a)),
                   start + (r + p['joint_radial_offset_mm']) * math.sin(math.radians(a))) for a in p['joint_angles_degrees'])
    outline = unary_union([path.buffer(p['guide_outer_radius_mm'], cap_style='flat', quad_segs=24),
                           box(-p['mount_foot_inboard_mm'], 0, p['mount_foot_outboard_mm'], p['mount_plate_thickness_mm']),
                           *[Point(x, y).buffer(p['joint_boss_radius_mm'], quad_segs=24) for x, y in joints]])
    assert outline.geom_type == 'Polygon' and not outline.interiors and outline.is_valid
    for x, y in joints:
        assert path.distance(Point(x, y)) > p['tube_guide_diameter_mm'] / 2 + 5
    sign = 1 if p['clamp_half'] == 'a' else -1
    # Countersunk screw length includes its head. Equal recesses leave the
    # declared protrusion beyond the outside face of the nut.
    recess = (2 * p['half_thickness_mm'] - p['joint_screw_length_mm']
              + p['joint_tip_protrusion_mm']) / 2
    if not 0 <= recess < p['half_thickness_mm'] - 5:
        raise ValueError('Joint screw length leaves insufficient material at the seam')
    return {
        'outline': affinity.scale(outline, xfact=sign, origin=(0, 0)),
        'path': affinity.scale(path, xfact=sign, origin=(0, 0)),
        'joints': [(sign * x, y) for x, y in joints],
        'sign': sign,
        'joint_recess_mm': recess,
        'bend_centre': [cx, start],
        'outlet': [end, start + r],
    }


def build(thing, **p):
    from working_scad import _append_section
    layout = get_layout(**p)
    d = p['half_thickness_mm']
    _append_section(thing, layout['outline'], d, 0, **p)
    cx, cy = layout['bend_centre']
    end, level = layout['outlet']
    guide, grip = p['tube_guide_diameter_mm']/2, p['tube_grip_diameter_mm']/2
    band, taper = p['tube_grip_length_mm'], p['tube_grip_transition_mm']
    module = f"pump_top_channel_half_{p['clamp_half']}"
    source = f'''module {module}() {{ scale([{layout['sign']},1,1]) union() {{
        translate([{p['outlet_offset_mm']},-1,{d}]) rotate([-90,0,0]) cylinder(h={p['rigid_clearance_height_mm']+1.01},r={p['rigid_clearance_diameter_mm']/2},$fn=64);
        translate([{p['outlet_offset_mm']},{p['rigid_clearance_height_mm']},{d}]) rotate([-90,0,0]) cylinder(h={cy-p['rigid_clearance_height_mm']+.01},r1={p['rigid_clearance_diameter_mm']/2},r2={guide},$fn=64);
        translate([{cx},{cy},{d}]) rotate([0,0,90]) rotate_extrude(angle=90,$fn=180) translate([{p['tube_bend_radius_mm']},0,0]) circle(r={guide},$fn=64);
        translate([{cx-.01},{level},{d}]) rotate([0,90,0]) cylinder(h={end-band-taper-cx+.02},r={guide},$fn=64);
        translate([{end-band-taper},{level},{d}]) rotate([0,90,0]) cylinder(h={taper},r1={guide},r2={grip},$fn=64);
        translate([{end-band},{level},{d}]) rotate([0,90,0]) cylinder(h={band+1},r={grip},$fn=64);
    }} }}'''
    oobb.append_full(thing, **{
        'type': 'negative',
        'shape': 'raw_scad',
        'module': module,
        'source': source,
        'pos': [0, 0, 0],
    })
    for x, y in layout['joints']:
        recess = layout['joint_recess_mm']
        if p['clamp_half'] == 'a':
            oobb.append_full(thing, **{
                'type': 'negative',
                'shape': 'oobb_screw_countersunk',
                'radius_name': 'm3',
                'depth': p['joint_screw_length_mm'],
                'zz': 'top',
                'nut_include': False,
                'overhang': True,
                'clearance': 'top',
                'mode': p.get('modes', ['3dpr']),
                'rot': [180, 0, 0],
                'pos': [x, y, recess],
            })
        else:
            oobb.append_full(thing, **{
                'type': 'negative',
                'shape': 'oobb_hole',
                'radius_name': 'm3',
                'depth': d + .02,
                'pos': [x, y, -.01],
            })
            for mode in p.get('modes', ['3dpr']):
                nut_depth = oobb.gv('nut_depth_m3', mode)
                oobb.append_full(thing, **{
                    'type': 'negative',
                    'shape': 'oobb_nut',
                    'radius_name': 'm3',
                    'mode': mode,
                    'depth': nut_depth,
                    'zz': 'bottom',
                    'overhang': True,
                    'clearance': 'top',
                    'rot': [180, 0, 0],
                    'pos': [x, y, recess + nut_depth],
                })
    oobb.append_full(thing, **{
        'type': 'negative',
        'shape': 'oobb_hole',
        'radius': p['wire_clearance_diameter_mm'] / 2,
        'depth': 100,
        'rot': [-90, 0, 0],
        'pos': [layout['sign'] * p['wire_offset_mm'], -1, d],
    })
    # M6 bearing face sits on the foot; local +Z points up toward the driver.
    oobb.append_full(thing, **{
        'type': 'negative',
        'shape': 'oobb_screw_socket_cap',
        'radius_name': 'm6',
        'mode': p.get('modes', ['3dpr']),
        'depth': p['mount_screw_length_mm'],
        'zz': 'none',
        'nut_include': False,
        'overhang': True,
        'clearance': 'top',
        'rot': [-90, 0, 0],
        'pos': [layout['sign'] * p['mount_row_offset_mm'], p['mount_plate_thickness_mm'], d - p['mount_hole_axial_mm']],
    })
    # Additional tool access is wider than the standard OOBB head clearance.
    oobb.append_full(thing, **{
        'type': 'negative',
        'shape': 'oobb_hole',
        'radius': p['mount_tool_radius_mm'],
        'depth': 100,
        'rot': [-90, 0, 0],
        'pos': [layout['sign'] * p['mount_row_offset_mm'], p['mount_plate_thickness_mm'], d - p['mount_hole_axial_mm']],
    })
