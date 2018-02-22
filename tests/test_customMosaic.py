from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock

from mapps_tools.mosaics.CustomMosaic import CustomMosaic

valid_start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")


class TestCustomMosaic(TestCase):
    def test_overall(self):
        start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")
        angles = [(-0.40000000000000002, -3.4830000000000001), (-0.40000000000000002, -2.4510000000000001),
                  (-0.40000000000000002, -1.419), (-0.40000000000000002, -0.38700000000000001),
                  (-0.40000000000000002, 0.64500000000000002), (-0.40000000000000002, 1.677),
                  (-0.40000000000000002, 2.7090000000000001), (-0.40000000000000002, 3.7410000000000001),
                  (0.97600000000000009, 3.7410000000000001), (0.97600000000000009, 2.7090000000000001),
                  (0.97600000000000009, 1.677), (0.97600000000000009, 0.64500000000000002),
                  (0.97600000000000009, -0.38700000000000001), (0.97600000000000009, -1.419),
                  (0.97600000000000009, -2.4510000000000001), (0.97600000000000009, -3.4830000000000001),
                  (2.3520000000000003, -3.4830000000000001), (2.3520000000000003, -2.4510000000000001),
                  (2.3520000000000003, -1.419), (2.3520000000000003, -0.38700000000000001),
                  (2.3520000000000003, 0.64500000000000002), (2.3520000000000003, 1.677),
                  (2.3520000000000003, 2.7090000000000001), (2.3520000000000003, 3.7410000000000001),
                  (3.7280000000000006, 2.7090000000000001), (3.7280000000000006, 1.677),
                  (3.7280000000000006, 0.64500000000000002), (3.7280000000000006, -0.38700000000000001),
                  (3.7280000000000006, -1.419), (3.7280000000000006, -2.4510000000000001)]

        cm = CustomMosaic((1.72, 1.29), "CALLISTO", start_time, "min",
                          "deg", 0.5, 0.5, angles)
        generated_PTR = \
            '''<block ref="OBS">
	<startTime> 2031-04-26T00:40:47 </startTime>
	<endTime> 2031-04-26T01:13:26 </endTime>
	<attitude ref="track">
		<boresight ref="SC_Zaxis"/>
		<target ref="CALLISTO"/>
		<offsetRefAxis frame="SC">
			<x>1.0</x>
			<y>0.0</y>
			<z>0.0</z>
		</offsetRefAxis>
		<offsetAngles ref="custom">
			<startTime>2031-04-26T00:41:47</startTime>
			<deltaTimes units='min'>    0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.688   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.688   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25   0.86   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25  0.516   0.25   0.25   0.25 </deltaTimes>
			<xAngles units='deg'>        0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4    0.4 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976 -0.976  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -2.35  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73  -3.73 </xAngles>
			<xRates units='deg/min'>     0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0 </xRates>
			<yAngles units='deg'>      -3.48  -3.48  -3.48  -2.45  -2.45  -2.45  -1.42  -1.42  -1.42 -0.387 -0.387 -0.387  0.645  0.645  0.645   1.68   1.68   1.68   2.71   2.71   2.71   3.74   3.74   3.74   3.74   3.74   3.74   2.71   2.71   2.71   1.68   1.68   1.68  0.645  0.645  0.645 -0.387 -0.387 -0.387  -1.42  -1.42  -1.42  -2.45  -2.45  -2.45  -3.48  -3.48  -3.48  -3.48  -3.48  -3.48  -2.45  -2.45  -2.45  -1.42  -1.42  -1.42 -0.387 -0.387 -0.387  0.645  0.645  0.645   1.68   1.68   1.68   2.71   2.71   2.71   3.74   3.74   3.74   2.71   2.71   2.71   1.68   1.68   1.68  0.645  0.645  0.645 -0.387 -0.387 -0.387  -1.42  -1.42  -1.42  -2.45  -2.45  -2.45 </yAngles>
			<yRates units='deg/min'>     0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0    0.0 </yRates>
		</offsetAngles>
		<phaseAngle ref="powerOptimised">
			<yDir> false </yDir>
		</phaseAngle>
	</attitude>
</block>
'''
        self.assertEqual(cm.generate_PTR(), generated_PTR)

        cm = CustomMosaic((1.72, 1.29), "CALLISTO", start_time, "min",
                          "deg", 0.5, 0.312634, angles)
        generated_PTR = \
            '''<block ref="OBS">
	<startTime> 2031-04-26T00:40:47 </startTime>
	<endTime> 2031-04-26T01:07:34 </endTime>
	<attitude ref="track">
		<boresight ref="SC_Zaxis"/>
		<target ref="CALLISTO"/>
		<offsetRefAxis frame="SC">
			<x>1.0</x>
			<y>0.0</y>
			<z>0.0</z>
		</offsetRefAxis>
		<offsetAngles ref="custom">
			<startTime>2031-04-26T00:41:47</startTime>
			<deltaTimes units='min'>      0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.43018     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.43018     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.53773     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25  0.32264     0.25     0.25     0.25 </deltaTimes>
			<xAngles units='deg'>          0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4      0.4   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -0.976   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -2.352   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728   -3.728 </xAngles>
			<xRates units='deg/min'>       0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0 </xRates>
			<yAngles units='deg'>       -3.483   -3.483   -3.483   -2.451   -2.451   -2.451   -1.419   -1.419   -1.419   -0.387   -0.387   -0.387    0.645    0.645    0.645    1.677    1.677    1.677    2.709    2.709    2.709    3.741    3.741    3.741    3.741    3.741    3.741    2.709    2.709    2.709    1.677    1.677    1.677    0.645    0.645    0.645   -0.387   -0.387   -0.387   -1.419   -1.419   -1.419   -2.451   -2.451   -2.451   -3.483   -3.483   -3.483   -3.483   -3.483   -3.483   -2.451   -2.451   -2.451   -1.419   -1.419   -1.419   -0.387   -0.387   -0.387    0.645    0.645    0.645    1.677    1.677    1.677    2.709    2.709    2.709    3.741    3.741    3.741    2.709    2.709    2.709    1.677    1.677    1.677    0.645    0.645    0.645   -0.387   -0.387   -0.387   -1.419   -1.419   -1.419   -2.451   -2.451   -2.451 </yAngles>
			<yRates units='deg/min'>       0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0      0.0 </yRates>
		</offsetAngles>
		<phaseAngle ref="powerOptimised">
			<yDir> false </yDir>
		</phaseAngle>
	</attitude>
</block>
'''
        self.assertEqual(cm.generate_PTR(decimal_places=5), generated_PTR)

    def test_initializations(self):
        valid_angles = [(0.2, 0.2), (0.0, 0.0), (-0.2, 0.2)]
        with self.assertRaises(TypeError, msg="First argument should be invalidated."):
            CustomMosaic(0.1, "CALLISTO", valid_start_time, "min", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(TypeError, msg="First argument should be invalidated."):
            CustomMosaic((0.1, 0.1, 0.1), "CALLISTO", valid_start_time, "min", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(TypeError, msg="Second argument should be invalidated."):
            CustomMosaic((0.1, 1.0), 0.1, valid_start_time, "min", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(TypeError, msg="Second argument should be invalidated."):
            CustomMosaic((0.1, 1.0), None, valid_start_time, "min", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(TypeError, msg="Third argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", None, "min", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Fourth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "mins", "deg", 0.5, 0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Fifth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "degrees", 0.5, 0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Sixth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", -0.5, 0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Sixth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", -0.001, 0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Seventh argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, -0.5, valid_angles)
        with self.assertRaises(ValueError, msg="Seventh argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.0, valid_angles)
        with self.assertRaises(ValueError, msg="Eighth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, [])
        with self.assertRaises(TypeError, msg="Eighth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, None)
        with self.assertRaises(TypeError, msg="Eighth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, [1.0, 1.0])
        with self.assertRaises(TypeError, msg="Eighth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, [(1.0), (1.0, 1.0)])
        with self.assertRaises(TypeError, msg="Eighth argument should be invalidated."):
            CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, [None, None])
        # this should pass
        CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", 0.1, 0.1, [(0.1, 0.1), (-0.1, 0.1)])

    def test__calculate_end_time(self):
        slew_time_per_unit_angle = 2.0
        dwell_time = 2.0
        angle_sep = 3.0

        cm = CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", dwell_time, slew_time_per_unit_angle,
                          [(-angle_sep, 0.0), (0.0, 0.0), (angle_sep, 0.0), (angle_sep, angle_sep)])
        duration_min = 1.0 + 3 * angle_sep * slew_time_per_unit_angle + 4 * dwell_time + 1.0
        self.assertEqual(cm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

        cm = CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", dwell_time, slew_time_per_unit_angle,
                          [(0.0, 0.0)])
        duration_min = 1.0 + dwell_time + 1.0
        self.assertEqual(cm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

        cm = CustomMosaic((0.1, 1.0), "CALLISTO", valid_start_time, "min", "deg", dwell_time, slew_time_per_unit_angle,
                          [(0.0, 0.0), (0.0, 0.0)])
        duration_min = 1.0 + 2 * dwell_time + 1.0
        self.assertEqual(cm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

    def test__calculate_slew_to_next_point(self):
        calculate_slew_to_next_point = CustomMosaic._calculate_slew_to_next_point
        mock = Mock()
        mock.slew_time_per_angle = 2.5
        mock.center_points = [(0.0, -1.5), (0.0, 0.0)]
        self.assertEqual(calculate_slew_to_next_point(mock, 0), 3.75)
        with self.assertRaises(ValueError, msg="Should fail on negative input"):
            calculate_slew_to_next_point(mock, -1)
        with self.assertRaises(ValueError, msg="Should fail on input out of bounds"):
            calculate_slew_to_next_point(mock, 2)
        with self.assertRaises(TypeError, msg="Should fail on non-int input"):
            calculate_slew_to_next_point(mock, 1.1)

        mock = Mock()
        mock.slew_time_per_angle = 2.0
        mock.center_points = [(0.0, -1.5), (0.0, 0.0), (3.0, 4.0)]
        self.assertEqual(calculate_slew_to_next_point(mock, 1), 10.0)

