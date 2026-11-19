import unittest
from shapely.geometry import box
from working_oomp_populate import get_options
from working_pump_cradle import get_layout
from working_scad import get_gutter_sections


class PumpCradleTests(unittest.TestCase):
    def test_two_identical_ribs_support_all_four_offset_feet(self):
        p = next(o for o in get_options() if o['oobb_type']=='pump_support_cradle')
        layout = get_layout(**p)
        self.assertEqual(p['print_quantity'], 2)
        self.assertEqual(layout['feet'], [-41, 19])
        self.assertEqual(p['foot_pitch_mm'], 60)
        self.assertEqual(p['holder_seat_height_mm'], 26)
        self.assertEqual(layout['section'].difference(get_gutter_sections(**p)['cavity']).area, 0)
        self.assertAlmostEqual(layout['section'].bounds[1], p['gutter_wall_mm'])
        for x in layout['feet']:
            self.assertTrue(layout['section'].covers(box(x-6,25.9,x+6,26.1)))
        self.assertGreater(p['support_thickness_mm'] - p['foot_pocket_width_mm'], 5)
