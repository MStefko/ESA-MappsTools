# coding=utf-8
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import spiceypy as spy

from mosaics.misc import Rectangle, datetime2et

class CustomMosaic:
    allowed_time_units = {"sec": "seconds", "min": "minutes", "hour": "hours"}
    allowed_angular_units = {"deg": 180/np.pi, "rad": 1.0, "arcMin": 3438, "arcSec": 206265}

    def __init__(self, fov_size: Tuple[float, float],
                 target: str, start_time: datetime,
                 time_unit: str, angular_unit: str,
                 dwell_time: float,
                 slew_time_per_unit_angle: float,
                 center_points: List[Tuple[float, float]],
                 target_radius = None,
                 target_radius_with_margin = None):
        """ Create a CustomMosaic


        :param fov_size: 2-tuple (x, y) containing rectangular FOV size
        :param target: Name of target body, e.g. "CALLISTO"
        :param start_time: Time of beginning of mosaic
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        :param dwell_time: Dwell time at each mosaic point
        :param slew_time_per_unit_angle: Speed at which the spacecraft can slew between points, accounting
            for acceleration and deceleration
        :param center_points: List of points at which to center images.
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
        if time_unit not in CustomMosaic.allowed_time_units:
            raise ValueError(f"Time unit must be one of following: {CustomMosaic.allowed_time_units}")
        self.time_unit = time_unit
        if angular_unit not in CustomMosaic.allowed_angular_units:
            raise ValueError(f"Angular unit must be one of following: {CustomMosaic.allowed_angular_units}")
        self.angular_unit = angular_unit
        if dwell_time < 0.0:
            raise ValueError(f"Dwell time must be non-negative: {dwell_time}")
        self.dwell_time = dwell_time
        if slew_time_per_unit_angle <= 0.0:
            raise ValueError(f"Slew time / angle must be positive: {slew_time_per_unit_angle}")
        self.slew_time_per_angle = slew_time_per_unit_angle

        if len(center_points)<1:
            raise ValueError("At least one point required.")
        for cp in center_points:
            if len(cp) != 2:
                raise TypeError("Center points must be iterables of length 2.")
        self._center_points = center_points

        self.target_radius = target_radius
        self.target_radius_with_margin = target_radius_with_margin

    def _calculate_slew_to_next_point(self, point_no: int):
        if not isinstance(point_no, int):
            raise TypeError("point_no must be an int")
        if point_no >= len(self.center_points)-1 or point_no < 0:
            raise ValueError("Invalid point_no")
        distance_sq = sum((x-y)**2 for (x,y) in
                          zip(self.center_points[point_no], self.center_points[point_no + 1]))
        return np.sqrt(distance_sq) * self.slew_time_per_angle

    def _generate_rectangles(self):
        """

                :return: List of image Rectangles in order of acquisition
                """
        return [Rectangle(cp, self.fov_size) for cp in self.center_points]

    @property
    def rectangles(self) -> List[Rectangle]:
        return self._generate_rectangles()

    @property
    def center_points(self) -> List[Tuple[float, float]]:
        return self._center_points

    def _calculate_end_time(self) -> datetime:
        """ Calculates time duration of mosaic, and thus the earliest end time.

        :return: Earliest possible end time for PTR request
        """
        slew_times = [self._calculate_slew_to_next_point(i) for i in range(len(self.center_points) - 1)]
        slew_time = sum(slew_times)
        dwell_time = self.dwell_time * len(self.center_points)
        # Required delay from start time.
        initial_delay = timedelta(minutes=1)
        # Required delay after finishing
        final_delay = timedelta(minutes=1)
        # Next line picks the correct keyword argument for timedelta object so that we have
        # correct units. (E.g. if self.time_unit is "min", the keyword argument has to be
        # "minutes").
        timedelta_kwarg = {CustomMosaic.allowed_time_units[self.time_unit]: slew_time + dwell_time}
        delay = initial_delay + timedelta(**timedelta_kwarg) + final_delay
        end_time = self.start_time + delay
        return end_time


    def generate_PTR(self, decimal_places = 3) -> str:
        """ Generates a PTR request for MAPPS for this mosaic

        :param decimal_places: Number of max decimal places for values.
        :return: PTR request string
        """
        slew_times = [self._calculate_slew_to_next_point(i) for i in range(len(self.center_points)-1)]
        # max nondecimal digits not including minus sign
        mnd = max([(len(f"{t:.0f}")) for t in (self.dwell_time, max(slew_times))])

        # one extra for decimal point and one for sign
        f_length = mnd + decimal_places + 2
        deltaTimes = f"<deltaTimes units='{self.time_unit}'> "
        for slew_time in slew_times:
            deltaTimes += f" {self.dwell_time*0.5: {f_length}.{decimal_places}}" + \
                          f" {self.dwell_time*0.5: {f_length}.{decimal_places}}" + \
                          f" {slew_time: {f_length}.{decimal_places}}"
        deltaTimes += f" {self.dwell_time*0.5: {f_length}.{decimal_places}}" + \
                      f" {self.dwell_time*0.5: {f_length}.{decimal_places}}" + \
                      f" {0.0: {f_length}.{decimal_places}}"
        deltaTimes += " </deltaTimes>"

        xAngles =    f"<xAngles units='{self.angular_unit}'>    " + \
                     "".join([3*f" {cp[0]: {f_length}.{decimal_places}}" for cp in self.center_points]) + \
                     " </xAngles>"

        xRates =     "<xRates units='deg/min'> " + f" {0.0:{f_length}.{decimal_places}}"*3*len(self.center_points) + " </xRates>"

        yAngles =    f"<yAngles units='{self.angular_unit}'>    " + \
                     "".join([3*f" {cp[1]: {f_length}.{decimal_places}}" for cp in self.center_points]) + \
                     " </yAngles>"

        yRates =     "<yRates units='deg/min'> " + f" {0.0: {f_length}.{decimal_places}}"*3*len(self.center_points) + " </yRates>"

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
\t\t<offsetAngles ref="custom">
\t\t\t<startTime>{(self.start_time+timedelta(minutes=1)).isoformat()}</startTime>
\t\t\t{deltaTimes}
\t\t\t{xAngles}
\t\t\t{xRates}
\t\t\t{yAngles}
\t\t\t{yRates}
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
        plt.axis('equal')
        plt.grid()
        plt.xlabel(f'X coordinate [{self.angular_unit}]')
        plt.ylabel(f'Y coordinate [{self.angular_unit}]')
        plt.title(f'Custom mosaic of {self.target} at {self.start_time.isoformat()}')
        plt.show()



if __name__=='__main__':
    start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")
    angles = [(-0.40000000000000002, -3.4830000000000001), (-0.40000000000000002, -2.4510000000000001), (-0.40000000000000002, -1.419), (-0.40000000000000002, -0.38700000000000001), (-0.40000000000000002, 0.64500000000000002), (-0.40000000000000002, 1.677), (-0.40000000000000002, 2.7090000000000001), (-0.40000000000000002, 3.7410000000000001), (0.97600000000000009, 3.7410000000000001), (0.97600000000000009, 2.7090000000000001), (0.97600000000000009, 1.677), (0.97600000000000009, 0.64500000000000002), (0.97600000000000009, -0.38700000000000001), (0.97600000000000009, -1.419), (0.97600000000000009, -2.4510000000000001), (0.97600000000000009, -3.4830000000000001), (2.3520000000000003, -3.4830000000000001), (2.3520000000000003, -2.4510000000000001), (2.3520000000000003, -1.419), (2.3520000000000003, -0.38700000000000001), (2.3520000000000003, 0.64500000000000002), (2.3520000000000003, 1.677), (2.3520000000000003, 2.7090000000000001), (2.3520000000000003, 3.7410000000000001), (3.7280000000000006, 2.7090000000000001), (3.7280000000000006, 1.677), (3.7280000000000006, 0.64500000000000002), (3.7280000000000006, -0.38700000000000001), (3.7280000000000006, -1.419), (3.7280000000000006, -2.4510000000000001)]

    cm = CustomMosaic((1.72, 1.29), "CALLISTO", start_time, "min",
                      "deg", 0.5, 0.312634, angles)
    print(cm.generate_PTR(decimal_places=5))
