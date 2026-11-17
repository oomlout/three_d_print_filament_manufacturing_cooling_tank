module half() { include <3dpr.scad>; }
module gutter_cutaway() {
  intersection() {
    translate([0,0,-300]) { include <gutter_reference.scad>; }
    translate([-100,-1,-60]) cube([200,160,60]);
  }
}
rotate([90,0,0]) {
  color([0.20,0.53,0.59]) half();
  color([0.85,0.57,0.26]) rotate([0,180,0]) half();
  color([0.74,0.77,0.79]) gutter_cutaway();
  color([0.74,0.77,0.79]) translate([0,75.0,0]) gutter_cutaway();
}
