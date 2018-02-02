# coding=utf-8
""" Raster mosaic class.

@author: Marcel Stefko
"""
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import spiceypy as spy

from mosaics.misc import Rectangle, get_body_angular_diameter_rad


class DiskMosaic:
    allowed_time_units = {"sec": "seconds", "min": "minutes", "hour": "hours"}
    allowed_angular_units = {"deg": 180/np.pi, "rad": 1.0, "arcMin": 3438, "arcSec": 206265}

    def __init__(self, fov_size: Tuple[float, float],
                 target: str, start_time: datetime,
                 time_unit: str, angular_unit: str,
                 dwell_time: float,
                 point_slew_time: float, line_slew_time: float,
                 start: Tuple[float, float],
                 delta: Tuple[float, float],
                 points: Tuple[int, int],
                 target_radius = None,
                 target_radius_with_margin = None):
        """ Create a DiskMosaic


        :param fov_size: 2-tuple (x, y) containing rectangular FOV size
        :param target: Name of target body, e.g. "CALLISTO"
        :param start_time: Time of beginning of mosaic
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        :param dwell_time: Dwell time at each mosaic point
        :param point_slew_time: Time to slew between two mosaic points in the same line
        :param line_slew_time: Time to slew from end of one line to beginning of another
        :param start: 2-tuple (x, y) starting position
        :param delta: 2-tuple (x, y) spacing between points
        :param points: 2-tuple (x, y) number of points
        :param target_radius:
        :param target_radius_with_margin:
        """
        if len(fov_size) != 2:
            raise TypeError("FOV size must be a tuple of length 2")
        if any([x < 0.0 for x in fov_size]):
            raise ValueError(f"FOV size values must be non-negative: {fov_size}")
        self.fov_size = fov_size

        if not isinstance(target, str):
            raise TypeError("Target must be a string.")
        self.target = target
        if not isinstance(start_time, datetime):
            raise TypeError("Start time must be a datetime object.")
        self.start_time = start_time
        if time_unit not in DiskMosaic.allowed_time_units:
            raise ValueError(f"Time unit must be one of following: {DiskMosaic.allowed_time_units}")
        self.time_unit = time_unit
        if angular_unit not in DiskMosaic.allowed_angular_units:
            raise ValueError(f"Angular unit must be one of following: {DiskMosaic.allowed_angular_units}")
        self.angular_unit = angular_unit
        if dwell_time < 0.0:
            raise ValueError(f"Dwell time must be non-negative: {dwell_time}")
        self.dwell_time = dwell_time
        if point_slew_time < 0.0:
            raise ValueError(f"Point slew time must be non-negative: {point_slew_time}")
        self.point_slew_time = point_slew_time
        if line_slew_time < 0.0:
            raise ValueError(f"Line slew time must be non-negative: {line_slew_time}")
        self.line_slew_time = line_slew_time
        if len(start) != 2:
            raise TypeError("Start position must be an iterable of length 2")
        self.start = start
        if len(delta) != 2:
            raise TypeError("Delta must be an iterable of length 2")
        self.delta = delta
        if len(points) != 2:
            raise TypeError("Number of points must be an iterable of length 2")
        if any(x < 1 for x in points):
            raise ValueError(f"Need at least 1 point in both x and y directions: {points}")
        if any(not isinstance(x, int) for x in points):
            raise TypeError("Number of points in both axes must be an integer.")
        self.points = points

        self.target_radius = target_radius
        self.target_radius_with_margin = target_radius_with_margin

    def _calculate_end_time(self) -> datetime:
        """ Calculates time duration of mosaic, and thus the earliest end time.

        :return: Earliest possible end time for PTR request
        """
        x_points, y_points = self.points
        line_slews = x_points - 1
        point_slews_per_line = y_points - 1
        slew_time = line_slews * self.line_slew_time + \
                    point_slews_per_line * x_points * self.point_slew_time
        dwell_time = self.dwell_time * (x_points * y_points)
        # Required delay from start time.
        initial_delay = timedelta(minutes=1)
        # Required delay after finishing
        final_delay = timedelta(minutes=1)
        # Next line picks the correct keyword argument for timedelta object so that we have
        # correct units. (E.g. if self.time_unit is "min", the keyword argument has to be
        # "minutes").
        timedelta_kwarg = {DiskMosaic.allowed_time_units[self.time_unit]: slew_time + dwell_time}
        delay = initial_delay + timedelta(**timedelta_kwarg) + final_delay
        end_time = self.start_time + delay
        return end_time.replace(microsecond=0)

    @property
    def end_time(self) -> datetime:
        return self._calculate_end_time()

    def _generate_rectangles(self) -> List[Rectangle]:
        """

        :return: List of image Rectangles in order of acquisition
        """
        return [Rectangle(cp, self.fov_size) for cp in self._generate_center_points()]

    def _generate_center_points(self) -> List[Tuple[float, float]]:
        """

        :return: List of (x,y) center points in order of acquisition.
        """
        x_points, y_points = self.points
        x_start, y_start = self.start
        x_delta, y_delta = self.delta
        center_points = []
        for x in range(x_points):
            line_points = []
            for y in range(y_points):
                line_points.append((x_start + x*x_delta,
                                    y_start + y*y_delta))
            if x % 2:
                line_points = line_points[::-1]
            center_points += line_points
        return center_points

    @property
    def rectangles(self) -> List[Rectangle]:
        return self._generate_rectangles()

    @property
    def center_points(self) -> List[Tuple[float, float]]:
        return self._generate_center_points()

    def generate_PTR(self, decimal_places = 3) -> str:
        """ Generates a PTR request for MAPPS for this mosaic

        :param decimal_places: Number of max decimal places for values.
        :return: PTR request string
        """
        x_points, y_points = self.points
        x_start, y_start = self.start
        x_delta, y_delta = self.delta
        PTR = \
f'''<block ref="OBS">
\t<startTime> {self.start_time.isoformat()} </startTime>
\t<endTime> {self._calculate_end_time().isoformat()} </endTime>
\t<attitude ref="track">
\t\t<boresight ref="SC_Zaxis"/>
\t\t<target ref="{self.target}"/>
\t\t<offsetRefAxis frame="SC">
\t\t\t<x>1.0</x>
\t\t\t<y>0.0</y>
\t\t\t<z>0.0</z>
\t\t</offsetRefAxis>
\t\t<offsetAngles ref="raster">
\t\t\t<startTime>{(self.start_time+timedelta(minutes=1)).isoformat()}</startTime>
\t\t\t<xPoints>{x_points}</xPoints>
\t\t\t<yPoints>{y_points}</yPoints>
\t\t\t<xStart units="{self.angular_unit}">{x_start:.{decimal_places}f}</xStart>
\t\t\t<yStart units="{self.angular_unit}">{y_start:.{decimal_places}f}</yStart>
\t\t\t<xDelta units="{self.angular_unit}">{x_delta:.{decimal_places}f}</xDelta>
\t\t\t<yDelta units="{self.angular_unit}">{y_delta:.{decimal_places}f}</yDelta>
\t\t\t<pointSlewTime units="{self.time_unit}">{self.point_slew_time:.{decimal_places}f}</pointSlewTime>
\t\t\t<lineSlewTime units="{self.time_unit}">{self.line_slew_time:.{decimal_places}f}</lineSlewTime>
\t\t\t<dwellTime units="{self.time_unit}">{self.dwell_time:.{decimal_places}f}</dwellTime>
\t\t\t<lineAxis>Y</lineAxis>
\t\t\t<keepLineDir>false</keepLineDir>
\t\t</offsetAngles>
\t\t<phaseAngle ref="powerOptimised">
\t\t\t<yDir> false </yDir>
\t\t</phaseAngle>
\t</attitude>
</block>
'''
        return PTR

    def plot(self):
        plt.figure()
        for r in self.rectangles:
            r.plot_to_ax(plt.gca(),'b')
        plt.gca().plot(*zip(*self.center_points),'k')
        plt.gca().plot(*zip(*self.center_points),'rx')

        if self.target_radius is not None:
            circle = plt.Circle((0,0), radius=self.target_radius,
                                color='r', fill=False)
            plt.gca().add_artist(circle)
        if self.target_radius_with_margin is not None:
            circle_margin = plt.Circle((0,0), radius = self.target_radius_with_margin,
                                       color='g', fill=False)
            plt.gca().add_artist(circle_margin)
        try:
            radius_end = DiskMosaic.allowed_angular_units[self.angular_unit] \
                    * get_body_angular_diameter_rad("JUICE", self.target, self.end_time) / 2
            circle_end = plt.Circle((0,0), radius = radius_end,
                                       color='c', fill=False)
            plt.gca().add_artist(circle_end)
        except:
            print("DiskMosaic plotter: Failed to calculate real radius at mosaic end.")
        plt.axis('equal')
        plt.grid()
        plt.xlabel(f'X coordinate [{self.angular_unit}]')
        plt.ylabel(f'Y coordinate [{self.angular_unit}]')
        plt.title(f'Raster mosaic of {self.target} at {self.start_time.isoformat()}')
        plt.show()


if __name__=="__main__":
    fov_size = (1.2, 1.7)
    point_slew_time = 1.75
    line_slew_time = 2.25
    dwell_time = 3.0
    valid_start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")

    dm = DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                    dwell_time, point_slew_time, line_slew_time,
                    (-1.5, 1.5), (1.5, -1.5), (3, 3))
    print(dm.generate_PTR())

    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    dm = DiskMosaic(fov_size, "CALLISTO", valid_start_time, "min", "deg",
                    dwell_time, point_slew_time, line_slew_time,
                    (-1.5, 1.5), (1.5, -1.5), (3, 3))

