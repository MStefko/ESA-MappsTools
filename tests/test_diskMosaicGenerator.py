from unittest import TestCase
from unittest.mock import patch
from mosaics.DiskMosaicGenerator import DiskMosaicGenerator

from datetime import datetime

valid_start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")

class TestDiskMosaicGenerator(TestCase):

    @patch('mosaics.DiskMosaic.spy.str2et', return_value=1.0)
    @patch('mosaics.DiskMosaicGenerator.get_body_angular_diameter_rad', return_value=0.19167923151263316)
    def test_generate_symmetric_mosaic(self, mock_diam, mock_str2et):
        dmg = DiskMosaicGenerator((3.0, 2.0), "JUICE", "CALLISTO", valid_start_time, "min",
                      "deg", 2.0, 0.04*60)
        dm = dmg.generate_symmetric_mosaic(margin=0.1)
        center_points = [(-4.54032604229169, -5.04032604229169), (-4.54032604229169, -3.360217361527793),
                         (-4.54032604229169, -1.6801086807638965), (-4.54032604229169, 0.0),
                         (-4.54032604229169, 1.6801086807638965), (-4.54032604229169, 3.360217361527794),
                         (-4.54032604229169, 5.04032604229169), (-2.270163021145845, 5.04032604229169),
                         (-2.270163021145845, 3.360217361527794), (-2.270163021145845, 1.6801086807638965),
                         (-2.270163021145845, 0.0), (-2.270163021145845, -1.6801086807638965),
                         (-2.270163021145845, -3.360217361527793), (-2.270163021145845, -5.04032604229169),
                         (0.0, -5.04032604229169), (0.0, -3.360217361527793), (0.0, -1.6801086807638965),
                         (0.0, 0.0), (0.0, 1.6801086807638965), (0.0, 3.360217361527794), (0.0, 5.04032604229169),
                         (2.2701630211458452, 5.04032604229169), (2.2701630211458452, 3.360217361527794),
                         (2.2701630211458452, 1.6801086807638965), (2.2701630211458452, 0.0),
                         (2.2701630211458452, -1.6801086807638965), (2.2701630211458452, -3.360217361527793),
                         (2.2701630211458452, -5.04032604229169), (4.54032604229169, -5.04032604229169),
                         (4.54032604229169, -3.360217361527793), (4.54032604229169, -1.6801086807638965),
                         (4.54032604229169, 0.0), (4.54032604229169, 1.6801086807638965),
                         (4.54032604229169, 3.360217361527794), (4.54032604229169, 5.04032604229169)]
        self.assertAlmostEqual(dm.center_points, center_points, places=4)

    def test__optimize_steps_centered(self):
        osc = DiskMosaicGenerator._optimize_steps_centered

        with self.assertRaises(ValueError, msg="Overlap between 0.0 (incl.) and 1.0 (excl.)"):
            osc(5.0, 2.0, -0.3)
        with self.assertRaises(ValueError, msg="Overlap between 0.0 (incl.) and 1.0 (excl.)"):
            osc(5.0, 2.0, 1.0)

        self.assertEqual(osc(0.9, 1.0, 0.0), (1, 0.0, 1.0))
        self.assertEqual(osc(0.9, 1.0, 0.9), (1, 0.0, 1.0))

        self.assertEqual(osc(1.8, 1.0, 0.0), (2, -0.4, 0.8))
        self.assertEqual(osc(1.8, 1.0, 0.3), (3, -0.4, 0.4))

        self.assertEqual(osc(5, 1, 0.0), (5, -2.0, 1.0))
        self.assertEqual(osc(4, 1, 0.1), (5, -1.5, 0.75))

        self.assertEqual(osc(10, 1, 0.9), (91, -4.5, 0.1))