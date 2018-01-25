from unittest import TestCase
from unittest.mock import patch

from datetime import datetime
import numpy as np

from mosaics.misc import get_nadir_point_surface_velocity_kps, \
     get_pixel_size_km, get_max_dwell_time_s


valid_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")

class TestMisc(TestCase):
    distance_to_surface = 3630.0
    # side_effect list is repeated 20 times so that all tests can run
    @patch('mosaics.misc.spy.sincpt',
           side_effect=20*[ ((0.0, 0.0, 12345.0), 45.5, (0.0, 0.0, 3630.0)),
                         ((300.0, 400.0, 12345.0), 45.7, (0.0, 0.0, 3430.0))])
    @patch('mosaics.misc.datetime2et', side_effect=20*[1346879.3, 1346889.3])
    def test_get_nadir_point_surface_velocity_kps(self, mock_datetime2et, mock_sincpt):
        self.assertEqual(500.0/10.0,
                         get_nadir_point_surface_velocity_kps("JUICE", "CALLISTO", valid_time, delta_s=10.0))
        self.assertEqual(500.0/4.0,
                         get_nadir_point_surface_velocity_kps("JUICE", "CALLISTO", valid_time, delta_s=4.0))
        with self.assertRaises(ValueError, msg="Should fail on negative delta_s"):
            get_nadir_point_surface_velocity_kps("JUICE", "CALLISTO", valid_time, delta_s=-1.0)
        with self.assertRaises(ValueError, msg="Should fail on zero delta_s"):
            get_nadir_point_surface_velocity_kps("JUICE", "CALLISTO", valid_time, delta_s=0.0)
        with self.assertRaises(TypeError, msg="Should fail on null time"):
            get_nadir_point_surface_velocity_kps("JUICE", "CALLISTO", None, delta_s=1.0)


    @patch('mosaics.misc.spy.sincpt',
           return_value=((0.0, 0.0, 12345.0), 45.5, (0.0, 0.0, distance_to_surface)))
    @patch('mosaics.misc.datetime2et', return_value = 1346879.3)
    def test_get_pixel_size_km(self, mock_datetime2et, mock_sincpt):
        self.assertAlmostEqual(get_pixel_size_km("JUICE", "CALLISTO", valid_time, 2.0, 200),
                               np.tan(1.0*np.pi/180)*TestMisc.distance_to_surface/100)
        self.assertAlmostEqual(get_pixel_size_km("JUICE", "CALLISTO", valid_time, 1.0, 350),
                               np.tan(0.5*np.pi/180)*TestMisc.distance_to_surface/175)
        with self.assertRaises(ValueError, msg="Should fail on negative fov_full_angle_deg"):
            get_pixel_size_km("JUICE", "CALLISTO", valid_time, -1.0, 10)
        with self.assertRaises(ValueError, msg="Should fail on zero fov_full_angle_deg"):
            get_pixel_size_km("JUICE", "CALLISTO", valid_time, 0.0, 10)
        with self.assertRaises(ValueError, msg="Should fail on negative fov_full_px"):
            get_pixel_size_km("JUICE", "CALLISTO", valid_time, 1.0, -10)
        with self.assertRaises(ValueError, msg="Should fail on zero fov_full_px"):
            get_pixel_size_km("JUICE", "CALLISTO", valid_time, 1.0, 0)

    @patch('mosaics.misc.get_nadir_point_surface_velocity_kps', side_effect=20*[5.0, 3.3])
    @patch('mosaics.misc.get_pixel_size_km',                    side_effect=20*[0.5, 1.0])
    def test_get_max_dwell_time_s(self, mock_get_pixelsize, mock_get_nadir_velocity):
        self.assertEqual(get_max_dwell_time_s(0.6, "JUICE", "CALLISTO", valid_time, 1.0, 3), 0.5 * 0.6 / 5.0)
        self.assertEqual(get_max_dwell_time_s(0.31, "JUICE", "CALLISTO", valid_time, 1.0, 3), 1.0 * 0.31 / 3.3)
        with self.assertRaises(ValueError, msg="Should fail on negative max_smear"):
            get_max_dwell_time_s(-0.3, "JUICE", "CALLISTO", valid_time, 1.0, 3)
        with self.assertRaises(ValueError, msg="Should fail on zero max_smear"):
            get_max_dwell_time_s(0.0, "JUICE", "CALLISTO", valid_time, 1.0, 3)