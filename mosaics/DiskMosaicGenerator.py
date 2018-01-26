from datetime import datetime
from typing import Tuple

import numpy as np
import spiceypy as spy

from mosaics.DiskMosaic import DiskMosaic
from mosaics.misc import get_body_angular_diameter_rad


class DiskMosaicGenerator:
    def __init__(self, fov_size: Tuple[float, float],
                 probe: str, target: str,
                 start_time: datetime,
                 time_unit: str, angular_unit: str,
                 dwell_time: float,
                 slew_rate: float):
        """ Create a DiskMosaicGenerator

        :param fov_size: 2-tuple (x, y) containing rectangular FOV size
        :param probe: SPICE name of probe, e.g. "JUICE"
        :param target: SPICE name of target body, e.g. "CALLISTO"
        :param start_time: Time of beginning of mosaic
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        :param dwell_time: Dwell time at each mosaic point
        :param slew_rate: Rate of slew of spacecraft in units specified
        """
        if any([x < 0.0 for x in fov_size]):
            raise ValueError(f"FOV size values must be non-negative: {fov_size}")
        self.fov_size = fov_size

        self.probe = probe
        self.target = target

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
        if slew_rate <= 0.0:
            raise ValueError(f"Slew rate must be positive: {slew_rate}")
        self.slew_rate = slew_rate

        #calculate angular size of target at start time
        self.target_angular_diameter = get_body_angular_diameter_rad(self.probe, self.target, start_time) \
                                       * DiskMosaic.allowed_angular_units[self.angular_unit]

    def generate_symmetric_mosaic(self, margin: float = 0.2, min_overlap: float = 0.1):
        """

        :param margin: Extra area around the target to be covered by the mosaic, in units of diameter
        (value 0.0 corresponds to no extra margin)
        :param min_overlap: Minimal value for overlap of neighboring images (value of 0.1 means 10% of image
        on either side overlaps with the neighbor)
        :return: Generated DiskMosaic
        """
        if margin <= -1.0:
            raise ValueError("margin must be larger than -1.0")
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("min_overlap must be in the interval <0.0, 1.0)")
        # TODO: Unit test this important function using a mock object
        diameter_to_cover = (self.target_angular_diameter * (1.0 + margin))
        (points, starts, steps) = zip(*[self._optimize_steps_centered(
            diameter_to_cover, fov_width, min_overlap) for fov_width in self.fov_size])
        # Calculate slew time, slew through lines along x axis, through points along y axis
        line_slew_time, point_slew_time = tuple(abs(step / self.slew_rate) for step in steps)
        return DiskMosaic(self.fov_size, self.target, self.start_time, self.time_unit, self.angular_unit,
                          self.dwell_time, point_slew_time, line_slew_time, starts, steps, points,
                          target_radius=self.target_angular_diameter/2,
                          target_radius_with_margin=diameter_to_cover/2)

    @staticmethod
    def _optimize_steps_centered(diameter_to_cover: float, fov_width: float, min_overlap: float) \
            -> Tuple[int, float, float]:
        """ Working in 1 dimension, determines where to place centers of images so that
        the overlap requirements are satisfied. Basically determines what is the optimal
        spacing between points required so that the whole diameter is covered in as few
        steps possible, while fulfilling overlap requirements, and not wasting space at
        the edges.

        :param diameter_to_cover: Length along one axis to be covered by FOV
        :param fov_width: FOV length along that axis
        :param min_overlap: Minimal overlap between neighboring frames
        :return: (no_of_points, start_position, step_size)
        """
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("Overlap must be between 0.0 and 1.0.")
        # case when only one image is needed
        if diameter_to_cover <= fov_width:
            return (1, 0.0, 1.0)
        else:
            effective_fov = fov_width * (1 - min_overlap)
            no_of_steps = int(np.math.ceil((diameter_to_cover - fov_width) / effective_fov - 0.00001)) # rounding error hack
            # case of odd amount of steps, we have even amount of points
            if no_of_steps % 2 == 1:
                first_img_loc = (-diameter_to_cover / 2) + 0.5 * fov_width
                last_img_loc = -first_img_loc
                step_size = (last_img_loc - first_img_loc) / no_of_steps
                return (no_of_steps + 1, first_img_loc, step_size)
            # even amount of steps, so an odd amount of points - one point is guaranteed at 0.0
            else:
                edge_img_loc = (-diameter_to_cover / 2) + 0.5 * fov_width
                center_img_loc = 0.0
                step_size = (center_img_loc - edge_img_loc) / (no_of_steps / 2)
                return (no_of_steps + 1, edge_img_loc, step_size)

if __name__=='__main__':
    start_time = datetime.strptime("2031-04-25T19:40:47", "%Y-%m-%dT%H:%M:%S")
    rmg = DiskMosaicGenerator((1.72, 1.29), "JUICE", "CALLISTO", start_time, "min",
                              "deg", 2.0, 0.04*60)
    rm = rmg.generate_symmetric_mosaic(margin=0.1)
    print(rm.generate_PTR())
    rm.plot()