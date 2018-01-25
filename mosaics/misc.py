# coding=utf-8
from datetime import datetime, timedelta

from matplotlib import pyplot as plt
from typing import Tuple

from shapely.geometry import Polygon
import spiceypy as spy
import numpy as np


class Rectangle:
    allowed_modes = {"CENTER", "CORNER"}
    """ Simple rectangle which serves as representation of FOV."""
    def __init__(self, point: Tuple[float, float],
                 lengths: Tuple[float, float], mode: str = "CENTER"):
        if mode not in Rectangle.allowed_modes:
            raise ValueError(f"Unrecognised mode: {mode}")
        if len(point) != 2:
            raise ValueError(f"Point needs to be a tuple of length 2.")
        if len(lengths) != 2:
            raise ValueError(f"Lengths needs to be a tuple of length 2.")
        if mode == "CENTER":
            x_center, y_center = point
            dx = lengths[0]/2
            dy = lengths[1]/2
            self._corners = [(x_center-dx, y_center-dy), (x_center-dx, y_center+dy),
                      (x_center+dx, y_center+dy), (x_center+dx, y_center-dy)]
            self._polygon = Polygon(self._corners)
            self._center = point
        elif mode == "CORNER":
            x_edge, y_edge = point
            dx, dy = lengths
            self._corners = [(x_edge, y_edge), (x_edge, y_edge+dy),
                      (x_edge+dx, y_edge+dy), (x_edge+dx, y_edge)]
            self._polygon = Polygon(self._corners)
            self._center = (x_edge + dx/2, y_edge + dx/2)

    def __str__(self):
        return f"Rectangle: {self.corners} "

    @property
    def corners(self):
        return self._corners

    @property
    def polygon(self):
        return self._polygon

    @property
    def center(self):
        return self._center

    def plot_to_ax(self, ax: plt.Axes, *args, **kwargs):
        x, y = self.polygon.exterior.xy
        ax.plot(x, y, *args, **kwargs)

def datetime2et(time: datetime) -> float:
    return spy.str2et(time.isoformat())


def get_nadir_point_surface_velocity_kps(probe: str, body: str, time: datetime, delta_s: float = 10.0):
    """ Computes surface velocity of nadir point of given probe at given time on given body.

    :param probe: SPICE name of probe
    :param body: SPICE name of target body
    :param time: datetime of computation
    :param delta_s: delta time used for computation of derivative
    :return: Velocity of nadir point across surface [km/s]
    """
    if delta_s <= 0.0:
        raise ValueError("delta_s must be positive.")
    start = datetime2et(time)
    end = datetime2et(time + timedelta(seconds=delta_s))
    nadir_points = [spy.sincpt("ELLIPSOID", body, et, f"IAU_{body}",
                               "LT+S", probe, probe, (0.0, 0.0, 1.0))[0]
                    for et in (start, end)]
    distance = spy.vdist(*nadir_points)
    return distance / delta_s


def get_pixel_size_km(probe: str, body: str, time: datetime,
                      fov_full_angle_deg: float, fov_full_px: int):
    """ Calculates size of one pixel on body's surface in km at given time.

    :param probe: SPICE name of probe
    :param body: SPICE name of target body
    :param time: datetime of computation
    :param fov_full_angle_deg: full angle of one FOV dimension
    :param fov_full_px: full pixel count of the same FOV dimension
    :return: length of square covered by one pixel in kilometers
    """
    if fov_full_angle_deg <= 0.0:
        raise ValueError("fov_full_angle_deg must be positive.")
    if fov_full_angle_deg > 90.0:
        raise ValueError(f"with fov_full_angle_deg = {fov_full_angle_deg} the calculation would be wildly inaccurate.")
    if fov_full_px < 1:
        raise ValueError("fov_full_px must be at least 1")

    et = datetime2et(time)
    nadir_vec = spy.sincpt("ELLIPSOID", body, et, f"IAU_{body}",
                            "LT+S", probe, probe, (0.0, 0.0, 1.0))[2]
    nadir_dist = spy.vnorm(nadir_vec)
    half_angle_rad = 0.5 * fov_full_angle_deg * np.pi / 180
    fov_half_px = fov_full_px / 2
    half_angle_km = np.tan(half_angle_rad) * nadir_dist
    return half_angle_km / fov_half_px


def get_max_dwell_time_s(max_smear: float, probe: str, body: str,
                         time: datetime, fov_full_angle_deg: float,
                         fov_full_px: int) -> float:
    """ Calculates the maximal dwell time in seconds based on the
    fov paramaters, spacecraft distance from surface, and velocity
    of nadir point.

    :param max_smear: Maximal smear distance in unit of pixels
    :param probe: SPICE name of probe
    :param body: SPICE name of target body
    :param time: datetime of computation
    :param fov_full_angle_deg: full angle of one FOV dimension
    :param fov_full_px: full pixel count of the same FOV dimension
    :return: Maximal possible dwell time in seconds
    """
    if max_smear<=0.0:
        raise ValueError("max_smear must be positive")
    pixel_size_km = get_pixel_size_km(probe, body, time, fov_full_angle_deg, fov_full_px)
    nadir_velocity_kps = get_nadir_point_surface_velocity_kps(probe, body, time)
    smear_per_second = nadir_velocity_kps / pixel_size_km
    return max_smear / smear_per_second


if __name__=="__main__":
    r = Rectangle( (0.0, 0.0), (1.0, 3.0))
    print(f"Corners: {r.corners}")
    print(f"Polygon: {r.polygon}")
    print(f"Center: {r.center}")



