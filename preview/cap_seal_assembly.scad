// Cover is inside the cap; mating faces meet at Z=3 around one 2 mm cord.
color([0.20,0.53,0.59]) { include <../parts/three_d_print_filament_manufacture_cooling_tank_cap_end_open_15_mm_depth_version_6/3dpr.scad>; }
translate([0,42.5,6.0]) rotate([0,180,0]) color([0.82,0.66,0.35]) { include <../parts/three_d_print_filament_manufacture_cooling_tank_cap_cover_3_by_3_oobb_3_mm_thickness_version_1/3dpr.scad>; }
