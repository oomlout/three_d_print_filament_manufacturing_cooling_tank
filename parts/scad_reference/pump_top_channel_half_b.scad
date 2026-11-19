module pump_top_channel_half_b() { scale([-1,1,1]) union() {
        translate([-9.0,-1,22.0]) rotate([-90,0,0]) cylinder(h=13.709999999999999,r=8.2,$fn=64);
        translate([-9.0,12.7,22.0]) rotate([-90,0,0]) cylinder(h=6.01,r1=8.2,r2=7.2,$fn=64);
        translate([31.0,18.7,22.0]) rotate([0,0,90]) rotate_extrude(angle=90,$fn=180) translate([40.0,0,0]) circle(r=7.2,$fn=64);
        translate([30.99,58.7,22.0]) rotate([0,90,0]) cylinder(h=4.02,r=7.2,$fn=64);
        translate([35.0,58.7,22.0]) rotate([0,90,0]) cylinder(h=2.0,r1=7.2,r2=6.8,$fn=64);
        translate([37.0,58.7,22.0]) rotate([0,90,0]) cylinder(h=5.0,r=6.8,$fn=64);
    } }