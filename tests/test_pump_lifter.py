import copy
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from shapely import affinity
from shapely.geometry import Point
from working_oomp_populate import get_options
from working_split_parts import halves
from working_scad import get_gutter_sections
from working_pump_lifter import get_layout, build, make_scad_portable


class PumpLifterTests(unittest.TestCase):
    def setUp(self):
        self.options = halves(next(o for o in get_options() if o['oobb_type']=='lifter_pump_inlet'))
        self.a, self.b = self.options

    def test_two_distinct_halves_mate_after_half_turn(self):
        a, b = [get_layout(**o) for o in self.options]
        self.assertFalse(a['path'].equals(b['path']))
        self.assertTrue(a['path'].equals(affinity.scale(b['path'], xfact=-1, origin=(0, 0))))
        self.assertEqual({(f['x'], f['y']) for f in a['fasteners']},
                         {(-f['x'], f['y']) for f in b['fasteners']})
        self.assertEqual([o['print_quantity'] for o in self.options], [1, 1])

    def test_channel_clears_both_gutters_and_exits_above_inside_floor(self):
        layout = get_layout(**self.a)
        self.assertEqual(layout['entry_y'], 66.75)
        self.assertEqual(layout['outlet_y'] - self.a['gutter_wall_mm'], 15)
        gutter = get_gutter_sections(**self.a)['gutter']
        tube_envelope = layout['path'].buffer(self.a['tube_od_mm'] / 2)
        self.assertEqual(tube_envelope.intersection(gutter).area, 0)
        self.assertEqual(tube_envelope.intersection(affinity.translate(gutter, yoff=75)).area, 0)
        self.assertFalse(layout['outline'].contains(Point(0, 10)))
        self.assertTrue(layout['outline'].contains(Point(24, 3)))

    def test_oobb_fasteners_are_complementary_and_on_outer_faces(self):
        for option in self.options:
            with patch('working_pump_lifter.oobb.append_full') as append:
                build({'components': []}, **option)
            calls = [c.kwargs for c in append.call_args_list]
            screws = [c for c in calls if c['shape'] == 'oobb_screw_countersunk']
            nuts = [c for c in calls if c['shape'] == 'oobb_nut']
            self.assertEqual((len(screws), len(nuts)), (4, 0) if option['pump_half'] == 'a' else (0, 4))
            self.assertTrue(all(c['pos'][2] == 0 for c in screws))
            self.assertTrue(all(c['pos'][2] == c['depth'] for c in nuts))
            for cut in screws + nuts:
                self.assertTrue(cut['overhang'])
                self.assertEqual(cut['clearance'], 'top')
                self.assertEqual(cut['rot'], [180, 0, 0])
            self.assertEqual(len([c for c in calls if c['shape'] == 'raw_scad']), 1)

    def test_invalid_bend_clamp_and_entry_fail(self):
        for change in ({'tube_bend_radius_mm': 50}, {'tube_guide_diameter_mm': 18},
                       {'tube_grip_diameter_mm': 15}, {'thickness_mm': 9}):
            parameters = copy.deepcopy(self.a)
            parameters.update(change)
            with self.assertRaises(ValueError):
                get_layout(**parameters)

    def test_exported_scad_has_no_external_channel_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / 'part'
            folder.mkdir()
            (root / 'scad_reference').mkdir()
            module = 'module pump_tube_channel_half_a() { sphere(7); }'
            (root / 'scad_reference/pump_tube_channel_half_a.scad').write_text(module)
            target = folder / '3dpr.scad'
            target.write_text('use <../scad_reference/pump_tube_channel_half_a.scad>;\npump_tube_channel_half_a();')
            make_scad_portable(folder)
            self.assertNotIn('use <', target.read_text())
            self.assertIn(module, target.read_text())


if __name__ == '__main__':
    unittest.main()
