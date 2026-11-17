module pump_tube_channel_half_b() {
        scale([-1,1,1]) union() {
            translate([-70,66.75,15.0]) rotate([0,90,0]) cylinder(h=30.01,r=7.2,$fn=64);
            translate([-40.0,26.75,15.0]) rotate_extrude(angle=90,$fn=180) translate([40.0,0,0]) circle(r=7.2,$fn=64);
            translate([0,17.24,15.0]) rotate([-90,0,0]) cylinder(h=4.01,r=6.8,$fn=64);
            translate([0,21.25,15.0]) rotate([-90,0,0]) cylinder(h=2.0,r1=6.8,r2=7.2,$fn=64);
            translate([0,23.25,15.0]) rotate([-90,0,0]) cylinder(h=3.51,r=7.2,$fn=64);
        }
    }