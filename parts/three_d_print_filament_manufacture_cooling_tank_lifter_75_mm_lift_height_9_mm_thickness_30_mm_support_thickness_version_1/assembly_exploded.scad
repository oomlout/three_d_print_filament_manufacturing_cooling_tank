module half() { include <3dpr.scad>; }
color([0.20,0.53,0.59]) translate([0,0,10]) half();
color([0.85,0.57,0.26]) translate([0,0,-10]) rotate([0,180,0]) half();
