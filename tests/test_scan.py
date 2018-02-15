from unittest import TestCase

from datetime import datetime, timedelta
from unittest.mock import Mock

from mosaics.Scan import Scan

valid_time = datetime.strptime("2031-09-27T09:40:00", "%Y-%m-%dT%H:%M:%S")

class TestScan(TestCase):
    def test_initializations(self):
        fov_width = 3.4
        with self.assertRaises(ValueError, msg="Argument 1 should be invalidated."):
            Scan(-2.0, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 1 should be invalidated."):
            Scan(0.0, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 1 should be invalidated."):
            Scan(None, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 2 should be invalidated."):
            Scan(2.5, None, valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 2 should be invalidated."):
            Scan(2.5, 0.36, valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 3 should be invalidated."):
            Scan(2.5, "CALLISTO", None, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 3 should be invalidated."):
            Scan(2.5, "CALLISTO", 4.16, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 4 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "MIN", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 4 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, None, "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 4 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min ", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 5 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", " deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 5 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", None, 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 6 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", -1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 6 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 0.0, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 6 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", None, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 7 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, -3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 7 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 0.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 8 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, -3.2,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(ValueError, msg="Argument 8 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 0.0,
                 (-3.4, 2.1), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 9 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 2.1, (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 9 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (2.1, None), (2.3, -4.2), 3)
        with self.assertRaises(TypeError, msg="Argument 10 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), 2.3, 3)
        with self.assertRaises(TypeError, msg="Argument 10 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, None), 3)
        with self.assertRaises(TypeError, msg="Argument 10 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2, 0.1), 3)
        with self.assertRaises(ValueError, msg="Argument 11 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 0)
        with self.assertRaises(ValueError, msg="Argument 11 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), 1.0)
        with self.assertRaises(TypeError, msg="Argument 11 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), None)
        with self.assertRaises(TypeError, msg="Argument 11 should be invalidated."):
            Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
                 (-3.4, 2.1), (2.3, -4.2), "1")
        # this should pass
        Scan(2.5, "CALLISTO", valid_time, "min", "deg", 1.5, 3.0, 3.2,
             (-3.4, 2.1), (2.3, -4.2), 2)

    def test__calculate_end_time(self):
        fun = Scan._calculate_end_time
        mock = Mock()
        distance = 4.31
        mock.delta = (None, distance)
        mock.scan_slew_rate = 2.18
        mock.border_slew_time = 0.6
        mock.number_of_lines = 4
        mock.line_slew_time = 7.3
        mock.time_unit = "min"
        mock.start_time = valid_time

        end_time = valid_time + timedelta(seconds=10) + timedelta(minutes=1) + \
            timedelta(minutes=(4 * (distance / 2.18) + 2 * 0.6 + 3 * 7.3))
        self.assertEqual(fun(mock), end_time.replace(microsecond=0))


    def test__generate_center_points(self):
        fun = Scan._generate_center_points
        mock = Mock()
        mock.start = (-3.6, 2.1)
        mock.delta = (-2.1, 7.3)
        mock.number_of_lines = 3
        result = [(-3.6, 2.1 + 7.3/2), (-3.6-2.1, 2.1 + 7.3/2), (-3.6-2*2.1, 2.1 + 7.3/2)]
        self.assertEqual(fun(mock), result)

        mock.number_of_lines = 1
        self.assertEqual(fun(mock), result[0:1])

    def test_generate_PTR(self):
        fov_width = 3.4
        valid_start_time = datetime.strptime("2031-09-27T09:40:00", "%Y-%m-%dT%H:%M:%S")
        s = Scan(fov_width, "CALLISTO", valid_start_time, "min", "deg",
                 0.00859 / (2 / 60), 5, 5, (-1.5, 3.3), (0.9 * fov_width, -6.5), 2)
        PTR = \
"""<block ref="OBS">
\t<startTime> 2031-09-27T09:40:00 </startTime>
\t<endTime> 2031-09-27T10:46:36 </endTime>
\t<attitude ref="track">
\t\t<boresight ref="SC_Zaxis"/>
\t\t<target ref="CALLISTO"/>
\t\t<offsetRefAxis frame="SC">
\t\t\t<x>1.0</x>
\t\t\t<y>0.0</y>
\t\t\t<z>0.0</z>
\t\t</offsetRefAxis>
\t\t<offsetAngles ref="scan">
\t\t\t<startTime>2031-09-27T09:45:10</startTime>
\t\t\t<numberOfLines> 2 </numberOfLines>
\t\t\t<xStart units="deg">1.500</xStart>
\t\t\t<yStart units="deg">3.300</yStart>
\t\t\t<lineDelta units="deg">-3.060</lineDelta>
\t\t\t<scanDelta units="deg">-6.500</scanDelta>
\t\t\t<scanSpeed units="deg/min">0.258</scanSpeed>
\t\t\t<scanSlewTime units="min">1.0</scanSlewTime>
\t\t\t<lineSlewTime units="min">5.000</lineSlewTime>
\t\t\t<borderSlewTime units="min">5.000</borderSlewTime>
\t\t\t<lineAxis>Y</lineAxis>
\t\t\t<keepLineDir>false</keepLineDir>
\t\t</offsetAngles>
\t\t<phaseAngle ref="powerOptimised">
\t\t\t<yDir> false </yDir>
\t\t</phaseAngle>
\t</attitude>
</block>
"""
        self.assertEqual(s.generate_PTR(), PTR)
