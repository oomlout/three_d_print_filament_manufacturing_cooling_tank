// Both 300 mm gutters continue 150 mm each way past the support.
module half() { include <3dpr.scad>; }
module gutter_span() {
  translate([0,0,-150]) { include <gutter_reference.scad>; }
}
rotate([90,0,0]) {
  color([0.20,0.53,0.59]) half();
  color([0.85,0.57,0.26]) rotate([0,180,0]) half();
  color([0.74,0.77,0.79,0.35]) gutter_span();
  color([0.74,0.77,0.79,0.35]) translate([0,75.0,0]) gutter_span();
}
