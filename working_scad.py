import copy
import oobb
import yaml
import os
import scad_help

def main(**kwargs):
    make_scad(**kwargs)

def make_scad(**kwargs):
    typ = scad_help.get_typ(**kwargs)
    oomp_mode = "project"
    #oomp_mode = "oobb"
    filt = ""
    build_variables = scad_help.get_build_variables(typ, filter=filt)
    if True:
        kwargs.setdefault("filter", build_variables["filter"])
        kwargs.setdefault("save_type", build_variables["save_type"])
        kwargs.setdefault("navigation", build_variables["navigation"])
        kwargs.setdefault("overwrite", build_variables["overwrite"])
        kwargs.setdefault("modes", build_variables["modes"])
        kwargs["oomp_mode"] = oomp_mode
        kwargs["oomp_run"] = build_variables["oomp_run"]
    parts = get_parts(kwargs, oomp_mode)
    
    kwargs["parts"] = parts

    scad_help.make_parts(**kwargs)

    if kwargs["navigation"]:
        oobb_style = False  
        sort = scad_help.get_navigation_sort(oobb_style=oobb_style)
        scad_help.generate_navigation(sort=sort)

def get_parts(kwargs, oomp_mode):
    import working_cad
    parts = []    

    #load parts from parts/folder/working.yaml
    parts_directory = os.path.join(os.path.dirname(__file__), "parts")
    if not os.path.isdir(parts_directory):
        return parts

    for folder in os.listdir(parts_directory):
        folder_path = os.path.join(parts_directory, folder)
        if not os.path.isdir(folder_path):
            continue

        working_yaml_path = os.path.join(folder_path, "working.yaml")
        if not os.path.isfile(working_yaml_path):
            continue

        with open(working_yaml_path, "r", encoding="utf-8") as infile:
            loaded_part = yaml.safe_load(infile)

        if not isinstance(loaded_part, dict):
            continue

        oobb_details = loaded_part.get("oobb_details")
        if not isinstance(oobb_details, dict):
            continue

        if not working_cad.enabled(oobb_details, "scad"):
            continue
        part = loaded_part

        part_kwargs = copy.deepcopy(kwargs)
        part_kwargs.update(copy.deepcopy(loaded_part.get("kwargs", {})))
        part_kwargs.update(copy.deepcopy(oobb_details))
        for key in ("modes", "save_type", "overwrite", "filter", "navigation", "oomp_run"):
            if key in kwargs:
                part_kwargs[key] = copy.deepcopy(kwargs[key])
        part["kwargs"] = working_cad.geometry_parameters(part_kwargs)
        part["oobb_name"] = part.get("oobb_name", oobb_details.get("oobb_name", oobb_details.get("oobb_type", "default")))

        if oomp_mode == "oobb":
            part["kwargs"]["oomp_size"] = part["oobb_name"]

        parts.append(part)


    return parts

def get_base(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 3)                    
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")
    


    #add plate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "positive"
        p3["shape"] = f"oobb_plate"    
        p3["depth"] = depth
        #p3["holes"] = True         uncomment to include default holes
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)         
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)
    
    #add holes seperate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"oobb_holes"
        p3["both_holes"] = True  
        p3["depth"] = depth
        p3["holes"] = "perimeter"
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)         
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)

    #add a test screw_countersunk
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"screw_countersunk"
        p3["depth"] = depth
        p3["radius_name"] = "m3"
        pos1 = copy.deepcopy(pos)         
        pos1[2] += depth
        p3["pos"] = pos1
        p3["m"] = "#"
        oobb.append_full(thing,**p3)

    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)

def get_hole_cover(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 3)                    
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")
    
    diameter = kwargs.get("diameter", 10)
    clearance = kwargs.get("clearance", 0.5)
    thickness_wall = 2
    depth_taper = 3
    depth_top = 2
    diameter_top_extra = 10
    radius_gap=6
    diameter_top_taper = 5

    #add cylinder
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"    
    dep = depth - depth_taper 
    p3["depth"] = dep
    p3["radius"] = (diameter-clearance)/2
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)         
    pos1[2] += depth_taper + dep/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)
    
    #add cylinder taper using radius_1 and radius_2
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_taper
    p3["radius_2"] = (diameter-clearance)/2
    p3["radius_1"] = (diameter+clearance-thickness_wall)/2    
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth_taper/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)

    #add top cylinder
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_top
    dia = diameter+diameter_top_extra
    p3["radius_2"] = (dia-diameter_top_taper)/2
    p3["radius_1"] = (dia)/2
    #p3["m"] = "#"
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth-depth_top/2
    p3["pos"] = pos1
    oobb.append_full(thing,**p3)

    

    #add hole
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth - depth_top/2
    p3["radius"] = (diameter+clearance-thickness_wall)/2    

    pos1 = copy.deepcopy(pos)
    pos1[2] += depth/2 - depth_top/2
    p3["pos"] = pos1
    #p3["m"] = "#"
    oobb.append_full(thing,**p3)

    
    #diameter_top 30
    #add hole_top
    diameter_top_hole = 30
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "negative"
    p3["shape"] = f"oobb_cylinder"
    p3["depth"] = depth_top
    p3["radius"] = (diameter_top_hole)/2
    pos1 = copy.deepcopy(pos)
    pos1[2] += depth - depth_top/2

    p3["pos"] = pos1
    p3["m"] = "#"
    oobb.append_full(thing,**p3)

    pos1 = copy.deepcopy(pos)
    pos1[1] += 100



    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)

    
def get_plate(thing, **kwargs):

    prepare_print = kwargs.get("prepare_print", False)
    width = kwargs.get("width", 1)
    height = kwargs.get("height", 1)
    depth = kwargs.get("depth", 3)
    rot = kwargs.get("rot", [0, 0, 0])
    pos = kwargs.get("pos", [0, 0, 0])
    extra = kwargs.get("extra", "")



    #add plate
    if True:
        if width == 1 and height == 1:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "positive"
            p3["shape"] = f"oobb_plate"
            p3["depth"] = depth
            #p3["holes"] = True         uncomment to include default holes
            #p3["m"] = "#"
            pos1 = copy.deepcopy(pos)
            p3["pos"] = pos1
            oobb.append_full(thing,**p3)
        else:
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "positive"
            p3["shape"] = f"oobb_rounded_rectangle_rounded"
            wid = (width *15)-1
            hei = (height *15)-1
            dep = depth
            size = [wid, hei, dep]
            p3["radius_rounded"] = 1.5
            p3["size"] = size
            #p3["holes"] = True         uncomment to include default holes
            #p3["m"] = "#"
            pos1 = copy.deepcopy(pos)
            p3["pos"] = pos1
            oobb.append_full(thing,**p3)

    #add holes seperate
    if True:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "p"
        p3["shape"] = f"oobb_holes"
        p3["both_holes"] = True
        p3["depth"] = depth
        p3["holes"] = "all"
        #p3["m"] = "#"
        pos1 = copy.deepcopy(pos)
        p3["pos"] = pos1
        oobb.append_full(thing,**p3)

    if prepare_print:
        scad_help.prepare_base_for_print(thing, pos, **kwargs)


def _rounded_profile_corner(previous, vertex, following, radius, step_degrees):
    """Tangent circular fillet for a counterclockwise convex profile vertex."""
    import math
    ax, ay = previous[0] - vertex[0], previous[1] - vertex[1]
    bx, by = following[0] - vertex[0], following[1] - vertex[1]
    la, lb = math.hypot(ax, ay), math.hypot(bx, by)
    ax, ay, bx, by = ax / la, ay / la, bx / lb, by / lb
    angle = math.acos(max(-1.0, min(1.0, ax * bx + ay * by)))
    tangent = radius / math.tan(angle / 2)
    if tangent >= min(la, lb) / 2:
        raise ValueError("Profile fillets are too large for adjacent edges")
    bisector_length = math.hypot(ax + bx, ay + by)
    centre_distance = radius / math.sin(angle / 2)
    cx = vertex[0] + (ax + bx) / bisector_length * centre_distance
    cy = vertex[1] + (ay + by) / bisector_length * centre_distance
    start = math.atan2(vertex[1] + ay * tangent - cy, vertex[0] + ax * tangent - cx)
    sweep = math.pi - angle
    segments = max(2, math.ceil(math.degrees(sweep) / step_degrees))
    return [(cx + radius * math.cos(start + sweep * i / segments),
             cy + radius * math.sin(start + sweep * i / segments))
            for i in range(segments + 1)]


def get_gutter_sections(**kwargs):
    """Shared XY cross-sections in mm; Y=0 is the outside base.

    Offsets act normal to the sloping/curved surfaces, not just in X or Y.
    Extend above the mouth before offsetting so the ledge remains U-shaped.
    The small inward top beads are estimates of the supplied raster drawing.
    """
    from shapely.geometry import Polygon, box
    from working_oomp_populate import PROFILE
    p = {key: kwargs.get(key, value) for key, value in PROFILE.items()}
    w, h, t = p["profile_width_mm"], p["profile_height_mm"], p["gutter_wall_mm"]
    shoulder, base = p["shoulder_height_mm"], p["bottom_virtual_width_mm"]
    if not (0 < base < w and 0 < shoulder < h and 0 < t < min(w, h) / 2):
        raise ValueError("Invalid gutter envelope or thickness")
    if not (0 < p["curve_step_degrees"] <= 10):
        raise ValueError("curve_step_degrees must be between 0 and 10")
    vertices = [(-w/2, h + 30), (-w/2, shoulder), (-base/2, 0),
                (base/2, 0), (w/2, shoulder), (w/2, h + 30)]
    radii = [0, p["shoulder_radius_mm"], p["bottom_radius_mm"],
             p["bottom_radius_mm"], p["shoulder_radius_mm"], 0]
    if min(radii[1:5]) <= t:
        raise ValueError("Outer corner radii must exceed the gutter wall thickness")
    points = []
    for index, vertex in enumerate(vertices):
        if radii[index]:
            points.extend(_rounded_profile_corner(vertices[index-1], vertex,
                          vertices[(index+1) % len(vertices)], radii[index], p["curve_step_degrees"]))
        else:
            points.append(vertex)
    extended = Polygon(points)
    clip = box(-w, -h, w, h)
    face = extended.intersection(clip)
    cavity = extended.buffer(-t, join_style="mitre")
    plain_cavity = cavity
    lip, lip_h, tip_drop = p["lip_projection_mm"], p["lip_height_mm"], p["lip_tip_drop_mm"]
    if not (0 <= lip < w/4 and 0 < tip_drop < lip_h < h - shoulder):
        raise ValueError("Invalid top lip dimensions")
    for sign in (-1, 1):
        edge = sign * (w/2 - t)
        bead = Polygon([(edge, h), (edge - sign * lip, h - tip_drop),
                        (edge, h - lip_h), (edge + sign * t, h - lip_h),
                        (edge + sign * t, h)])
        cavity = cavity.difference(bead)
    gutter = face.difference(cavity)
    clearance = float(kwargs.get("fit_clearance_mm", 0.0))
    wall = float(kwargs.get("ledge_wall_mm", 3.0))
    if clearance < 0 or wall <= 0:
        raise ValueError("Fit clearance must be nonnegative and ledge wall positive")
    setback = float(kwargs.get("ledge_top_setback_mm", 0.0))
    if not 0 <= setback < h - t:
        raise ValueError("Ledge setback must leave a positive-height insertion wall")
    ledge_cavity = plain_cavity if kwargs.get("ledge_ignore_clip", False) else cavity
    ledge_outer = ledge_cavity.buffer(-clearance, join_style="round", quad_segs=90) if clearance else ledge_cavity
    ledge_void = ledge_outer.buffer(-wall, join_style="round", quad_segs=90)
    if ledge_void.is_empty:
        raise ValueError("Ledge wall consumes the entire gutter opening")
    ledge_clip = box(-w, -h, w, h - setback)
    ledge = ledge_outer.difference(ledge_void).intersection(ledge_clip)
    sections = {"face": face, "gutter": gutter, "cavity": cavity.intersection(clip), "ledge": ledge}
    for name, section in sections.items():
        if section.geom_type != "Polygon" or not section.is_valid or section.is_empty or section.interiors:
            raise ValueError(f"Expected a valid simple polygon for {name}")
    return sections


def _append_section(thing, section, extrusion, z, **kwargs):
    """An ordinary OOBB polygon extrusion, bundled into the generated SCAD."""
    p3 = copy.deepcopy(kwargs)
    p3["type"] = "positive"
    p3["shape"] = "polygon"
    p3["points"] = [[round(x, 7), round(y, 7)] for x, y in list(section.exterior.coords)[:-1]]
    # The primitive dispatch checks height before depth: set both explicitly.
    p3["height"] = extrusion
    p3["depth"] = extrusion
    p3["pos"] = copy.deepcopy(kwargs.get("pos", [0, 0, 0]))
    p3["pos"][2] += z
    oobb.append_full(thing, **p3)


def get_cap_sections(**kwargs):
    """Expand only the butt plate; retain the established insertion fit."""
    sections = get_gutter_sections(**kwargs)
    lip = float(kwargs.get("outer_lip_mm", 0))
    if lip < 0:
        raise ValueError("Outer lip cannot be negative")
    if lip:
        sections["face"] = sections["face"].buffer(lip, quad_segs=90)
    return sections


def get_cap_opening_layout(**kwargs):
    width = float(kwargs["opening_width_mm"])
    depth = float(kwargs["opening_depth_mm"])
    radius = float(kwargs["opening_bottom_corner_radius_mm"])
    top = float(kwargs["profile_height_mm"]) + float(kwargs["outer_lip_mm"])
    pitch = float(kwargs["hole_grid_pitch_mm"])
    if not (0 < radius <= width / 2 and 2 * radius < depth < top and pitch > 0):
        raise ValueError("Invalid opening dimensions, corner radius or hole pitch")
    centre_y = top - depth / 2
    # Keep the cover's mounting pattern fixed when adjusting the slot floor.
    # Missing offset reproduces the original version 4 opening and pattern.
    hole_centre_y = top - float(kwargs.get("hole_pattern_top_offset_mm", depth / 2))
    return {
        "width": width,
        "depth": depth,
        "radius": radius,
        "top": top,
        "bottom": top - depth,
        "centre_y": centre_y,
        "holes": [
            {"x": x, "y": hole_centre_y + y}
            for x in (-pitch, pitch)
            for y in (-pitch, pitch)
        ],
    }


def get_cap_end_solide(thing, **kwargs):
    total = float(kwargs.get("total_depth_mm", kwargs.get("depth", 15)))
    plate = float(kwargs.get("front_plate_mm", 3))
    if not 0 < plate < total:
        raise ValueError("Total depth must exceed the positive front plate thickness")
    sections = get_cap_sections(**kwargs)
    _append_section(thing, sections["face"], plate, 0, **kwargs)
    # Internal overlap makes the union robust; external dimensions stay exact.
    overlap = min(0.01, plate / 10)
    _append_section(thing, sections["ledge"], total - plate + overlap, plate - overlap, **kwargs)


def get_cap_seal_geometry(**kwargs):
    """Shared U centreline and groove in installed gutter XY coordinates."""
    import math
    from shapely.geometry import LineString

    layout = get_cap_opening_layout(**kwargs)
    groove_width = float(kwargs["seal_groove_width_mm"])
    groove_depth = float(kwargs["seal_groove_depth_mm"])
    land = float(kwargs["seal_opening_land_mm"])
    cord = float(kwargs["seal_cord_diameter_mm"])
    if min(groove_width, groove_depth, land, cord) <= 0:
        raise ValueError("Seal dimensions and opening land must be positive")
    if not 0 < 2 * groove_depth + kwargs.get("seal_face_gap_mm", 0) < cord:
        raise ValueError("Opposed grooves must compress the single cord")
    offset = land + groove_width / 2
    radius = layout["radius"] + offset
    cx = layout["width"] / 2 - layout["radius"]
    cy = layout["bottom"] + layout["radius"]
    side_x = layout["width"] / 2 + offset
    points = [(-side_x, layout["top"] + 1), (-side_x, cy)]
    points.extend((-cx + radius * math.cos(math.radians(angle)),
                   cy + radius * math.sin(math.radians(angle))) for angle in range(181, 271))
    points.append((cx, cy - radius))
    points.extend((cx + radius * math.cos(math.radians(angle)),
                   cy + radius * math.sin(math.radians(angle))) for angle in range(271, 361))
    points.append((side_x, layout["top"] + 1))
    path = LineString(points)
    return {
        "path": path,
        "groove": path.buffer(groove_width / 2, cap_style="flat", quad_segs=90),
        "side_x": side_x,
        "bottom": cy - radius,
        "cord_length_to_rim_mm": 2 * (layout["top"] - cy) + math.pi * radius + 2 * cx,
    }


def _append_cap_seal_groove(thing, z, y_offset=0, **kwargs):
    from shapely import affinity
    groove = affinity.translate(get_cap_seal_geometry(**kwargs)["groove"], yoff=y_offset)
    pos = kwargs.get("pos", [0, 0, 0])
    cutter = {
        "type": "negative",
        "shape": "polygon",
        "points": [[round(x, 7), round(y, 7)] for x, y in list(groove.exterior.coords)[:-1]],
        "height": kwargs["seal_groove_depth_mm"] + 0.01,
        "pos": [pos[0], pos[1], pos[2] + z],
    }
    oobb.append_full(thing, **cutter)


def get_cap_cover(thing, **kwargs):
    thickness = float(kwargs["cover_thickness_mm"])
    if kwargs["seal_groove_depth_mm"] >= thickness:
        raise ValueError("Cover must retain material under the seal groove")
    pos = kwargs.get("pos", [0, 0, 0])
    plate = {
        "type": "positive",
        "shape": "oobb_plate",
        "width": kwargs["cover_width_grid"],
        "height": kwargs["cover_height_grid"],
        "depth": thickness,
        "r": kwargs["cover_corner_radius_mm"],
        "holes": False,
        "pos": list(pos),
    }
    oobb.append_full(thing, **plate)
    pitch = kwargs["hole_grid_pitch_mm"]
    for x, y in [(-pitch, -pitch), (-pitch, pitch), (pitch, -pitch), (pitch, pitch), (0, 0)]:
        hole = {
            "type": "negative",
            "shape": "oobb_hole",
            "radius_name": kwargs["central_hole_size"] if (x, y) == (0, 0) else kwargs["hole_size"],
            "depth": thickness + 0.02,
            "pos": [pos[0] + x, pos[1] + y, pos[2] - 0.01],
        }
        oobb.append_full(thing, **hole)
    top = kwargs["profile_height_mm"] + kwargs["outer_lip_mm"]
    cover_centre_y = top - kwargs["hole_pattern_top_offset_mm"]
    _append_cap_seal_groove(thing, thickness - kwargs["seal_groove_depth_mm"], -cover_centre_y, **kwargs)


def get_cap_end_open(thing, **kwargs):
    get_cap_end_solide(thing, **kwargs)
    layout = get_cap_opening_layout(**kwargs)
    total = float(kwargs["total_depth_mm"])
    pos = kwargs.get("pos", [0, 0, 0])
    # Same 5 mm corner radius as a standard OOBB 1 x 3 plate. This installed
    # primitive extrudes its corner cylinders upward from the supplied Z.
    rounded_opening = {
        "type": "negative",
        "shape": "rounded_rectangle",
        "size": [layout["width"], layout["depth"], total + 0.02],
        "r": layout["radius"],
        "pos": [pos[0], pos[1] + layout["centre_y"], pos[2] - 0.01],
    }
    oobb.append_full(thing, **rounded_opening)
    # Remove the upper roundovers and continue above the edge for square,
    # fully open top corners, retaining the two bottom roundovers.
    square_mouth = {
        "type": "negative",
        "shape": "cube",
        "size": [layout["width"], layout["radius"] + 0.01, total + 0.02],
        "pos": [
            pos[0] - layout["width"] / 2,
            pos[1] + layout["top"] - layout["radius"],
            pos[2] - 0.01,
        ],
    }
    oobb.append_full(thing, **square_mouth)
    for hole in layout["holes"]:
        mounting_hole = {
            "type": "negative",
            "shape": "oobb_hole",
            "radius_name": kwargs["hole_size"],
            "depth": total + 0.02,
            "pos": [pos[0] + hole["x"], pos[1] + hole["y"], pos[2] - 0.01],
        }
        oobb.append_full(thing, **mounting_hole)
    if "seal_groove_depth_mm" in kwargs:
        if kwargs["seal_groove_depth_mm"] >= kwargs["front_plate_mm"]:
            raise ValueError("Cap must retain material under the seal groove")
        # Inside mating face is at the top of the front plate, beside the ledge.
        _append_cap_seal_groove(thing, kwargs["front_plate_mm"] - kwargs["seal_groove_depth_mm"], **kwargs)


def get_gutter_square(thing, **kwargs):
    length = float(kwargs.get("length_mm", kwargs.get("depth", 3000)))
    if length <= 0:
        raise ValueError("Gutter length must be positive")
    _append_section(thing, get_gutter_sections(**kwargs)["gutter"], length, 0, **kwargs)


def get_lifter_sections(**kwargs):
    """Bearing outline in gutter coordinates, before axial flow/fastener cuts."""
    from shapely import affinity
    from shapely.geometry import box

    lift_height = float(kwargs["lift_height_mm"])
    thickness = float(kwargs["thickness_mm"])
    support_thickness = float(kwargs["support_thickness_mm"])
    lower_shoe_height = float(kwargs["lower_shoe_height_mm"])
    upper_shoe_below_seat = float(kwargs["upper_shoe_below_seat_mm"])
    cradle_height = float(kwargs["upper_cradle_height_mm"])
    gutter_height = float(kwargs["profile_height_mm"])
    gutter_wall = float(kwargs["gutter_wall_mm"])
    gutter_width = float(kwargs["profile_width_mm"])

    if lift_height <= gutter_height:
        raise ValueError("Lift must leave the upper gutter above the lower gutter rim")
    if not 8 <= thickness <= support_thickness:
        raise ValueError("Assembled web must be at least 8 mm and no thicker than the shoes")
    if min(lower_shoe_height, upper_shoe_below_seat, cradle_height) <= 0:
        raise ValueError("Shoe heights must be positive")
    if cradle_height >= kwargs["shoulder_height_mm"]:
        raise ValueError("Upper cradle must stop below the upper gutter shoulder")

    gutter_sections = get_gutter_sections(**kwargs)
    half_width = gutter_width / 2 - gutter_wall
    contact_setback = float(kwargs.get("contact_top_setback_mm", 0.0))
    if not 0 <= contact_setback < gutter_height - kwargs["shoulder_height_mm"]:
        raise ValueError("Lifter contact setback must stop in the vertical side region")
    lower_contact = gutter_sections["cavity"]
    extension_half_width = half_width
    if contact_setback:
        if contact_setback < kwargs["lip_height_mm"]:
            raise ValueError("Lifter contact must stop below the entire lip")
        clip_clearance = float(kwargs.get("clip_side_clearance_mm", 0.5))
        if clip_clearance < 0:
            raise ValueError("Clip side clearance must be nonnegative")
        extension_half_width -= kwargs["lip_projection_mm"] + clip_clearance
        lower_contact = lower_contact.intersection(
            box(-gutter_width, 0, gutter_width, gutter_height - contact_setback)
        )
    extension = box(
        -extension_half_width,
        gutter_height - contact_setback,
        extension_half_width,
        lift_height + cradle_height,
    )
    upper_gutter_envelope = affinity.translate(
        gutter_sections["face"],
        yoff=lift_height,
    )
    web = lower_contact.union(extension)
    saddle_extra = float(kwargs.get("upper_saddle_width_extra_mm", 0.0))
    if saddle_extra < 0:
        raise ValueError("Extra saddle width must be nonnegative")
    if saddle_extra:
        # A horizontal expansion preserves the corner radius and adds exactly
        # half the requested width to each side of every seating cross-section.
        upper_gutter_envelope = affinity.translate(
            upper_gutter_envelope, xoff=-saddle_extra / 2
        ).union(
            affinity.translate(upper_gutter_envelope, xoff=saddle_extra / 2)
        )
        # Restore the outer shoe width above the lower gutter rim. The narrowed
        # neck still clears the clips, while the wider opening retains sidewalls.
        web = web.union(
            box(
                -half_width,
                lift_height - upper_shoe_below_seat,
                half_width,
                lift_height + cradle_height,
            )
        )
        top_opening = upper_gutter_envelope.intersection(
            box(-gutter_width, lift_height + cradle_height - 0.001,
                gutter_width, lift_height + cradle_height)
        )
        if top_opening.bounds[2] > half_width - 3:
            raise ValueError("Widened saddle must retain at least 3 mm sidewalls")
    web = web.difference(upper_gutter_envelope)
    lower_shoe = web.intersection(
        box(
            -gutter_width,
            0,
            gutter_width,
            gutter_wall + lower_shoe_height,
        )
    )
    upper_shoe = web.intersection(
        box(
            -gutter_width,
            lift_height - upper_shoe_below_seat,
            gutter_width,
            lift_height + cradle_height,
        )
    )
    sections = {
        "web": web,
        "lower_shoe": lower_shoe,
        "upper_shoe": upper_shoe,
    }
    for name, section in sections.items():
        if section.geom_type != "Polygon" or not section.is_valid or section.interiors:
            raise ValueError(f"Lifter {name} must be one simple connected outline")
    return sections


def get_lifter_hole_layout(**kwargs):
    """Explicit complementary fastener roles; a Y half-turn swaps X and Z."""
    from shapely.geometry import Point

    sections = get_lifter_sections(**kwargs)
    count = kwargs["flow_hole_count"]
    if not isinstance(count, int) or count < 1:
        raise ValueError("flow_hole_count must be a positive integer")
    radius = float(kwargs["flow_hole_diameter_mm"]) / 2
    pitch = float(kwargs["flow_hole_pitch_mm"])
    floor = float(kwargs["flow_hole_floor_mm"])
    if radius <= 0 or floor < 2 or (count > 1 and pitch < 2 * radius + 3):
        raise ValueError("Flow holes require positive radii and at least 2/3 mm floor/spacing")
    flow_y = kwargs["gutter_wall_mm"] + floor + radius
    flow_holes = []
    for index in range(count):
        x = (index - (count - 1) / 2) * pitch
        bore = Point(x, flow_y).buffer(radius)
        if not sections["web"].buffer(-2).covers(bore):
            raise ValueError("Flow bore is too close to the lifter outline")
        flow_holes.append(
            {
                "x": x,
                "y": flow_y,
                "radius": radius,
                    "region": "lower_shoe",
            }
        )

    for row in kwargs.get("web_flow_hole_rows", []):
        web_radius = float(row["diameter_mm"]) / 2
        if web_radius <= 0:
            raise ValueError("Web flow-hole diameter must be positive")
        for web_x in row["x_positions_mm"]:
            web_y = float(row["height_mm"])
            bore = Point(web_x, web_y).buffer(web_radius)
            if not sections["web"].buffer(-3).covers(bore):
                raise ValueError("Web flow hole needs at least 3 mm to the outer edge")
            if bore.intersects(sections["lower_shoe"]) or bore.intersects(sections["upper_shoe"]):
                raise ValueError("Web flow holes must remain between the bearing shoes")
            for previous in flow_holes:
                other = Point(previous["x"], previous["y"]).buffer(previous["radius"])
                if bore.distance(other) < 3:
                    raise ValueError("Flow holes need at least 3 mm of material between them")
            flow_holes.append(
                {
                    "x": float(web_x),
                    "y": web_y,
                    "radius": web_radius,
                    "region": "web",
                }
            )
    for hole in flow_holes:
        if not any(other["x"] == -hole["x"] and other["y"] == hole["y"]
                   and other["radius"] == hole["radius"] for other in flow_holes):
            raise ValueError("Flow pattern must align after turning the identical second half")

    x = float(kwargs["fastener_x_mm"])
    rows = [
        float(kwargs["fastener_lower_height_mm"]),
        float(kwargs["lift_height_mm"] - kwargs["fastener_upper_seat_offset_mm"]),
    ]
    if x < 6 or rows[1] - rows[0] < 12:
        raise ValueError("Fastener columns/rows need at least 12 mm centre spacing")
    fasteners = []
    for y in rows:
        for side in (-1, 1):
            head_region = Point(side * x, y).buffer(6)
            if not sections["web"].covers(head_region):
                raise ValueError("Fastener needs at least 6 mm to the web edge")
            if head_region.intersects(sections["lower_shoe"]) or head_region.intersects(sections["upper_shoe"]):
                raise ValueError("Fasteners need clear external access between the shoes")
            for flow_hole in flow_holes:
                bore = Point(flow_hole["x"], flow_hole["y"]).buffer(flow_hole["radius"])
                if head_region.intersects(bore):
                    raise ValueError("Fastener conflicts with a flow hole")
            fasteners.append(
                {
                    "x": side * x,
                    "y": y,
                    "role": "countersink" if side < 0 else "nut",
                }
            )
    return {
        "flow_holes": flow_holes,
        "fasteners": fasteners,
    }


def get_lifter(thing, **kwargs):
    """One flat-printable half; assemble two identical copies, face to face."""
    sections = get_lifter_sections(**kwargs)
    layout = get_lifter_hole_layout(**kwargs)
    half_web = float(kwargs["thickness_mm"]) / 2
    half_support = float(kwargs["support_thickness_mm"]) / 2
    pos = copy.deepcopy(kwargs.get("pos", [0, 0, 0]))

    # All solids start on the joining/bed plane. No unsupported flange overhang.
    if kwargs.get("fit_revision", 1) >= 2:
        # One extrusion, relieved between the shoes, avoids coincident polygon
        # unions and preserves a closed mesh at the profile's sloping edges.
        _append_section(thing, sections["web"], half_support, 0, **kwargs)
        lower_top = kwargs["gutter_wall_mm"] + kwargs["lower_shoe_height_mm"]
        upper_bottom = kwargs["lift_height_mm"] - kwargs["upper_shoe_below_seat_mm"]
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "negative"
        p3["shape"] = "cube"
        p3["size"] = [
            kwargs["profile_width_mm"] * 2,
            upper_bottom - lower_top,
            half_support - half_web + 0.01,
        ]
        p3["pos"] = [
            pos[0] - kwargs["profile_width_mm"],
            pos[1] + lower_top,
            pos[2] + half_web,
        ]
        oobb.append_full(thing, **p3)
    else:
        _append_section(thing, sections["web"], half_web, 0, **kwargs)
        _append_section(thing, sections["lower_shoe"], half_support, 0, **kwargs)
        _append_section(thing, sections["upper_shoe"], half_support, 0, **kwargs)

    for flow_hole in layout["flow_holes"]:
        p3 = copy.deepcopy(kwargs)
        p3["type"] = "negative"
        p3["shape"] = "oobb_hole"
        p3["radius_name"] = ""
        p3["radius"] = flow_hole["radius"]
        p3["depth"] = half_support + 0.02
        p3["pos"] = [
            pos[0] + flow_hole["x"],
            pos[1] + flow_hole["y"],
            pos[2] - 0.01,
        ]
        oobb.append_full(thing, **p3)

    for fastener in layout["fasteners"]:
        if fastener["role"] == "countersink":
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "negative"
            p3["shape"] = "oobb_screw_countersunk"
            p3["mode"] = kwargs.get("modes", ["3dpr"])
            p3["radius_name"] = "m3"
            p3["depth"] = half_web + 0.01
            p3["zz"] = "top"
            p3["hole"] = True
            p3["nut_include"] = False
            p3["overhang"] = False
            p3["clearance"] = ""
            p3["pos"] = [
                pos[0] + fastener["x"],
                pos[1] + fastener["y"],
                pos[2] + half_web,
            ]
            oobb.append_full(thing, **p3)
        else:
            # Explicit OOBB through-bore, then a separate upward-opening nut pocket.
            p3 = copy.deepcopy(kwargs)
            p3["type"] = "negative"
            p3["shape"] = "oobb_hole"
            p3["radius_name"] = "m3"
            p3["depth"] = half_web + 0.02
            p3["pos"] = [
                pos[0] + fastener["x"],
                pos[1] + fastener["y"],
                pos[2] - 0.01,
            ]
            oobb.append_full(thing, **p3)

            for mode in kwargs.get("modes", ["3dpr"]):
                p3 = copy.deepcopy(kwargs)
                p3["type"] = "negative"
                p3["shape"] = "oobb_nut"
                p3["radius_name"] = "m3"
                # Resolve each mode independently: the legacy primitive otherwise
                # reuses its first mode's depth when given an empty depth.
                p3["mode"] = mode
                p3["depth"] = oobb.gv("nut_depth_m3", mode)
                p3["zz"] = "top"
                p3["hole"] = False
                p3["overhang"] = False
                p3["clearance"] = ""
                p3["pos"] = [
                    pos[0] + fastener["x"],
                    pos[1] + fastener["y"],
                    pos[2] + half_web,
                ]
                oobb.append_full(thing, **p3)


if __name__ == '__main__':
    main()
