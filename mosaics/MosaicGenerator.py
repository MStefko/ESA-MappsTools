# coding=utf-8
from datetime import datetime
from typing import Tuple, List

import numpy as np

from mosaics.CustomMosaic import CustomMosaic
from mosaics.DiskMosaic import DiskMosaic
from mosaics.misc import get_body_angular_diameter_rad, get_illuminated_shape, Rectangle
from mosaics.tsp_solver import solve_tsp
from mosaics.units import angular_units, time_units, convertAngleFromTo


class MosaicGenerator:
    """ Generator for DiskMosaics and CustomMosaics. Contains two public methods:

    - MosaicGenerator.generate_symmetric_mosaic(): Creates a symmetric full-disk "raster" mosaic.

    - MosaicGenerator.generate_sunside_mosaic(): Creates a "custom" mosaic that images the sun-illuminated
    side of the body.
    """
    def __init__(self, fov_size: Tuple[float, float],
                 probe: str, target: str,
                 start_time: datetime,
                 time_unit: str, angular_unit: str,
                 dwell_time: float,
                 slew_rate: float):
        """ Create a MosaicGenerator

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
        if time_unit not in time_units:
            raise ValueError(f"Time unit must be one of following: {time_units}")
        self.time_unit = time_unit
        if angular_unit not in angular_units:
            raise ValueError(f"Angular unit must be one of following: {angular_units}")
        self.angular_unit = angular_unit
        if dwell_time < 0.0:
            raise ValueError(f"Dwell time must be non-negative: {dwell_time}")
        self.dwell_time = dwell_time
        if slew_rate <= 0.0:
            raise ValueError(f"Slew rate must be positive: {slew_rate}")
        self.slew_rate = slew_rate

        # calculate angular size of target at start time
        self.target_angular_diameter = convertAngleFromTo(get_body_angular_diameter_rad(self.probe, self.target, start_time),
                                                          "rad", self.angular_unit)

    def generate_symmetric_mosaic(self, margin: float = 0.2, min_overlap: float = 0.1) -> DiskMosaic:
        """ Generate a full-body "raster" observation that is symmetric along both the x and y axis.
        The number of tiles of this mosaic is optimized according to input parameters., so that the
        disk is covered evenly using the lowest number of tiles possible.

        :param margin: Extra area around the target to be covered by the mosaic, in units of diameter
        (value 0.0 corresponds to no extra margin)
        :param min_overlap: Minimal value for overlap of neighboring images (value of 0.1 means 10% of image
        on either side overlaps with the neighbor). Resulting overlap can be higher, if it is allowed
        by size of target (however, this is never at the cost of needing more tiles to cover the image).
        :return: Generated DiskMosaic
        """
        if margin <= -1.0:
            raise ValueError("margin must be larger than -1.0")
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("min_overlap must be in the interval <0.0, 1.0)")
        diameter_to_cover = (self.target_angular_diameter * (1.0 + margin))
        (points, starts, steps) = zip(*[self._optimize_steps_centered(
            diameter_to_cover, fov_width, min_overlap) for fov_width in self.fov_size])
        # Calculate slew time, slew through lines along x axis, through points along y axis
        line_slew_time, point_slew_time = tuple(abs(step / self.slew_rate) for step in steps)
        return DiskMosaic(self.fov_size, self.target, self.start_time, self.time_unit, self.angular_unit,
                          self.dwell_time, point_slew_time, line_slew_time, starts, steps, points)

    def generate_sunside_mosaic(self, margin: float = 0.5, min_overlap: float = 0.1) -> CustomMosaic:
        """ Generate a "custom" observation that images the sun-illuminated part of the body visible
        from the spacecraft. Number of tiles in x and y directions on a rectangular grid is
        optimized for the illuminated shape. Tiles on this rectangular grid that don't contain any
        visible part of body are skipped (usually in corners).

        :param margin: Extra area around the target to be covered by the mosaic, in units of diameter
        (value 0.0 corresponds to no extra margin)
        :param min_overlap: Minimal value for overlap of neighboring images (value of 0.1 means 10% of image
        on either side overlaps with the neighbor)
        :return: Generated CustomMosaic
        """
        if margin <= -1.0:
            raise ValueError("margin must be larger than -1.0")
        if min_overlap < 0.0 or min_overlap >= 1.0:
            raise ValueError("min_overlap must be in the interval <0.0, 1.0)")
        vertical_diameter_to_cover = (self.target_angular_diameter * (1.0 + margin))
        points_y, start_y, step_y = self._optimize_steps_centered(
            vertical_diameter_to_cover, self.fov_size[1], min_overlap)
        illuminated_shape = get_illuminated_shape(self.probe, self.target, self.start_time, self.angular_unit)
        x_shape_coords = np.array([c[0] for c in list(illuminated_shape.exterior.coords)])
        shape_width = (max(x_shape_coords) - min(x_shape_coords)) * (1.0 + margin)
        points_x, start_x, step_x = self._optimize_steps_centered(shape_width, self.fov_size[0], min_overlap)
        # translate center to center of x_shape
        start_x += (max(x_shape_coords) + min(x_shape_coords)) / 2

        rectangles = self._generate_grid_rectangles((points_x, points_y), (start_x, start_y), (step_x, step_y))
        center_points = [r.center for r in rectangles if r.polygon.overlaps(illuminated_shape)
                                                      or illuminated_shape.contains(r.polygon)]

        # solve Traveling Salesman Problem for the center points
        sorted_center_points = self._optimize_center_points_tsp(center_points)

        return CustomMosaic(self.fov_size, self.target, self.start_time, self.time_unit, self.angular_unit,
                            self.dwell_time, 1.0/self.slew_rate, sorted_center_points)

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
            no_of_steps = int(
                np.math.ceil((diameter_to_cover - fov_width) / effective_fov - 0.00001))  # rounding error hack
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

    def _generate_grid_rectangles(self, no_points: Tuple[int, int], starts: Tuple[float, float], steps: Tuple[float, float])\
            -> List[Rectangle]:
        """ Generates a rectangular grid of Rectangles based on number of points, start and step
        in each direction.

        :param no_points: Number of points (x, y)
        :param starts: Start coordinate (x, y)
        :param steps: Step for each point (x, y)
        :return: List of Rectangles
        """
        result = []
        for nx in range(no_points[0]):
            line = []
            for ny in range(no_points[1]):
                line.append(Rectangle((starts[0] + nx*steps[0], starts[1] + ny*steps[1]),
                                      self.fov_size))
            if nx % 2 == 1:
                line = list(reversed(line))
            result += line
        return result

    @staticmethod
    def _optimize_center_points_tsp(center_points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """ Solves the traveling salesman problem for given list of points using euclidean distances.

        :param center_points: List of 2d (x,y) points to reorder
        :return: Reordered list of points
        """
        distances = []
        for i, p in enumerate(center_points[:]):
            distances.append([])
            for j, q in enumerate(center_points[:]):
                distances[i].append(np.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2))
        indices = solve_tsp(distances, optim_steps=10)
        return [center_points[i] for i in indices]


if __name__ == '__main__':
    import spiceypy as spy

    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2031-04-25T19:40:47", "%Y-%m-%dT%H:%M:%S")
    dmg = MosaicGenerator((1.72, 1.29), "JUICE", "CALLISTO", start_time, "min",
                              "deg", 2.0, 0.04 * 60)
    dm = dmg.generate_symmetric_mosaic(margin=0.1)
    print(dm.generate_PTR())
    dm.plot()
