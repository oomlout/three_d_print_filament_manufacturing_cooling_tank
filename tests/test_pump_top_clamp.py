import unittest
from unittest.mock import patch
import numpy as np
from shapely import affinity
from working_oomp_populate import get_options
from working_split_parts import halves
from working_pump_top_clamp import get_layout, build


class PumpTopClampTests(unittest.TestCase):
    def test_25_mm_screw_reaches_nut_without_opening_the_tube_channel(self):
        pair = halves(next(o for o in get_options() if o['oobb_type']=='pump_hose_clamp'))
        cuts = []
        for p in pair:
            with patch('working_pump_top_clamp.oobb.append_full') as append:
                build({'components': []}, **p)
            fasteners = [c.kwargs for c in append.call_args_list
                         if c.kwargs['shape'] in ('oobb_screw_countersunk', 'oobb_nut')]
            mount = next(c.kwargs for c in append.call_args_list
                         if c.kwargs['shape'] == 'oobb_screw_socket_cap')
            self.assertEqual(mount['radius_name'], 'm6')
            self.assertTrue(mount['overhang'])
            self.assertEqual(mount['clearance'], 'top')
            self.assertEqual(len(fasteners), 3)
            for cut in fasteners:
                self.assertTrue(cut['overhang'])
                self.assertEqual(cut['clearance'], 'top')
            cuts.append(fasteners[0])
        screw, nut = cuts
        d = pair[0]['half_thickness_mm']
        nut_bearing = 2*d - nut['pos'][2]
        nut_outer = nut_bearing + nut['depth']
        tip = screw['pos'][2] + screw['depth']
        self.assertEqual(screw['depth'], 25)
        self.assertEqual(screw['pos'][2], 10)
        self.assertAlmostEqual(tip - nut_outer, 1)
        self.assertGreater(nut_bearing, d + 5)
        self.assertLess(screw['pos'][2] + 2, d - 5)

    def test_one_catalogue_entry_with_rigid_outlet_clearance(self):
        parts = [p for p in get_options() if p['oobb_type']=='pump_hose_clamp']
        self.assertEqual(len(parts),1)
        p = parts[0]
        self.assertTrue(p['print_set'])
        self.assertNotIn('clamp_half',p)
        self.assertGreaterEqual(p['bend_start_above_mount_mm']-p['rigid_outlet_above_mount_mm'],9)
        self.assertGreaterEqual(p['rigid_clearance_diameter_mm']-p['tube_od_mm'],2)
        self.assertEqual(p['mount_tool_radius_mm']*2,16)

    def test_halves_align_with_a_physical_half_turn(self):
        a,b = [get_layout(**p) for p in halves(next(o for o in get_options() if o['oobb_type']=='pump_hose_clamp'))]
        self.assertTrue(a['outline'].equals_exact(affinity.scale(b['outline'],xfact=-1,origin=(0,0)),1e-8))
        self.assertEqual(a['joints'],[(-x,y) for x,y in b['joints']])

    def test_r40_and_m6_driver_access(self):
        p = halves(next(p for p in get_options() if p['oobb_type']=='pump_hose_clamp'))[0]
        layout = get_layout(**p)
        cx,cy = layout['bend_centre']
        for x,y in list(layout['path'].coords)[1:-1]:
            self.assertAlmostEqual(np.hypot(x-cx,y-cy),40)
        for x,y in layout['joints']:
            self.assertGreater(abs(x-p['mount_row_offset_mm']),p['mount_tool_radius_mm']+3.6)
        self.assertEqual(p['mount_hole_axial_mm']*2,30)


if __name__=='__main__':
    unittest.main()
