# coding=utf-8
from datetime import datetime

import numpy as np

from mosaics.Scan import Scan
from mosaics.DiskMosaicGenerator import DiskMosaicGenerator
from mosaics.misc import get_body_angular_diameter_rad, get_illuminated_shape
from mosaics.units import time_units, angular_units, convertTimeFromTo, convertAngleFromTo

_optimize_steps_centered = DiskMosaicGenerator._optimize_steps_centered


class ScanGenerator:
    """ Generator for Scans. """
    def __init__(self, fov_width: float,
                 probe: str, target: str,
                 start_time: datetime,
                 time_unit: str, angular_unit: str,
                 measurement_slew_rate: float,
                 transfer_slew_rate: float):
        """ Create a ScanGenerator

        :param fov_width: width of FOV along x-axis
        :param probe: SPICE name of probe, e.g. "JUICE"
        :param target: SPICE name of target body, e.g. "CALLISTO"
        :param start_time: Time of beginning of mosaic
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        :param measurement_slew_rate: Slew rate during scanning measurement - depends on instrument
        :param transfer_slew_rate: Slew rate for transferring in between scans - as high as possible
        """
        if fov_width <= 0.0:
            raise ValueError(f"FOV width must be positive: {fov_width}")
        self.fov_width = fov_width

        self.probe = probe
        self.target = target

        self.start_time = start_time
        if time_unit not in time_units:
            raise ValueError(f"Time unit must be one of following: {time_units}")
        self.time_unit = time_unit
        if angular_unit not in angular_units:
            raise ValueError(f"Angular unit must be one of following: {angular_units}")
        self.angular_unit = angular_unit
        if measurement_slew_rate <= 0.0:
            raise ValueError(f"Measurement slew rate must be positive: {measurement_slew_rate}")
        self.measurement_slew_rate = measurement_slew_rate
        if transfer_slew_rate <= 0.0:
            raise ValueError(f"Transfer slew rate must be positive: {transfer_slew_rate}")
        self.transfer_slew_rate = transfer_slew_rate

        # calculate angular size of target at start time
        self.target_angular_diameter = convertAngleFromTo(get_body_angular_diameter_rad(self.probe, self.target, start_time),
                                                          "rad", self.angular_unit)

    def generate_symmetric_scan(self, margin: float = 0.2, min_overlap: float = 0.1):
        """

        :param margin: Extra area around the target to be covered by the mosaic, in units of diameter
        (value 0.0 corresponds to no extra margin)
        :param min_overlap: Minimal value for overlap of neighboring vertical scans(value of 0.1 means 10% of image
        on either side overlaps with the neighbor)
        :return: Generated Scan
        """
        if margin <= -1.0:
            raise ValueError("margin must be larger than -1.0")
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("min_overlap must be in the interval <0.0, 1.0)")
        diameter_to_cover = (self.target_angular_diameter * (1.0 + margin))
        (no_of_slews, start_x, step_x) = _optimize_steps_centered(diameter_to_cover, self.fov_width, min_overlap)
        start_y = diameter_to_cover / 2
        step_y = - diameter_to_cover
        line_slew_time = step_x / self.transfer_slew_rate
        border_slew_time = convertTimeFromTo(5.0, "min", self.time_unit)
        return Scan(self.fov_width, self.target, self.start_time, self.time_unit, self.angular_unit,
                    self.measurement_slew_rate, line_slew_time, border_slew_time,
                    (start_x, start_y), (step_x, step_y), no_of_slews)

    def generate_sunside_scan(self, margin: float = 0.2, min_overlap: float = 0.1):
        """

        :param margin: Extra area around the target to be covered by the mosaic, in units of diameter
        (value 0.0 corresponds to no extra margin)
        :param min_overlap: Minimal value for overlap of neighboring vertical scans(value of 0.1 means 10% of image
        on either side overlaps with the neighbor)
        :return: Generated Scan
        """
        if margin <= -1.0:
            raise ValueError("margin must be larger than -1.0")
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("min_overlap must be in the interval <0.0, 1.0)")
        diameter_to_cover = (self.target_angular_diameter * (1.0 + margin))
        illuminated_shape = get_illuminated_shape(self.probe, self.target, self.start_time, self.angular_unit)
        x_shape_coords = np.array([c[0] for c in list(illuminated_shape.exterior.coords)])
        shape_width = (max(x_shape_coords) - min(x_shape_coords)) * (1.0 + margin)
        (no_of_slews, start_x, step_x) = _optimize_steps_centered(shape_width, self.fov_width, min_overlap)
        # translate center to center of x_shape
        start_x += (max(x_shape_coords) + min(x_shape_coords)) / 2
        start_y = diameter_to_cover / 2
        step_y = - diameter_to_cover
        line_slew_time = step_x / self.transfer_slew_rate
        border_slew_time = convertTimeFromTo(5.0, "min", self.time_unit)
        return Scan(self.fov_width, self.target, self.start_time, self.time_unit, self.angular_unit,
                    self.measurement_slew_rate, line_slew_time, border_slew_time,
                    (start_x, start_y), (step_x, step_y), no_of_slews)


if __name__ == '__main__':
    import spiceypy as spy

    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2031-09-27T09:50:00", "%Y-%m-%dT%H:%M:%S")
    sg = ScanGenerator(3.4, "JUICE", "CALLISTO", start_time, "min",
                              "deg", 0.00859/(2/60), 0.04 * 60)
    s = sg.generate_symmetric_scan(margin=0.05, min_overlap=0.05)
    print(s.generate_PTR())
    s.plot()
