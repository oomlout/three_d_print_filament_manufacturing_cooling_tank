"""Two identical transverse ribs seat the offset pump holder level."""
from shapely import affinity
from shapely.geometry import box
import oobb


def get_layout(**p):
    from working_scad import get_gutter_sections
    clearance = p['gutter_side_clearance_mm']
    seat = p['holder_seat_height_mm']
    depth = p['support_thickness_mm']
    pocket = p['foot_pocket_width_mm']
    if seat < 20 or pocket >= depth or pocket <= 12:
        raise ValueError('Cradle requires adequate seat height, foot clearance and end walls')
    # Touch the flat floor; retain side clearance around the rounded contour.
    cavity = get_gutter_sections(**p)['cavity']
    contact = affinity.translate(cavity.buffer(-clearance, join_style='round', quad_segs=90), yoff=-clearance)
    section = contact.intersection(box(-100, 0, 100, seat + p['foot_locating_height_mm']))
    feet = [-p['holder_offset_toward_edge_mm'] + side * p['foot_pitch_mm']/2 for side in (-1, 1)]
    for x in feet:
        if not section.covers(box(x-pocket/2, seat-.1, x+pocket/2, seat+.1)):
            raise ValueError('Foot pocket is outside the cradle seat')
    for x in p['flow_hole_x_mm']:
        from shapely.geometry import Point
        if not section.covers(Point(x, p['flow_hole_height_mm']).buffer(p['flow_hole_diameter_mm']/2 + 2)):
            raise ValueError('Flow hole leaves less than 2 mm of surrounding material')
    return {
        'section': section,
        'feet': feet,
    }


def build(thing, **p):
    from working_scad import _append_section
    layout = get_layout(**p)
    depth = p['support_thickness_mm']
    pocket = p['foot_pocket_width_mm']
    _append_section(thing, layout['section'], depth, 0, **p)
    for x in layout['feet']:
        oobb.append_full(thing, **{
            'type': 'negative',
            'shape': 'oobb_cube_center',
            'size': [pocket, 2*p['foot_locating_height_mm'], pocket],
            'pos': [x, p['holder_seat_height_mm'] + p['foot_locating_height_mm'], (depth-pocket)/2],
        })
    for x in p['flow_hole_x_mm']:
        oobb.append_full(thing, **{
            'type': 'negative',
            'shape': 'oobb_hole',
            'radius': p['flow_hole_diameter_mm']/2,
            'depth': depth + .02,
            'pos': [x, p['flow_hole_height_mm'], -.01],
        })
