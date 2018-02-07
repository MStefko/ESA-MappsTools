# coding=utf-8
from datetime import datetime, timedelta

from matplotlib import pyplot as plt
from typing import Tuple, List

from shapely.geometry import Polygon
import spiceypy as spy
import numpy as np

conversions_from_rad = {"deg": 180/np.pi, "rad": 1.0, "arcMin": 3438, "arcSec": 206265}


class Rectangle:
    """ Simple non-rotatable rectangle which serves as representation of FOV. """

    allowed_modes = {"CENTER", "CORNER"}

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
    def corners(self) -> List[Tuple[float, float]]:
        """ List of rectangle (x,y) corners. """
        return self._corners

    @property
    def polygon(self) -> Polygon:
        """ Shapely polygon representing the rectangle. """
        return self._polygon

    @property
    def center(self) -> Tuple[float, float]:
        """ Center (x,y) coordinates of the rectangle. """
        return self._center

    def plot_to_ax(self, ax: plt.Axes, *args, **kwargs) -> None:
        """ Plots the rectangle to desired axis.

        :param ax: Axis to plot onto.
        :param args: Pyplot args
        :param kwargs: Pyplot kwargs
        """
        x, y = self.polygon.exterior.xy
        ax.plot(x, y, *args, **kwargs)


def datetime2et(time: datetime) -> float:
    return spy.str2et(time.isoformat())


def get_nadir_point_surface_velocity_kps(probe: str, body: str, time: datetime, delta_s: float = 10.0) -> float:
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
    nadir_points = [spy.subpnt("INTERCEPT/ELLIPSOID", body, et, f"IAU_{body}",
                               "LT+S", probe)[0]
                    for et in (start, end)]
    distance = spy.vdist(*nadir_points)
    return distance / delta_s


def get_pixel_size_km(probe: str, body: str, time: datetime,
                      fov_full_angle_deg: float, fov_full_px: int) -> float:
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
    nadir_vec = spy.subpnt("INTERCEPT/ELLIPSOID", body, et, f"IAU_{body}",
                            "LT+S", probe)[2]
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


def get_body_angular_diameter_rad(probe: str, body: str, time: datetime) -> float:
    """ Calculates angular diameter of given body as viewed from probe at given time

    :param probe: SPICE name of probe
    :param body: SPICE name of target body
    :param time: datetime of computation
    :return: Angular diameter of body in radians
    """
    et = datetime2et(time)
    limb_points = spy.limbpt("TANGENT/ELLIPSOID", body, et, f"IAU_{body}", "LT+S",
                             "CENTER", probe, (0.0, 0.0, 1.0), np.pi, 2, 1.0, 1.0, 10)
    # output sanity check
    if any([npts != 1 for npts in limb_points[0]]):
        raise RuntimeError("Unable to determine limb vectors for determining angular size of target.")
    limb_vectors = limb_points[3]
    return spy.vsep(*limb_vectors)


def get_illuminated_shape(probe: str, body: str, time: datetime, angular_unit: str) -> Polygon:
    """ Calculates the shape of sun-illuminated part of SPICE body as viewed from a probe.

    :param probe: Name of probe, e.g. "JUICE"
    :param body: Name of body, e.g. "CALLISTO"
    :param time: Time of observation
    :param angular_unit: Angular unit, one of ["deg", "rad", "arcMin", "arcSec"]
    :return: Polygon marking the illuminated part of body as viewed from probe, centered on the nadir
             point. The x-direction points towards the Sun.
    """
    if angular_unit not in conversions_from_rad:
        raise ValueError(f"Unknown angular_unit: '{angular_unit}'. Allowed units: {conversions_from_rad.keys()}")

    et = datetime2et(time)
    ncuts = 20

    # we need to compute our own coordinate system, where +z is the probe->body vector,
    # the Sun lies in the x-z plane, with +x direction towards the Sun
    # this coordinate system is left-handed (from view of probe, +z points into the screen,
    # +x points right, and +y points up)
    sun_position_from_probe = spy.spkpos("SUN", et, f"IAU_{body}", "LT+S", probe)[0]
    body_position_from_probe = spy.spkpos(body, et, f"IAU_{body}", "LT+S", probe)[0]

    # we only need to know the orientations os x-z and y-z planes, we don't care about point of origin
    x_z_plane_normal_vector = spy.vcrss(sun_position_from_probe, body_position_from_probe)
    y_z_plane_normal_vector = spy.vcrss(body_position_from_probe, x_z_plane_normal_vector)

    # the illuminated side of limb in our coordinate system is always on the right side, so we start
    # with +y direction (x_z_plane_normal_vector), and rotate clockwise for 180 degrees
    step_limb = - np.pi/ncuts
    limb_points = spy.limbpt("TANGENT/ELLIPSOID", body, et, f"IAU_{body}", "LT+S",
                             "CENTER", probe, x_z_plane_normal_vector, step_limb, ncuts, 1.0, 1.0, ncuts)[3]
    assert(len(limb_points==ncuts))

    # if we preserve the upwards direction of y axis, but look at the body from POV of the Sun,
    # the probe will always be on the left side. That means we start slicing again at +y direction,
    # but this time rotate counter-clockwise for 180 degrees, to get terminator points that are
    # actually visible from probe
    step_terminator = np.pi/ncuts
    terminator_points = spy.termpt("UMBRAL/TANGENT/ELLIPSOID", "SUN", body, et, f"IAU_{body}", "LT+S",
                                   "CENTER", probe, x_z_plane_normal_vector, step_terminator, ncuts, 1.0, 1.0, ncuts)[3]
    assert(len(terminator_points<=ncuts))

    # reverse the order of terminator points so we go
    # (limb top -> ... -> limb bottom -> terminator bottom -> ... -> terminator top)
    # these vectors emanate from probe towards the body limb and terminator
    points_3d = list(limb_points) + list(reversed(terminator_points))

    # convert the points to appropriate units from radians
    conversion_factor = conversions_from_rad[angular_unit]
    # project the points from IAU body-fixed 3d frame, to our probe POV 2d frame
    points_2d = []
    for p in points_3d:
        # x-coordinate of each point is the angle vector with the y-z plane (this also recognizes the sign)
        x_rad = np.arcsin(spy.vdot(y_z_plane_normal_vector, p)/(spy.vnorm(y_z_plane_normal_vector)*spy.vnorm(p)))
        # similarly, y-coordinate is angle with x-z plane
        y_rad = np.arcsin(spy.vdot(x_z_plane_normal_vector, p)/(spy.vnorm(x_z_plane_normal_vector)*spy.vnorm(p)))
        # convert the angular coordinate from radians to desired unit, and add to list
        points_2d.append((x_rad * conversion_factor, y_rad * conversion_factor))
    return Polygon(points_2d)


if __name__=="__main__":
    r = Rectangle( (0.0, 0.0), (1.0, 3.0))
    print(f"Corners: {r.corners}")
    print(f"Polygon: {r.polygon}")
    print(f"Center: {r.center}")

    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2031-04-25T18:40:47", "%Y-%m-%dT%H:%M:%S")

    poly = get_illuminated_shape("JUICE", "CALLISTO", start_time, "deg")
    from matplotlib import pyplot as plt
    plt.plot(*poly.exterior.xy)
    plt.axis('equal')
    plt.show()


