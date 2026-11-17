"""Mating seal alignment, lands, cord compression and cover hole selection."""
import math
import unittest
from unittest.mock import patch

from shapely.geometry import Point, box
from working_oomp_populate import get_options
from working_scad import get_cap_seal_geometry, get_cap_cover


class CapSealTests(unittest.TestCase):
    def setUp(self):
        self.cap = next(o for o in get_options() if o['oobb_type'] == 'cap_end_open')
        self.cover = next(o for o in get_options() if o['oobb_type'] == 'cap_cover')

    def test_grooves_match_and_clear_holes_slot_and_cover_edge(self):
        groove = get_cap_seal_geometry(**self.cap)['groove']
        self.assertTrue(groove.equals_exact(get_cap_seal_geometry(**self.cover)['groove'], 0))
        self.assertAlmostEqual(groove.distance(box(-7, 31.5, 7, 64.5)), 1.175, delta=0.001)
        for x in (-15, 15):
            for y in (27.5, 57.5):
                self.assertGreaterEqual(groove.distance(Point(x, y).buffer(3.25)), 1.1749)
        self.assertAlmostEqual(groove.bounds[1] - 20.5, 2.425)
        self.assertTrue(groove.covers(Point(9.375, 64.5)))
        self.assertTrue(groove.covers(Point(-9.375, 64.5)))
        self.assertFalse(groove.covers(Point(0, 64.5)))

    def test_single_cord_compression_and_retained_walls(self):
        depth = self.cap['seal_groove_depth_mm']
        width = self.cap['seal_groove_width_mm']
        cord = self.cap['seal_cord_diameter_mm']
        self.assertAlmostEqual(1 - 2 * depth / cord, 0.2)
        self.assertLess(math.pi * (cord / 2)**2 / (2 * depth * width), 0.85)
        self.assertEqual(cord, 2)
        self.assertAlmostEqual(self.cap['front_plate_mm'] - depth, 2.2)
        self.assertAlmostEqual(self.cover['cover_thickness_mm'] - depth, 2.2)

    def test_standard_plate_has_exactly_four_corner_holes_and_centre(self):
        with patch('working_scad.oobb.append_full') as append:
            get_cap_cover({}, **self.cover)
        calls = [c.kwargs for c in append.call_args_list]
        self.assertEqual(calls[0]['shape'], 'oobb_plate')
        self.assertEqual((calls[0]['width'], calls[0]['height'], calls[0]['depth'], calls[0]['r']), (3, 3, 3, 5))
        self.assertFalse(calls[0]['holes'])
        holes = [c for c in calls if c['shape'] == 'oobb_hole']
        self.assertEqual({tuple(c['pos'][:2]) for c in holes}, {(-15, -15), (-15, 15), (15, -15), (15, 15), (0, 0)})
        self.assertEqual(len(holes), 5)
        self.assertEqual({c['radius_name'] for c in holes}, {'m6'})


if __name__ == '__main__':
    unittest.main()
