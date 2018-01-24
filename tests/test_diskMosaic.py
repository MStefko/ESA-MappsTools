from unittest import TestCase

from datetime import datetime, timedelta
from unittest.mock import Mock

from mosaics.DiskMosaic import DiskMosaic

valid_start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")

class TestDiskMosaic(TestCase):

    def test_initializations(self):
        fov_size = (1.2, 1.7)
        point_slew_time = 1.75
        line_slew_time = 2.25
        dwell_time = 3.0
        start_step_no = ((-1.5, 1.5), )
        with self.assertRaises(TypeError, msg="First argument should be invalidated."):
            DiskMosaic(1.2, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="First argument should be invalidated."):
            DiskMosaic(None, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="First argument should be invalidated."):
            DiskMosaic((1.2, 1.7, 1.3), "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Second argument should be invalidated."):
            DiskMosaic(fov_size, None, valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Second argument should be invalidated."):
            DiskMosaic(fov_size, 300, valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Third argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", None, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Third argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", "2031-04-25T22:40:47", "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(ValueError, msg="Fourth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "mins", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(ValueError, msg="Fifth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Sixth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5, 1.2), (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Sixth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       1.5, (1.5, -1.5), (3, 3))
        with self.assertRaises(TypeError, msg="Seventh argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), 1.5, (3, 3))
        with self.assertRaises(TypeError, msg="Eighth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), 9)
        with self.assertRaises(ValueError, msg="Eighth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (0, 3))
        with self.assertRaises(ValueError, msg="Eighth argument should be invalidated."):
            DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                       dwell_time, point_slew_time, line_slew_time,
                       (-1.5, 1.5), (1.5, -1.5), (3, -2))
        # this should pass
        DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                   dwell_time, point_slew_time, line_slew_time,
                   (-1.5, 1.5), (1.5, -1.5), (3, 3))

    def test__calculate_end_time(self):
        fov_size = (1.2, 1.7)
        point_slew_time = 1.75
        line_slew_time = 2.25
        dwell_time = 3.0

        dm = DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                        dwell_time, point_slew_time, line_slew_time,
                        (-1.5, 1.5), (1.5, -1.5), (3, 3))
        duration_min = 1.0 + 2 * line_slew_time + 6 * point_slew_time + 9 * dwell_time + 1.0
        self.assertEqual(dm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

        dm = DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                        dwell_time, point_slew_time, line_slew_time,
                        (-1.5, 1.5), (1.5, -1.5), (4, 3))
        duration_min = 1.0 + 3 * line_slew_time + 8 * point_slew_time + 12 * dwell_time + 1.0
        self.assertEqual(dm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

        dm = DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                        dwell_time, point_slew_time, line_slew_time,
                        (-1.5, 1.5), (1.5, -1.5), (1, 1))
        duration_min = 1.0 + 1 * dwell_time + 1.0
        self.assertEqual(dm._calculate_end_time(), valid_start_time + timedelta(minutes=duration_min))

    def test__generate_center_points(self):
        fun = DiskMosaic._generate_center_points
        mock = Mock()
        mock.start = (-1.5, 1.5)
        mock.points = (3, 3)
        mock.delta = (1.5, -1.5)

        result = [(-1.5, 1.5), (-1.5, 0.0), (-1.5, -1.5),
                         (0.0, -1.5), (0.0, 0.0), (0.0, 1.5),
                         (1.5, 1.5), (1.5, 0.0), (1.5, -1.5)]
        self.assertEqual(fun(mock), result)

        mock = Mock()
        mock.start = (-1.5, 1.5)
        mock.points = (1, 2)
        mock.delta = (1.5, -1.5)
        result = [(-1.5, 1.5), (-1.5, 0.0)]
        self.assertEqual(fun(mock), result)

        mock = Mock()
        mock.start = (-1.5, 1.5)
        mock.points = (1, 1)
        mock.delta = (1.5, -1.5)
        result = [(-1.5, 1.5)]
        self.assertEqual(fun(mock), result)

    def test_generate_PTR(self):
        fun = DiskMosaic.generate_PTR
        mock = Mock()
        mock.start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")
        mock._calculate_end_time.return_value = datetime.strptime("2031-04-26T01:24:47", "%Y-%m-%dT%H:%M:%S")
        mock.point_slew_time = 1.75
        mock.line_slew_time = 2.25
        mock.dwell_time = 3.0
        mock.angular_unit = "deg"
        mock.time_unit = "min"
        mock.target = "CALLISTO"
        mock.start = (-1.5, 1.5)
        mock.points = (3, 3)
        mock.delta = (1.5, -1.5)

        generated_PTR = \
'''<block ref="OBS">
	<startTime> 2031-04-26T00:40:47 </startTime>
	<endTime> 2031-04-26T01:24:47 </endTime>
	<attitude ref="track">
		<boresight ref="SC_Zaxis"/>
		<target ref="CALLISTO"/>
		<offsetRefAxis frame="SC">
			<x>1.0</x>
			<y>0.0</y>
			<z>0.0</z>
		</offsetRefAxis>
		<offsetAngles ref="raster">
			<startTime>2031-04-26T00:41:47</startTime>
			<xPoints>3</xPoints>
			<yPoints>3</yPoints>
			<xStart units="deg">-1.5000</xStart>
			<yStart units="deg">1.5000</yStart>
			<xDelta units="deg">1.5000</xDelta>
			<yDelta units="deg">-1.5000</yDelta>
			<pointSlewTime units="min">1.7500</pointSlewTime>
			<lineSlewTime units="min">2.2500</lineSlewTime>
			<dwellTime units="min">3.0000</dwellTime>
			<lineAxis>Y</lineAxis>
			<keepLineDir>false</keepLineDir>
		</offsetAngles>
		<phaseAngle ref="powerOptimised">
			<yDir> false </yDir>
		</phaseAngle>
	</attitude>
</block>
'''
        self.assertEqual(fun(mock, decimal_places=4), generated_PTR)

        generated_PTR = \
'''<block ref="OBS">
	<startTime> 2031-04-26T00:40:47 </startTime>
	<endTime> 2031-04-26T01:24:47 </endTime>
	<attitude ref="track">
		<boresight ref="SC_Zaxis"/>
		<target ref="CALLISTO"/>
		<offsetRefAxis frame="SC">
			<x>1.0</x>
			<y>0.0</y>
			<z>0.0</z>
		</offsetRefAxis>
		<offsetAngles ref="raster">
			<startTime>2031-04-26T00:41:47</startTime>
			<xPoints>3</xPoints>
			<yPoints>3</yPoints>
			<xStart units="deg">-1.500</xStart>
			<yStart units="deg">1.500</yStart>
			<xDelta units="deg">1.500</xDelta>
			<yDelta units="deg">-1.500</yDelta>
			<pointSlewTime units="min">1.750</pointSlewTime>
			<lineSlewTime units="min">2.250</lineSlewTime>
			<dwellTime units="min">3.000</dwellTime>
			<lineAxis>Y</lineAxis>
			<keepLineDir>false</keepLineDir>
		</offsetAngles>
		<phaseAngle ref="powerOptimised">
			<yDir> false </yDir>
		</phaseAngle>
	</attitude>
</block>
'''
        self.assertEqual(fun(mock), generated_PTR)
