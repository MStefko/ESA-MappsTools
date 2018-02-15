# coding=utf-8
""" Scan class.

@author: Marcel Stefko
"""
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from typing import List, Tuple

import numpy as np
import spiceypy as spy

from mosaics.DiskMosaic import DiskMosaic
from mosaics.misc import Rectangle, get_body_angular_diameter_rad, get_illuminated_shape


class Scan:
    """ Observation in which a slit oriented along x-axis slews with a certain angular rate in the y direction.

    Number of slew lines is optional. """
    allowed_time_units = {"sec": "seconds", "min": "minutes", "hour": "hours"}
    allowed_angular_units = {"deg": 180 / np.pi, "rad": 1.0, "arcMin": 3438, "arcSec": 206265}

    def __init__(self, fov_width: float,
                 target: str, start_time: datetime,
                 time_unit: str, angular_unit: str,
                 scan_slew_rate: float, line_slew_time: float,
                 border_slew_time: float,
                 start: Tuple[float, float],
                 delta: Tuple[float, float],
                 number_of_lines: int):
        """ Create a scan, where the slit is assumed to be oriented along the x-axis

        :param fov_width: width of slit along x-axis
        :param target: Name of target body, e.g. "CALLISTO"
        :param start_time: Time of beginning of mosaic
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        :param scan_slew_rate: Rate at which the scan should be performed
        :param line_slew_time: Time to get from end of one line to start of another
        :param border_slew_time: Time to get to start of scan, and to return from end of scan
        :param start: 2-tuple (x, y) starting position
        :param delta: 2-tuple (x-line spacing, y-line length)
        :param number_of_lines: number of lines along x-axis
        """
        if fov_width <= 0.0:
            raise ValueError(f"FOV width value must be non-negative: {fov_width}")
        self.fov_width = fov_width
        if not isinstance(target, str):
            raise TypeError("Target must be a string.")
        self.target = target
        if not isinstance(start_time, datetime):
            raise TypeError("Start time must be a datetime object.")
        self.start_time = start_time
        if time_unit not in Scan.allowed_time_units:
            raise ValueError(f"Time unit must be one of following: {Scan.allowed_time_units}")
        self.time_unit = time_unit
        if angular_unit not in Scan.allowed_angular_units:
            raise ValueError(f"Angular unit must be one of following: {Scan.allowed_angular_units}")
        self.angular_unit = angular_unit
        if scan_slew_rate <= 0.0:
            raise ValueError(f"Slew rate of the scan must be positive: {scan_slew_rate}")
        self.scan_slew_rate = scan_slew_rate
        if line_slew_time <= 0.0:
            raise ValueError(f"Line slew time must be positive: {line_slew_time}")
        self.line_slew_time = line_slew_time
        if border_slew_time <= 0.0:
            raise ValueError(f"Border slew time must be positive: {border_slew_time}")
        self.border_slew_time = border_slew_time
        if len(start) != 2 or not all([isinstance(s, float) for s in start]):
            raise TypeError("Start position must be an iterable of length 2")
        self.start = start
        if len(delta) != 2 or not all([isinstance(s, float) for s in delta]):
            raise TypeError("Delta must be an iterable of length 2")
        self.delta = delta
        if number_of_lines < 1 or not isinstance(number_of_lines, int):
            raise ValueError("Number of lines must be a positive integer.")
        self.number_of_lines = number_of_lines

    def _calculate_end_time(self) -> datetime:
        """ Calculates time duration of scan, and thus the earliest end time.

        :return: Earliest possible end time for PTR request
        """
        slew_length = abs(self.delta[1])
        time_per_slew = slew_length / self.scan_slew_rate

        scan_time = 2 * self.border_slew_time + self.number_of_lines * time_per_slew + \
                    (self.number_of_lines - 1) * self.line_slew_time
        # Required delay from start time.
        # 10 seconds required by MAPPS
        initial_delay = timedelta(seconds=10)
        # Required delay after finishing
        final_delay = timedelta(minutes=1)
        # Next line picks the correct keyword argument for timedelta object so that we have
        # correct units. (E.g. if self.time_unit is "min", the keyword argument has to be
        # "minutes").
        timedelta_kwarg = {Scan.allowed_time_units[self.time_unit]: scan_time}
        delay = initial_delay + timedelta(**timedelta_kwarg) + final_delay
        end_time = self.start_time + delay
        return end_time.replace(microsecond=0)

    @property
    def end_time(self) -> datetime:
        """ End time of mosaic. """
        return self._calculate_end_time()

    def _generate_rectangles(self) -> List[Rectangle]:
        """

        :return: List of image Rectangles in order of acquisition
        """
        return [Rectangle(cp, (self.fov_width, self.delta[1])) for cp in self._generate_center_points()]

    def _generate_center_points(self) -> List[Tuple[float, float]]:
        """

        :return: List of (x,y) center points in order of acquisition.
        """
        x_start, y_start = self.start
        x_delta, y_delta = self.delta
        center_points = []
        for x in range(self.number_of_lines):
            center_points.append((x_start + x*x_delta, y_start + y_delta/2))
        return center_points

    @property
    def rectangles(self) -> List[Rectangle]:
        """ List of image Rectangles in order of acquisition """
        return self._generate_rectangles()

    @property
    def center_points(self) -> List[Tuple[float, float]]:
        """ List of (x,y) image center points in order of acquisition. """
        return self._generate_center_points()

    def generate_PTR(self, decimal_places=3) -> str:
        """ Generates a PTR request for MAPPS for this scan

        :param decimal_places: Number of max decimal places for values.
        :return: PTR request string
        """
        x_start, y_start = self.start
        x_delta, y_delta = self.delta
        # compute the scan start_time = 10 seconds + borderSlewTime
        timedelta_kwarg = {Scan.allowed_time_units[self.time_unit]: self.border_slew_time}
        start_time_timedelta = timedelta(seconds=10) + timedelta(**timedelta_kwarg)
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
\t\t<offsetAngles ref="scan">
\t\t\t<startTime>{(self.start_time+start_time_timedelta).isoformat()}</startTime>
\t\t\t<numberOfLines> {self.number_of_lines} </numberOfLines>
\t\t\t<xStart units="{self.angular_unit}">{-x_start:.{decimal_places}f}</xStart>
\t\t\t<yStart units="{self.angular_unit}">{y_start:.{decimal_places}f}</yStart>
\t\t\t<lineDelta units="{self.angular_unit}">{-x_delta:.{decimal_places}f}</lineDelta>
\t\t\t<scanDelta units="{self.angular_unit}">{y_delta:.{decimal_places}f}</scanDelta>
\t\t\t<scanSpeed units="{self.angular_unit}/{self.time_unit}">{self.scan_slew_rate:.{decimal_places}f}</scanSpeed>
\t\t\t<scanSlewTime units="{self.time_unit}">1.0</scanSlewTime>
\t\t\t<lineSlewTime units="{self.time_unit}">{self.line_slew_time:.{decimal_places}f}</lineSlewTime>
\t\t\t<borderSlewTime units="{self.time_unit}">{self.border_slew_time:.{decimal_places}f}</borderSlewTime>
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

    def plot(self, query_spice: bool = True):
        """ Shows generated scan diagram. """
        plt.figure()
        # plot rectangles
        for r in self.rectangles:
            r.plot_to_ax(plt.gca(), 'b')
        # plot slew trajectory
        traj_points = []
        x_delta, y_delta = self.delta
        for i, cp in enumerate(self.center_points):
            tps = [(cp[0], cp[1] - y_delta/2),
                   (cp[0], cp[1] + y_delta/2)]
            if i%2:
                tps = list(reversed(tps))
            traj_points += tps
        plt.gca().plot(*zip(*traj_points), 'k', linewidth=2, linestyle='dashed')
        plt.gca().plot(*zip(*traj_points), 'rx')
        if query_spice:
            radius_start = DiskMosaic.allowed_angular_units[self.angular_unit] \
                           * get_body_angular_diameter_rad("JUICE", self.target, self.start_time) / 2
            circle_start = plt.Circle((0, 0), radius=radius_start,
                                      color='#FF0000', fill=False, linewidth=2)
            plt.gca().add_artist(circle_start)

            radius_end = DiskMosaic.allowed_angular_units[self.angular_unit] \
                * get_body_angular_diameter_rad("JUICE", self.target, self.end_time) / 2
            circle_end = plt.Circle((0, 0), radius=radius_end,
                                    color='#A00000', fill=False, linewidth=2, linestyle='-.')
            plt.gca().add_artist(circle_end)

            illuminated_shape_start = get_illuminated_shape("JUICE", self.target, self.start_time, self.angular_unit)
            plt.gca().plot(*illuminated_shape_start.exterior.xy, '#CCCC00')

            illuminated_shape_end = get_illuminated_shape("JUICE", self.target, self.end_time, self.angular_unit)
            plt.gca().plot(*illuminated_shape_end.exterior.xy, color='#999900', linestyle='-.')
        plt.axis('equal')
        plt.grid()
        plt.xlabel(f'X coordinate [{self.angular_unit}]')
        plt.ylabel(f'Y coordinate [{self.angular_unit}]')
        plt.title(f'Mosaic of {self.target} at {self.start_time.isoformat()}')
        plt.show()

if __name__ == "__main__":
    fov_width = 3.4
    valid_start_time = datetime.strptime("2031-09-27T09:40:00", "%Y-%m-%dT%H:%M:%S")

    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    s = Scan(fov_width, "CALLISTO", valid_start_time, "min", "deg",
             0.00859/(2/60), 5, 5, (-1.5, 3.3), (0.9*fov_width, -6.5), 2)
    print(s.generate_PTR())
    s.plot()