"""Lifter bearing contact, identical-half joint and variant constraints."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shapely import affinity
from shapely.geometry import Point
import working_oomp_populate as populate
import working_scad as cad


class LifterTests(unittest.TestCase):
    def setUp(self):
        self.option = next(o for o in populate.get_options() if o['oobb_type'] == 'lifter')

    def test_two_identical_halves_swap_head_and_nut_roles(self):
        holes = cad.get_lifter_hole_layout(**self.option)['fasteners']
        self.assertEqual(len(holes), 4)
        for hole in holes:
            mate = next(h for h in holes if h['x'] == -hole['x'] and h['y'] == hole['y'])
            self.assertNotEqual(hole['role'], mate['role'])
        for section in cad.get_lifter_sections(**self.option).values():
            mirror = affinity.scale(section, xfact=-1, origin=(0, 0))
            self.assertLess(section.symmetric_difference(mirror).area, 1e-7)

    def test_no_gutter_interference_and_correct_seat_height(self):
        sections = cad.get_lifter_sections(**self.option)
        gutter = cad.get_gutter_sections(**self.option)['gutter']
        upper = affinity.translate(gutter, yoff=75)
        self.assertLess(sections['web'].intersection(gutter).area, 1e-7)
        self.assertLess(sections['web'].intersection(upper).area, 1e-7)
        self.assertGreater(sections['lower_shoe'].boundary.intersection(gutter.boundary).length, 65)
        self.assertGreater(sections['upper_shoe'].boundary.intersection(upper.boundary).length, 65)
        self.assertTrue(sections['upper_shoe'].covers(Point(0, 75)))
        self.assertFalse(sections['upper_shoe'].covers(Point(0, 75.01)))
        self.assertTrue(sections['lower_shoe'].covers(Point(0, 2.25)))

    def test_flow_ports_have_material_around_them(self):
        sections = cad.get_lifter_sections(**self.option)
        layout = cad.get_lifter_hole_layout(**self.option)
        self.assertEqual(len(layout['flow_holes']), 9)
        for hole in layout['flow_holes']:
            bore = Point(hole['x'], hole['y']).buffer(hole['radius'])
            if hole['region'] == 'lower_shoe':
                self.assertTrue(sections['lower_shoe'].buffer(-2.9).covers(bore))
            else:
                self.assertTrue(sections['web'].buffer(-3).covers(bore))
                self.assertFalse(bore.intersects(sections['lower_shoe']))
                self.assertFalse(bore.intersects(sections['upper_shoe']))
            mate = next(h for h in layout['flow_holes'] if h['x'] == -hole['x'] and h['y'] == hole['y'])
            self.assertEqual(mate['radius'], hole['radius'])

    def test_top_side_contact_is_relieved_before_clip(self):
        from shapely.geometry import LineString
        web = cad.get_lifter_sections(**self.option)['web']
        self.assertTrue(web.covers(Point(54.7, 50.99)))
        for y in (51.01, 53.5, 54.5, 58.5, 60):
            width = LineString([(-60, y), (60, y)]).intersection(web).length
            self.assertAlmostEqual(width, 104.5)

    def test_oobb_fasteners_are_explicit_and_open_on_outer_face(self):
        requests = []
        with patch.object(cad.oobb, 'append_full', side_effect=lambda thing, **kw: requests.append(kw)):
            cad.get_lifter({'components': []}, **self.option)
        screws = [r for r in requests if r['shape'] == 'oobb_screw_countersunk']
        nuts = [r for r in requests if r['shape'] == 'oobb_nut']
        self.assertEqual(len(screws), 2)
        self.assertEqual(len(nuts), 2)
        for request in screws + nuts:
            self.assertEqual(request['radius_name'], 'm3')
            self.assertTrue(request['overhang'])
            self.assertEqual(request['clearance'], 'top')
        for request in screws:
            self.assertEqual(request['pos'][2], 4.5)
            self.assertEqual(request['zz'], 'top')
        for request in nuts:
            self.assertEqual(request['pos'][2] + request['depth'], 4.5)
            self.assertEqual(request['zz'], 'bottom')
        solids = [r for r in requests if r['type'] == 'positive']
        self.assertEqual([r['height'] for r in solids], [15])
        relief = next(r for r in requests if r['shape'] == 'cube')
        self.assertEqual(relief['pos'][2], 4.5)

    def test_upper_opening_has_three_mm_allowance_without_widening_lower_foot(self):
        from shapely.geometry import LineString
        wide = cad.get_lifter_sections(**self.option)
        original_params = dict(self.option)
        original_params['upper_saddle_width_extra_mm'] = 0
        narrow = cad.get_lifter_sections(**original_params)
        self.assertLess(wide['lower_shoe'].symmetric_difference(narrow['lower_shoe']).area, 1e-8)
        for y in (75.001, 80, 90):
            line = LineString([(-54.75, y), (54.75, y)])
            # The old relieved shoe is narrower externally; compare actual inner endpoints.
            wide_parts = list(line.intersection(wide['upper_shoe']).geoms)
            narrow_parts = list(line.intersection(narrow['upper_shoe']).geoms)
            wide_gap = wide_parts[1].bounds[0] - wide_parts[0].bounds[2]
            narrow_gap = narrow_parts[1].bounds[0] - narrow_parts[0].bounds[2]
            self.assertAlmostEqual(wide_gap - narrow_gap, 3, places=6)

    def test_saddle_is_five_mm_narrower_at_bottom_middle_and_top(self):
        from shapely.geometry import LineString
        current = cad.get_lifter_sections(**self.option)
        previous_params = dict(self.option)
        previous_params['upper_saddle_width_extra_mm'] = 8
        previous = cad.get_lifter_sections(**previous_params)
        self.assertTrue(current['lower_shoe'].equals(previous['lower_shoe']))
        for y in (75.0001, 80, 90, 93):
            line = LineString([(-54.75, y), (54.75, y)])
            old_width = line.difference(previous['upper_shoe']).length
            new_width = line.difference(current['upper_shoe']).length
            self.assertAlmostEqual(old_width - new_width, 5, places=6)

    def test_declared_variant_changes_taxonomy_and_geometry(self):
        variant = {
            'lift_height_mm': 90.0,
            'thickness_mm': 12.0,
            'support_thickness_mm': 40.0,
        }
        with patch.object(populate, 'LIFTER_VARIANTS', [variant]):
            option = next(o for o in populate.get_options() if o['oobb_type'] == 'lifter')
        identity = populate.build_oomp_id(option)
        self.assertIn('90_mm_lift_height_12_mm_thickness_40_mm_support_thickness', identity)
        self.assertEqual(option['depth_mm'], 20)
        self.assertEqual(cad.get_lifter_sections(**option)['web'].bounds[3], 108)
        self.assertEqual(cad.get_lifter_hole_layout(**option)['fasteners'][-1]['y'], 71)

    def test_bad_sizes_fail_before_export(self):
        for change in (
            {'lift_height_mm': 50},
            {'thickness_mm': 5},
            {'support_thickness_mm': 8},
            {'flow_hole_diameter_mm': 30},
            {'web_flow_hole_rows': [{'height_mm': 33, 'diameter_mm': 12, 'x_positions_mm': [-24, 24]}]},
        ):
            option = copy.deepcopy(self.option)
            option.update(change)
            with self.assertRaises(ValueError):
                cad.get_lifter_hole_layout(**option)


if __name__ == '__main__':
    unittest.main()
