"""Persistent cooling-tank catalogue; regenerate with action_make_scad.py."""
import copy

from oomp_populate_helper import build_oomp_id, write_extras


FIT_REVISION = {
    "inside_bottom_diameter_mm": 10.0,
    "wall_top_setback_mm": 7.5,
    "lifter_clip_side_clearance_mm": 0.5,
}


CAP_FIT = {
    "inside_bottom_radius_mm": 5.5,
    "wall_top_setback_mm": 9.5,
    "outer_lip_mm": 6.0,
}


CAP_OPENING = {
    "width_mm": 14.0,
    "depth_mm": 38.0,
    "bottom_corner_radius_mm": 5.0,
    "hole_pattern_top_offset_mm": 22.0,
    "hole_grid_pitch_mm": 15.0,
    "hole_size": "m6",
}


CAP_SEAL = {
    "seal_cord_diameter_mm": 2.0,
    "seal_groove_width_mm": 2.4,
    "seal_groove_depth_mm": 0.8,
    "seal_opening_land_mm": 1.175,
    "seal_style": "matching_open_top_u_grooves_single_cord",
    "seal_face_gap_mm": 0.0,
}


CAP_COVER = {
    "width_grid": 3,
    "height_grid": 3,
    "thickness_mm": 3.0,
    "corner_radius_mm": 5.0,
}


PROFILE = {
    "profile_width_mm": 114.0,
    "profile_height_mm": 58.5,
    "gutter_wall_mm": 2.25,
    # Undimensioned features reconstructed from the supplied section drawing.
    # Update these after measuring a physical cut end; they are not factory CAD.
    "shoulder_height_mm": 37.5,
    "bottom_virtual_width_mm": 75.0,
    "shoulder_radius_mm": 3.0,
    "lip_projection_mm": 2.0,
    "lip_height_mm": 5.0,
    "lip_tip_drop_mm": 4.0,
    "curve_step_degrees": 1.0,
}
PROFILE["bottom_radius_mm"] = (
    FIT_REVISION["inside_bottom_diameter_mm"] / 2
    + PROFILE["gutter_wall_mm"]
)

PROFILE_IMAGE_URL = "https://www.floplast.co.uk/uploads/product-images/thumbs/TzthwyEyd4jlruupRya4q3cotOfUAovxlqG51iY3.jpg"
PRODUCT_URL = "https://www.screwfix.com/p/floplast-rgs3w-upvc-square-gutter-white-114mm-x-3m/28154"


# Add another dictionary here to generate another lifter size. These are the
# ASSEMBLED dimensions: a printed half has half the web/support thickness.
LIFTER_VARIANTS = [
    {
        "lift_height_mm": 75.0,
        "thickness_mm": 9.0,
        "support_thickness_mm": 30.0,
    },
]


def get_lifter_options():
    options = []
    for variant in LIFTER_VARIANTS:
        lift_height = variant["lift_height_mm"]
        thickness = variant["thickness_mm"]
        support_thickness = variant["support_thickness_mm"]

        option = {}
        option["oobb_type"] = "lifter"
        option["taxonomy_4"] = "lifter"
        option["taxonomy_5"] = f"{lift_height:g}_mm_lift_height"
        option["taxonomy_6"] = f"{thickness:g}_mm_thickness"
        option["taxonomy_7"] = f"{support_thickness:g}_mm_support_thickness"
        option["contact_top_setback_mm"] = FIT_REVISION["wall_top_setback_mm"]
        option["clip_side_clearance_mm"] = FIT_REVISION["lifter_clip_side_clearance_mm"]
        option["lift_height_mm"] = lift_height
        option["thickness_mm"] = thickness
        option["support_thickness_mm"] = support_thickness
        option["lift_height_datum"] = "outside_bottom_to_outside_bottom"
        option["lower_shoe_height_mm"] = 18.0
        option["upper_shoe_below_seat_mm"] = 9.0
        option["upper_cradle_height_mm"] = 18.0
        option["upper_saddle_width_extra_mm"] = 3.0
        option["flow_hole_diameter_mm"] = 12.0
        option["flow_hole_pitch_mm"] = 24.0
        option["flow_hole_count"] = 3
        option["flow_hole_floor_mm"] = 3.0
        option["web_flow_hole_rows"] = [
            {
                "height_mm": 32.0,
                "diameter_mm": 12.0,
                "x_positions_mm": [-40.0, 0.0, 40.0],
            },
            {
                "height_mm": 50.0,
                "diameter_mm": 12.0,
                "x_positions_mm": [-40.0, 0.0, 40.0],
            },
        ]
        option["fastener_x_mm"] = 24.0
        option["fastener_lower_height_mm"] = 33.0
        option["fastener_upper_seat_offset_mm"] = 19.0
        option["fastener_size"] = "m3"
        option["fastener_count"] = 4
        option["print_quantity"] = 2
        option["depth"] = support_thickness / 2
        option["depth_mm"] = support_thickness / 2
        option["width"] = PROFILE["profile_width_mm"] - 2 * PROFILE["gutter_wall_mm"]
        option["width_mm"] = option["width"]
        option["height"] = lift_height + option["upper_cradle_height_mm"] - PROFILE["gutter_wall_mm"]
        option["height_mm"] = option["height"]
        option["part_role"] = "printed_identical_lifter_half"
        option["placement"] = "mid_span_with_both_gutters_continuing_past_support"
        option["description"] = (
            f"Mid-span lifter half, print two; {lift_height:g} mm bottom-to-bottom lift, "
            f"{thickness:g} mm assembled web, {support_thickness:g} mm assembled shoes."
        )
        option["print_orientation"] = (
            "Flat joining face on bed at Z=0; countersinks and nut pockets face upward."
        )
        option["assembly_instruction"] = (
            "Rotate the second identical print 180 degrees about its upright Y axis; "
            "join the flat faces at Z=0. Four M3 screws alternate direction across X. "
            "Position the assembled lifter in the middle of the lower gutter span, "
            "with both gutters extending past it in both directions. It is not an end closure. "
            "Side contact ends 7.5 mm below the rim; straight relieved sides clear the clips."
        )
        options.append(option)
    return options


def get_options():
    options = []
    for depth in (15, 6):
        options.append({
            "oobb_type": "cap_end_solide",
            "taxonomy_4": "cap_end_solide",
            "taxonomy_5": f"{depth}_mm_depth",
            "depth": depth,
            "total_depth_mm": depth,
            "front_plate_mm": 3.0,
            "outer_lip_mm": CAP_FIT["outer_lip_mm"],
            "width": PROFILE["profile_width_mm"] + 2 * CAP_FIT["outer_lip_mm"],
            "height": PROFILE["profile_height_mm"] + 2 * CAP_FIT["outer_lip_mm"],
            "width_mm": PROFILE["profile_width_mm"] + 2 * CAP_FIT["outer_lip_mm"],
            "height_mm": PROFILE["profile_height_mm"] + 2 * CAP_FIT["outer_lip_mm"],
            "ledge_wall_mm": 3.0,
            "insertion_depth_mm": depth - 3.0,
            "fit_clearance_mm": 0.0,
            "ledge_top_setback_mm": CAP_FIT["wall_top_setback_mm"],
            "ledge_ignore_clip": True,
            "part_role": "printed_solid_end_cap",
            "description": f"Solid blank cap, {depth} mm total depth; 3 mm face and {depth - 3} mm insertion, 3 mm U-shaped ledge.",
            "print_orientation": "Flat exterior face on bed at Z=0; ledge upward; no supports required by geometry.",
        })

    for solid_cap in list(options):
        option = copy.deepcopy(solid_cap)
        option["oobb_type"] = "cap_end_open"
        option["taxonomy_4"] = "cap_end_open"
        option["opening_width_mm"] = CAP_OPENING["width_mm"]
        option["opening_depth_mm"] = CAP_OPENING["depth_mm"]
        option["opening_bottom_corner_radius_mm"] = CAP_OPENING["bottom_corner_radius_mm"]
        option["opening_depth_datum"] = "enlarged_front_plate_top_edge"
        option["hole_grid_pitch_mm"] = CAP_OPENING["hole_grid_pitch_mm"]
        option["hole_pattern_top_offset_mm"] = CAP_OPENING["hole_pattern_top_offset_mm"]
        option["hole_size"] = CAP_OPENING["hole_size"]
        option["hole_pattern"] = "3_by_3_oobb_corner_holes_22_mm_below_front_plate_top"
        option.update(copy.deepcopy(CAP_SEAL))
        option["part_role"] = "printed_open_end_cap"
        option["description"] = (
            f"Open cap, {option['total_depth_mm']} mm total depth; 6 mm outer lip, "
            f"14 x {option['opening_depth_mm']:g} mm top opening, 5 mm bottom corner radius and four M6 holes "
            "at 3 x 3 OOBB corner positions on the 15 mm grid; inside U seal groove for 2 mm cord."
        )
        options.append(option)

    cover = copy.deepcopy(next(o for o in options if o["oobb_type"] == "cap_end_open"))
    cover["oobb_type"] = "cap_cover"
    cover["taxonomy_4"] = "cap_cover"
    cover["taxonomy_5"] = "3_by_3_oobb"
    cover["taxonomy_6"] = f"{CAP_COVER['thickness_mm']:g}_mm_thickness"
    cover["cover_width_grid"] = CAP_COVER["width_grid"]
    cover["cover_height_grid"] = CAP_COVER["height_grid"]
    cover["cover_corner_radius_mm"] = CAP_COVER["corner_radius_mm"]
    cover["cover_thickness_mm"] = CAP_COVER["thickness_mm"]
    cover["depth"] = CAP_COVER["thickness_mm"]
    cover["width"] = CAP_COVER["width_grid"] * 15 - 1
    cover["height"] = CAP_COVER["height_grid"] * 15 - 1
    cover["width_mm"] = cover["width"]
    cover["height_mm"] = cover["height"]
    cover["central_hole_size"] = "m6"
    cover["part_role"] = "printed_grooved_cap_cover"
    cover["description"] = "44 x 44 x 3 mm cover, R5 outline corners, straight sides; four corner M6 holes and one central M6 hole; matching U seal groove."
    cover["print_orientation"] = "Flat ungrooved face at Z=0; U groove facing upward."
    cover["assembly_instruction"] = "Place one 2 mm rubber cord in the matching U grooves, with both ends exiting the top. Install the cover inside the cap with its groove facing the cap inside face; bring the flat mating faces together. Central M6 hole is an open port."
    for cap_only_key in ("total_depth_mm", "front_plate_mm", "ledge_wall_mm", "insertion_depth_mm", "fit_clearance_mm", "ledge_top_setback_mm", "ledge_ignore_clip"):
        cover.pop(cap_only_key, None)
    options.append(cover)

    for length in (3000, 1000, 500, 300):
        options.append({
            "oobb_type": "gutter_square",
            "taxonomy_4": "gutter_square",
            "taxonomy_5": "114_mm_width",
            "taxonomy_6": f"{length}_mm_length",
            "depth": length,
            "length_mm": length,
            "part_role": "purchased_gutter_reference",
            "material": "upvc",
            "colour": "white",
            "manufacturer": "floplast",
            "reference_product": "RGS3W",
            "description": f"FloPlast 114 x 58.5 mm square gutter, {length} mm length; reference geometry, not a print instruction.",
        })

    options.extend(get_lifter_options())

    for option in options:
        option.update(copy.deepcopy(PROFILE))
        option["inside_bottom_diameter_mm"] = FIT_REVISION["inside_bottom_diameter_mm"]
        option["fit_revision"] = 2
        option["fit_photo_local"] = "source_file/fit_trials/2026_11_16/printed_fit.jpg"
        if option["oobb_type"] == "lifter":
            option["fit_photo_local"] = "source_file/fit_trials/2026_11_16/printed_lifter_fit.jpg"
        option.setdefault("width", 114.0)
        option.setdefault("height", 58.5)
        option.setdefault("width_mm", 114.0)
        option.setdefault("height_mm", 58.5)
        option.update({
            "taxonomy_1": "three_d_print",
            "taxonomy_2": "filament_manufacture",
            "taxonomy_3": "cooling_tank",
            "oobb_name": option["oobb_type"],
            "depth_mm": option["depth"],
            "run_scad": True,
            "run_solidcraft": False,
            "profile_status": "revision_2_user_selected_10_mm_inside_bottom_diameter_other_undimensioned_features_estimated",
            "profile_image_url": PROFILE_IMAGE_URL,
            "profile_image_local": "source_file/floplast/square_gutter_profile.jpg",
            "product_reference_url": PRODUCT_URL,
            "dimension_basis": "114 x 58.5 mm external from drawing; 2.25 mm material thickness supplied by user.",
            "fit_note": "Nominal model fit only. Measure actual radii/lips and trial-fit before sealing; drawing does not establish a perfect physical match.",
        })
        if option["oobb_type"].startswith("cap_end_"):
            option["bottom_radius_mm"] = CAP_FIT["inside_bottom_radius_mm"] + option["gutter_wall_mm"]
            option["inside_bottom_diameter_mm"] = CAP_FIT["inside_bottom_radius_mm"] * 2
            option["fit_revision"] = 3
            option["profile_status"] = "cap_trial_5_5_mm_inside_bottom_radius_flat_wall_ends_9_5_mm_below_rim"
        option["oobb_details"] = copy.deepcopy(option)
    return options


def main(**kwargs):
    extras = get_options()
    import working_oomp_populate_extra_detail
    working_oomp_populate_extra_detail.main(extras=extras)
    write_extras(extras)


if __name__ == "__main__":
    main()
