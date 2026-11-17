"""Physical geometry constraints for the cooling-tank profile and catalogue."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shapely import affinity
from shapely.geometry import LineString, Point
from working_oomp_populate import get_options, build_oomp_id, LIFTER_VARIANTS, PROFILE
from working_scad import get_gutter_sections, get_cap_sections, get_cap_opening_layout, get_cap_end_open


class CoolingTankTests(unittest.TestCase):
    def setUp(self):
        self.cap = get_options()[0]
        self.s = get_gutter_sections(**self.cap)

    def test_catalogue_dimensions_and_identity(self):
        options = get_options()
        expected_count = 11 + len(LIFTER_VARIANTS)
        self.assertEqual(len(options), expected_count)
        self.assertEqual(len({build_oomp_id(o) for o in options}), expected_count)
        caps = [o for o in options if o['oobb_type'] == 'cap_end_solide']
        self.assertEqual({o['total_depth_mm'] for o in caps}, {6, 15})
        self.assertEqual({o['insertion_depth_mm'] for o in caps}, {3, 12})
        for cap in caps:
            self.assertEqual(cap['total_depth_mm'], cap['front_plate_mm'] + cap['insertion_depth_mm'])
            self.assertEqual(cap['front_plate_mm'], 3)
            self.assertEqual(cap['ledge_wall_mm'], 3)
        self.assertEqual({o['length_mm'] for o in options if 'length_mm' in o}, {300, 500, 1000, 3000})
        for option in options:
            self.assertEqual(option['taxonomy_1'], 'three_d_print')
            self.assertEqual(option['taxonomy_2'], 'filament_manufacture')
            self.assertEqual(option['taxonomy_3'], 'cooling_tank')
            self.assertEqual(option['oobb_details']['gutter_wall_mm'], 2.25)

    def test_envelope_and_symmetry(self):
        for actual, expected in zip(self.s['face'].bounds, (-57, 0, 57, 58.5)):
            self.assertAlmostEqual(actual, expected, places=9)
        for section in self.s.values():
            mirrored = affinity.scale(section, xfact=-1, origin=(0, 0))
            self.assertLess(section.symmetric_difference(mirrored).area, 1e-8)

    def test_mating_ledge_fits_without_overlap(self):
        self.assertLess(self.s['ledge'].intersection(self.s['gutter']).area, 1e-8)
        self.assertLess(self.s['ledge'].difference(self.s['cavity']).area, 1e-8)
        self.assertGreater(self.s['ledge'].boundary.intersection(self.s['gutter'].boundary).length, 170)

    def test_normal_wall_thickness_on_base_slope_and_vertical(self):
        rays = [LineString([(0, -1), (0, 12)]),
                LineString([(60, 45), (45, 45)])]
        # Right sloping wall: x = 37.5 + (19.5/37.5)*y.
        x, y = 47.9, 20
        norm = math.hypot(37.5, 19.5)
        nx, ny = -37.5 / norm, 19.5 / norm
        rays.append(LineString([(x - nx, y - ny), (x + 12*nx, y + 12*ny)]))
        # Right lower circular corner: independently constructed centre/ray.
        angle = math.atan2(37.5, 19.5)
        radius = self.cap['bottom_radius_mm']
        cx, cy = 37.5 - radius*math.tan(angle/2), radius
        radial_angle = -math.pi/2 + angle/2
        ux, uy = math.cos(radial_angle), math.sin(radial_angle)
        rays.append(LineString([(cx + (radius + 1)*ux, cy + (radius + 1)*uy), (cx, cy)]))
        for ray in rays:
            self.assertAlmostEqual(ray.intersection(self.s['gutter']).length, 2.25, delta=0.001)
            self.assertAlmostEqual(ray.intersection(self.s['ledge']).length, 3, delta=0.001)

    def test_top_is_open_and_ledge_is_one_continuous_u(self):
        self.assertTrue(self.s['face'].covers(Point(0, 58)))
        self.assertFalse(self.s['ledge'].covers(Point(0, 58)))
        self.assertEqual(self.s['ledge'].geom_type, 'Polygon')
        self.assertFalse(self.s['ledge'].interiors)

    def test_fit_allowance_is_a_normal_gap(self):
        params = dict(self.cap)
        params['fit_clearance_mm'] = 0.2
        loose = get_gutter_sections(**params)
        self.assertAlmostEqual(loose['gutter'].distance(loose['ledge']), 0.2, delta=0.001)
        ray = LineString([(0, 0), (0, 12)])
        self.assertAlmostEqual(ray.intersection(loose['ledge']).length, 3, delta=0.001)

    def test_invalid_parameters_fail(self):
        for kwargs in ({'gutter_wall_mm': -1}, {'ledge_wall_mm': -1},
                       {'fit_clearance_mm': -0.1}, {'bottom_radius_mm': 1},
                       {'curve_step_degrees': 0}):
            with self.assertRaises(ValueError):
                get_gutter_sections(**kwargs)

    def test_cap_radius_increases_half_mm(self):
        self.assertEqual(self.cap['inside_bottom_diameter_mm'], 11)
        self.assertEqual(self.cap['bottom_radius_mm'] - self.cap['gutter_wall_mm'], 5.5)

    def test_flange_expands_face_six_mm_without_changing_insertion(self):
        expanded = get_cap_sections(**self.cap)
        for actual, expected in zip(expanded['face'].bounds, (-63, -6, 63, 64.5)):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(expanded['ledge'].equals_exact(self.s['ledge'], 0))
        for x, y in self.s['face'].exterior.coords:
            self.assertAlmostEqual(expanded['face'].boundary.distance(Point(x, y)), 6, delta=0.001)

    def test_open_variant_uses_oobb_cutters_on_correct_grid(self):
        from unittest.mock import patch
        option = next(o for o in get_options() if o['oobb_type'] == 'cap_end_open')
        layout = get_cap_opening_layout(**option)
        self.assertEqual((layout['width'], layout['depth'], layout['bottom'], layout['top']), (14, 38, 26.5, 64.5))
        self.assertEqual({(h['x'], h['y']) for h in layout['holes']},
                         {(-15, 27.5), (-15, 57.5), (15, 27.5), (15, 57.5)})
        with patch('working_scad.oobb.append_full') as append:
            get_cap_end_open({}, **option)
        cuts = [c.kwargs for c in append.call_args_list if c.kwargs['type'] == 'negative']
        self.assertEqual([c['shape'] for c in cuts], ['rounded_rectangle', 'cube'] + ['oobb_hole'] * 4 + ['polygon'])
        self.assertEqual(cuts[0]['size'][:2], [14, 38])
        self.assertEqual(cuts[0]['r'], 5)
        self.assertEqual({c['radius_name'] for c in cuts if c['shape'] == 'oobb_hole'}, {'m6'})

    def test_ledge_stops_below_clip_with_flat_three_mm_ends(self):
        self.assertEqual(self.s['ledge'].bounds[3], 49)
        for y in (45, 47, 48.99, 49):
            line = LineString([(-60, y), (60, y)])
            cross_section = line.intersection(self.s['ledge'])
            self.assertAlmostEqual(cross_section.length, 6)
        self.assertFalse(self.s['ledge'].intersects(LineString([(-60, 49.01), (60, 49.01)])))
        self.assertTrue(self.s['face'].covers(Point(0, 58.49)))

    def test_current_catalogue_uses_unversioned_part_names(self):
        for option in get_options():
            self.assertNotIn('version_', build_oomp_id(option))
            self.assertFalse(any(str(value).startswith('version_')
                                 for key, value in option.items() if key.startswith('taxonomy_')))


if __name__ == '__main__':
    unittest.main()
