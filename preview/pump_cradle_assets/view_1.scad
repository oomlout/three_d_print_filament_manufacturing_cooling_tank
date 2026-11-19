multmatrix([[0,0,1,0],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) {
color([0.02,0.55,0.62]) {
            import("pump_cradle_front.stl"); import("pump_cradle_rear.stl");
        }
        color([0.12,0.12,0.12]) import("pump_holder_base.stl");
        color([0.2,0.2,0.2,0.16]) intersection() {
            translate([0,0,-250]) import("lower_gutter.stl");
            translate([-100,-1,239]) cube([200,70,92]);
        }
}