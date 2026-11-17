// Source axes: Y upright, Z along the gutter. Set gap=0 to assemble.
gap=12;
module a() { import("pump_lifter_assets/half_a.stl"); }
module b() { import("pump_lifter_assets/half_b.stl"); }
module tube() {
        translate([-80,66.75,15.0]) rotate([0,90,0]) cylinder(h=40.0,r=7,$fn=64);
        translate([-40.0,26.75,15.0]) rotate_extrude(angle=90,$fn=180) translate([40.0,0,0]) circle(r=7,$fn=64);
        translate([0,17.25,15.0]) rotate([-90,0,0]) cylinder(h=9.5,r=7,$fn=64);
    }
    
color([0.20,0.53,0.59]) translate([0,0,-gap]) a();
color([0.85,0.57,0.26]) translate([0,0,30.0+gap]) rotate([0,180,0]) b();
// OD envelope only; actual tube has 12 mm ID and 1 mm wall.
color([0.9,0.65,0.55,0.65]) tube();
