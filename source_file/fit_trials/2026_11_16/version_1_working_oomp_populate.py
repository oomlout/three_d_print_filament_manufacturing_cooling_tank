"""Persistent cooling-tank catalogue; regenerate with action_make_scad.py."""
import copy

from oomp_populate_helper import build_oomp_id, write_extras


PROFILE = {
    "profile_width_mm": 114.0,
    "profile_height_mm": 58.5,
    "gutter_wall_mm": 2.25,
    # Undimensioned features reconstructed from the supplied section drawing.
    # Update these after measuring a physical cut end; they are not factory CAD.
    "shoulder_height_mm": 37.5,
    "bottom_virtual_width_mm": 75.0,
    "bottom_radius_mm": 7.0,
    "shoulder_radius_mm": 3.0,
    "lip_projection_mm": 2.0,
    "lip_height_mm": 5.0,
    "lip_tip_drop_mm": 4.0,
    "curve_step_degrees": 1.0,
}

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
        option["taxonomy_8"] = "version_1"
        option["lift_height_mm"] = lift_height
        option["thickness_mm"] = thickness
        option["support_thickness_mm"] = support_thickness
        option["lift_height_datum"] = "outside_bottom_to_outside_bottom"
        option["lower_shoe_height_mm"] = 18.0
        option["upper_shoe_below_seat_mm"] = 9.0
        option["upper_cradle_height_mm"] = 18.0
        option["flow_hole_diameter_mm"] = 12.0
        option["flow_hole_pitch_mm"] = 24.0
        option["flow_hole_count"] = 3
        option["flow_hole_floor_mm"] = 3.0
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
            "For installation, slide it along from an open end to that position before capping."
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
            "taxonomy_6": "version_1",
            "depth": depth,
            "total_depth_mm": depth,
            "front_plate_mm": 3.0,
            "ledge_wall_mm": 3.0,
            "insertion_depth_mm": depth - 3.0,
            "fit_clearance_mm": 0.0,
            "part_role": "printed_solid_end_cap",
            "description": f"Solid blank cap, {depth} mm total depth; 3 mm face and {depth - 3} mm insertion, 3 mm U-shaped ledge.",
            "print_orientation": "Flat exterior face on bed at Z=0; ledge upward; no supports required by geometry.",
        })

    for length in (3000, 1000, 500, 300):
        options.append({
            "oobb_type": "gutter_square",
            "taxonomy_4": "gutter_square",
            "taxonomy_5": "114_mm_width",
            "taxonomy_6": f"{length}_mm_length",
            "taxonomy_7": "version_1",
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
            "profile_status": "dimensioned_envelope_with_estimated_radii_shoulders_and_lips",
            "profile_image_url": PROFILE_IMAGE_URL,
            "profile_image_local": "source_file/floplast/square_gutter_profile.jpg",
            "product_reference_url": PRODUCT_URL,
            "dimension_basis": "114 x 58.5 mm external from drawing; 2.25 mm material thickness supplied by user.",
            "fit_note": "Nominal model fit only. Measure actual radii/lips and trial-fit before sealing; drawing does not establish a perfect physical match.",
        })
        option["oobb_details"] = copy.deepcopy(option)
    return options


def main(**kwargs):
    extras = get_options()
    import working_oomp_populate_extra_detail
    working_oomp_populate_extra_detail.main(extras=extras)
    write_extras(extras)


if __name__ == "__main__":
    main()
