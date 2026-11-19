"""Two handed riser halves which capture a bent silicone pump-inlet tube."""
import math
from pathlib import Path
import re

import oobb
from shapely import affinity
from shapely.geometry import LineString, Point, box


def make_scad_portable(folder):
    """Inline this part's generated tube module before navigation copies it."""
    folder = Path(folder)
    for scad in folder.glob('*.scad'):
        source = scad.read_text(encoding='utf-8')
        def inline(match):
            helper = folder.parent / 'scad_reference' / match.group(1)
            return helper.read_text(encoding='utf-8')
        source = re.sub(r'use <\.\./scad_reference/(pump_(?:tube|top)_channel_half_[ab]\.scad)>;', inline, source)
        scad.write_text(source, encoding='utf-8')


def get_layout(**p):
    from working_scad import get_lifter_sections
    side = p['pump_half']
    if side not in ('a', 'b'):
        raise ValueError('Pump half must be A or B')
    if p['thickness_mm'] != p['support_thickness_mm']:
        raise ValueError('Flat-print pump halves require equal web and shoe thickness')
    half_depth = p['thickness_mm'] / 2
    guide = p['tube_guide_diameter_mm'] / 2
    grip = p['tube_grip_diameter_mm'] / 2
    radius = p['tube_bend_radius_mm']
    entry = (p['profile_height_mm'] + p['lift_height_mm']) / 2
    outlet = p['gutter_wall_mm'] + p['tube_outlet_above_floor_mm']
    cy = entry - radius
    if not 0 < grip < p['tube_od_mm'] / 2 <= guide < half_depth - 3:
        raise ValueError('Tube guide must fit with at least 3 mm of backing material')
    if entry - guide <= p['profile_height_mm'] or entry + guide >= p['lift_height_mm']:
        raise ValueError('Side-entry tube must clear both gutters')
    if cy < outlet + p['tube_grip_length_mm'] + p['tube_grip_transition_mm']:
        raise ValueError('Bend leaves insufficient straight length for the outlet grip')
    if p['outlet_window_width_mm'] < p['tube_od_mm'] + 2:
        raise ValueError('Outlet window needs room around the tube end')
    path_points = [(-70, entry), (-radius, entry)]
    path_points.extend((-radius + radius * math.cos(math.radians(a)),
                        cy + radius * math.sin(math.radians(a))) for a in range(89, -1, -1))
    path_points.append((0, outlet))
    path = LineString(path_points)
    outline = get_lifter_sections(**p)['web']
    outlet_cut = box(-p['outlet_window_width_mm'] / 2, -1,
                     p['outlet_window_width_mm'] / 2, outlet)
    outline = outline.difference(outlet_cut)
    if outline.geom_type != 'Polygon' or not outline.is_valid or outline.interiors:
        raise ValueError('Outlet relief must retain a connected riser')
    for hole in p['pump_flow_holes']:
        bore = Point(hole['x'], hole['y']).buffer(hole['radius'])
        if not outline.buffer(-2).covers(bore):
            raise ValueError('Flow hole too close to an edge or outlet window')
        if path.distance(Point(hole['x'], hole['y'])) < guide + hole['radius'] + 3:
            raise ValueError('Flow hole too close to tube channel')
    for fastener in p['pump_fasteners']:
        centre = Point(fastener['x'], fastener['y'])
        if not outline.buffer(-5).covers(centre) or path.distance(centre) < guide + 5:
            raise ValueError('Fastener conflicts with tube channel or outside edge')
        for hole in p['pump_flow_holes']:
            if centre.distance(Point(hole['x'], hole['y'])) < hole['radius'] + 6:
                raise ValueError('Fastener conflicts with flow hole')
    sign = 1 if side == 'a' else -1
    return {
        'outline': outline,
        'path': affinity.scale(path, xfact=sign, origin=(0, 0)),
        'half_depth': half_depth,
        'entry_y': entry,
        'outlet_y': outlet,
        'bend_centre_y': cy,
        'side_sign': sign,
        'flow_holes': [{**h, 'x': sign * h['x']} for h in p['pump_flow_holes']],
        'fasteners': [{**h, 'x': sign * h['x']} for h in p['pump_fasteners']],
    }


def channel_source(**p):
    layout = get_layout(**p)
    r = p['tube_bend_radius_mm']
    entry, cy, outlet = layout['entry_y'], layout['bend_centre_y'], layout['outlet_y']
    seam = layout['half_depth']
    guide, grip = p['tube_guide_diameter_mm'] / 2, p['tube_grip_diameter_mm'] / 2
    band = p['tube_grip_length_mm']
    transition = p['tube_grip_transition_mm']
    module = f"pump_tube_channel_half_{p['pump_half']}"
    # A true toroidal quarter bend, tangent to both straight tube sections.
    source = f'''module {module}() {{
        scale([{layout['side_sign']},1,1]) union() {{
            translate([-70,{entry},{seam}]) rotate([0,90,0]) cylinder(h={70-r+0.01},r={guide},$fn=64);
            translate([{-r},{cy},{seam}]) rotate_extrude(angle=90,$fn=180) translate([{r},0,0]) circle(r={guide},$fn=64);
            translate([0,{outlet-0.01},{seam}]) rotate([-90,0,0]) cylinder(h={band+0.01},r={grip},$fn=64);
            translate([0,{outlet+band},{seam}]) rotate([-90,0,0]) cylinder(h={transition},r1={grip},r2={guide},$fn=64);
            translate([0,{outlet+band+transition},{seam}]) rotate([-90,0,0]) cylinder(h={cy-outlet-band-transition+0.01},r={guide},$fn=64);
        }}
    }}'''
    return module, source


def build(thing, **p):
    from working_scad import _append_section
    layout = get_layout(**p)
    depth = layout['half_depth']
    _append_section(thing, layout['outline'], depth, 0, **p)
    pos = p.get('pos', [0, 0, 0])
    module, source = channel_source(**p)
    oobb.append_full(thing, **{
        'type': 'negative',
        'shape': 'raw_scad',
        'module': module,
        'source': source,
        'pos': list(pos),
    })
    for hole in layout['flow_holes']:
        oobb.append_full(thing, **{
            'type': 'negative',
            'shape': 'oobb_hole',
            'radius': hole['radius'],
            'depth': depth + 0.02,
            'pos': [pos[0] + hole['x'], pos[1] + hole['y'], pos[2] - 0.01],
        })
    for hole in layout['fasteners']:
        point = [pos[0] + hole['x'], pos[1] + hole['y'], pos[2]]
        if p['pump_half'] == 'a':
            oobb.append_full(thing, **{
                'type': 'negative',
                'shape': 'oobb_screw_countersunk',
                'radius_name': 'm3',
                'mode': p.get('modes', ['3dpr']),
                'depth': depth + 0.01,
                'zz': 'top',
                'hole': True,
                'nut_include': False,
                'overhang': True,
                'clearance': 'top',
                'rot': [180, 0, 0],
                'pos': point,
            })
        else:
            oobb.append_full(thing, **{
                'type': 'negative',
                'shape': 'oobb_hole',
                'radius_name': 'm3',
                'depth': depth + 0.02,
                'pos': [point[0], point[1], point[2] - 0.01],
            })
            for mode in p.get('modes', ['3dpr']):
                oobb.append_full(thing, **{
                    'type': 'negative',
                    'shape': 'oobb_nut',
                    'radius_name': 'm3',
                    'mode': mode,
                    'depth': oobb.gv('nut_depth_m3', mode),
                    'zz': 'bottom',
                    'hole': False,
                    'overhang': True,
                    'clearance': 'top',
                    'rot': [180, 0, 0],
                    'pos': [point[0], point[1], point[2] + oobb.gv('nut_depth_m3', mode)],
                })
