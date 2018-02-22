# -*- coding: utf-8 -*-
""" Tools for analyzing various properties of flybys such as surface coverage, resolution,
altitude, etc.

@author: Marcel Stefko
"""
import os
import sys

import spiceypy as spy
print(spy.tkvrsn('TOOLKIT'))
from spiceypy.utils.support_types import SpiceyError

import numpy as np
print("Numpy version:", np.__version__)

import pandas as pd

from shapely.geometry import Polygon, LineString, Point
from shapely.geometry import MultiPolygon
from shapely.ops import cascaded_union

from matplotlib import pyplot as plt
plt.rcParams["figure.figsize"] = (12,9)
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
from mpl_toolkits.basemap import Basemap

CALLISTO_RADIUS = 2410.3
CALLISTO_AREA = 4 * np.pi * CALLISTO_RADIUS**2
EUROPA_RADIUS = 1560.8
EUROPA_AREA = 4 * np.pi * EUROPA_RADIUS**2

class Flyby:
    def __init__(self, body: str, approximate_et: float, max_altitude: float,
                 step: float = 1.0, count: int = 1000, max_time: float = 3600 * 24 * 2, name: str = None):
        """ This monster class computes all characteristics of a flyby.
        Parameters:
            body: name of moon
            approximate_et: approximate ephemeris time of CA [s]
            max_altitude: height cutoff for flyby [km]
            step: time step of GF SPICE functions [s]
            count: number of logarithmically-spaced sampling points from CA to cutoff [-]
            max_time: edges of search interval around approximate_et [s]
            name: arbitrary name of flyby
        """
        self.name = name if (name is not None) else spy.timout(approximate_et, "YYYY MON DD")
        print("Analyzing flyby {}...".format(self.name))
        self.step = step
        self.count = count
        # store parameters
        self.probe = "JUICE"
        self.body = body
        self.max_altitude = max_altitude

        # initialize members
        self.heights = None
        self.nadir_solar_incidence = None
        self.pushbroom_solar_incidence = None
        self.fov_rectangles_corrected = {}
        self.fov_rectangles_uncorrected = {}

        # calculate approximate max distance for determining the interval
        # max distance = radius of ellipsoid + max altitude
        self.body_radius = spy.vnorm(spy.subpnt("NEAR POINT/ELLIPSOID", body, approximate_et,
                                                "IAU_" + body, "LT+S", self.probe)[0])
        self.body_area = 4 * np.pi * self.body_radius ** 2
        max_distance = self.body_radius + self.max_altitude

        # calculate the constraint interval based on max altitude
        result_cnfine = spy.utils.support_types.SPICEDOUBLE_CELL(2)
        cnfine = spy.utils.support_types.SPICEDOUBLE_CELL(2)
        # insert initial bounds into cnfine
        spy.appndd([approximate_et - max_time, approximate_et + max_time], cnfine)
        # validate window
        spy.wnvald(2, 2, cnfine)
        # get the constrained interval based on max altitude
        spy.gfdist(self.probe, "LT+S", self.body, "<", max_distance, 0, self.step, 1, cnfine, result_cnfine)
        # check there is only one interval
        if spy.wncard(result_cnfine) != 1:
            raise RuntimeError("Incorrect number of intervals found: " + str(spy.wncard(result_cnfine)))

        # get closest approach time
        result_min = spy.utils.support_types.SPICEDOUBLE_CELL(4)
        spy.gfdist(self.probe, "LT+S", body, "LOCMIN", max_distance, 0, self.step, 1, result_cnfine, result_min)
        if spy.wncard(result_min) != 1:
            raise RuntimeError("Incorrect number of local minima found: " + str(spy.wncard(result_min)))

        # save closest approach parameters
        self.ca_time = spy.wnfetd(result_min, 0)[0]
        ca_nadir = spy.subpnt("NEAR POINT/ELLIPSOID", body, self.ca_time, "IAU_" + body, "LT+S", self.probe)
        self.ca_nadir_vector = ca_nadir[2]
        self.ca_altitude = spy.vnorm(self.ca_nadir_vector)
        self.ca_lonlat = np.array(spy.reclat(spy.subpnt("NEAR POINT/ELLIPSOID", body, self.ca_time,
                                                        "IAU_" + body, "LT+S", self.probe)[0])[1:3]) * 180 / np.pi

        # start and end times
        self.time_interval = spy.wnfetd(result_cnfine, 0)

        # sample the time interval from start to end with logarithmic spacing, so that
        # the time region around CA is sampled more densely than far from CA
        times_before = self.ca_time - np.logspace(np.log10(0.1),
                                                  np.log10(np.abs(self.time_interval[0] - self.ca_time)), num=count)[
                                      ::-1]
        times_after = self.ca_time + np.logspace(np.log10(0.1), np.log10(self.time_interval[1] - self.ca_time),
                                                 num=count)
        self.times = np.concatenate((times_before, np.array([self.ca_time]), times_after))

        # calculate sub-spacecraft (nadir) points
        sub_points = [spy.subpnt("INTERCEPT/ELLIPSOID", body, t, "IAU_" + body, "LT+S", self.probe) for t in self.times]

        probe_positions = [spy.spkpos(self.probe, t, "IAU_" + body, "LT+S", body)[0] for t in self.times]
        solar_positions = [spy.spkpos("SUN", t, "IAU_" + body, "LT+S", body)[0] for t in self.times]

        self.probe_sun_angle = np.array([spy.vsep(p, s) for (p, s) in zip(probe_positions, solar_positions)])
        # distance from CA along surface curve
        ds = [0]
        # incremental surface distances from first point
        for i in range(len(self.times) - 1):
            ds.append(spy.vnorm(spy.vsub(sub_points[i + 1][0], sub_points[i][0])))
        ds = np.array(ds)
        s = np.cumsum(ds)
        self.surface_distances_from_ca = s - s[len(self.times) // 2]

        # compute nadir point surface velocity
        # using central differences: https://stackoverflow.com/questions/25875253/
        # numpy-or-scipy-derivative-function-for-non-uniform-spacing
        from scipy.interpolate import UnivariateSpline
        splin = UnivariateSpline(self.times, self.surface_distances_from_ca, s=0.0)
        dsplin = splin.derivative(1)
        self.nadir_surface_velocities = dsplin(self.times)

        # latitudes and longitudes at each point
        lat_coords = [spy.reclat(p[0]) for p in sub_points]
        self.longs = np.array([l[1] for l in lat_coords]) * 180 / np.pi
        self.lats = np.array([l[2] for l in lat_coords]) * 180 / np.pi
        # altitude at each point
        self.heights = np.array([spy.vnorm(p[2]) for p in sub_points])
        # calculate angle of solar incidence - 90 is straight above, 0 is on the horizon
        self.nadir_solar_angle = 90.0 - np.array([spy.ilumin("ELLIPSOID", self.body, t, "IAU_" + self.body,
                                                             "LT+S", self.probe, p[0])[3] for (t, p) in
                                                  zip(self.times, sub_points)]) * 180.0 / np.pi

        # calculate velocity relative to body center in J2000 frame
        body_relative_velocity_vectors = [spy.spkezr(self.probe, t, "J2000", "LT+S", self.body)[0][3:] for t in
                                          self.times]
        self.body_relative_velocities = np.array([spy.vnorm(b) for b in body_relative_velocity_vectors])

        # calculate pushbroom solar incidence
        self.get_pushbroom_solar_incidence()
        return

    def plot_ground_track_to_map(self, map: Basemap, **kwargs):
        # transform CA longitudes and latitudes according to the projection
        x, y = map(self.ca_lonlat[0], self.ca_lonlat[1])
        # plot CA point and label
        map.scatter(x, y, s=3, color='k')
        plt.text(x, y, self.name, fontsize=12, ha='left', va='bottom', color='k')
        # plot trajectory
        x, y = map(self.longs, self.lats)
        p = map.scatter(x, y, **kwargs)
        return p

    def plot_FOV_to_map(self, plot_map: Basemap, instrument_id: int, correct_overflow=False,
                        sparse=10, c_values=None, *args, **kwargs):
        # compute the FOV rectangles to be plotted, in CEA coordinates
        rects = self.get_FOV_rectangles_cylindrical(instrument_id, mid_points=3, correct_overflow=correct_overflow)
        # CEA map which will be used for coordinate transformations from CEA to lon-lat coords
        cea_to_lat_map = Basemap(projection='cea', rsphere=self.body_radius)
        for i, rect in enumerate(rects):
            # in case of sparser plotting, plot only a subset of rectangles
            if sparse:
                if i % sparse != 0:
                    continue
            # transform coords and plot them to the given map
            x, y = zip(*rect.exterior.coords)
            lon, lat = cea_to_lat_map(x, y, inverse=True)
            x, y = plot_map(lon, lat)
            if c_values is None:
                plot_map.plot(x, y, *args, **kwargs)
            else:
                plot_map.plot(x, y, c=c_values[i], **kwargs)
        return

    def get_FOV_rectangles_cylindrical(self, instrument_id: int, mid_points: int = 3, correct_overflow=True):
        """ Compute FOV rectangles at each point in CEA coordinates.
        Parameters:
            instrument_id: SPICE id of instrument with rectangular FOV
            mid_points: number of points to be sampled on each side of FOV rectangle
            correct_overflow: if True, the points that wrap around the 360 degree mark will be correctly transposed
                so that within each rectangle, the rectangle has a correct shape
        """
        if correct_overflow:
            if instrument_id in self.fov_rectangles_corrected:
                return self.fov_rectangles_corrected[instrument_id]
        else:
            if instrument_id in self.fov_rectangles_uncorrected:
                return self.fov_rectangles_uncorrected[instrument_id]
        fractions = mid_points + 1
        if mid_points < 0:
            raise RuntimeError("Number of mid points must be positive.")

        # get FOV characteristics from instrument kernel
        ik_output = spy.getfov(instrument_id, 10)
        if (ik_output[0] != "RECTANGLE"):
            raise RuntimeError("Non-rectangular FOVs not supported.")
        corners = ik_output[4]
        instrument_frame_name = ik_output[1]

        # generate an array with all FOV edge points in order (corners and mid_points)
        fov_edge = []
        for i, corner in enumerate(corners):
            # add corner
            fov_edge.append(corner)
            next_corner = corners[(i + 1) % 4]
            # add mid points between this corner and next corner
            for j in range(1, fractions):
                fov_edge.append(((fractions - j) * corner + j * next_corner) / fractions)

        # compute surface intercepts of all FOV edge vectors for all time points
        # WARNING: if even one vector does not intercept the body, this whole method throws a not found error
        try:
            fov_edge_points = [[spy.sincpt("ELLIPSOID", self.body, t, "IAU_" + self.body,
                                           "LT+S", self.probe, instrument_frame_name,
                                           bv)[0] for bv in fov_edge] for t in self.times]
        except SpiceyError:
            raise

        # now we have four points on the body surface for each sampling time
        # we transform these coordinates into latitudinal coordinates, and extract longitude and latitude
        lat_coords = [[np.array(spy.reclat(v)[1:3]) * 180 / np.pi for v in bound_vectors] for bound_vectors in
                      fov_edge_points]
        # we transform from latitude-longitude into equal-area cylindrical projection
        temp_map = Basemap(projection='cea', rsphere=self.body_radius)
        cyl_coords = [[temp_map(point[0], point[1]) for point in rectangle] for rectangle in lat_coords]
        # form a shapely rectangle for each point and return the list
        rectangles = [Polygon(corners) for corners in cyl_coords]

        # we need to make sure that no rectangle got distorted by the cutoff at left-right edge
        if correct_overflow:
            mid_line = LineString(self.body_radius * np.array([(np.pi, 0.0), (np.pi, np.pi)]))
            for i, rect in enumerate(rectangles):
                if rect.crosses(mid_line):
                    lat = self.lats[i]
                    lon = self.longs[i]
                    # this is the center of the rectangle, if it is not inside the rectangle, the rectangle is deformed
                    center = Point(temp_map(self.longs[i], self.lats[i]))
                    # the polygon is not valid if it crosses itself - which we don't want as well
                    if not rect.is_valid or not rect.contains(center):
                        x, y = zip(*rect.exterior.coords)
                        # transpose the x coordinates of points on left side
                        # of map onto the right side if center is on right
                        if lon > 0.0:
                            x_new = [a if (a > np.pi * self.body_radius) else (a + 2 * np.pi * self.body_radius) for a
                                     in x]
                        # otherwise transpose from right to left
                        else:
                            x_new = [a if (a < np.pi * self.body_radius) else (a - 2 * np.pi * self.body_radius) for a
                                     in x]
                        # replace the broken rectangle with the fixed one
                        new_rect = Polygon(zip(x_new, y))
                        rectangles[i] = new_rect

        # store the computed rectangles so we dont have to compute them again
        if correct_overflow:
            self.fov_rectangles_corrected[instrument_id] = rectangles
        else:
            self.fov_rectangles_uncorrected[instrument_id] = rectangles
        return rectangles

    def get_FOV_surface_areas(self, instrument_id):
        """ Returns an array of areas covered by FOV at each time point. """
        rects = self.get_FOV_rectangles_cylindrical(instrument_id, mid_points=3)
        return np.array([rect.area for rect in rects])

    def get_nadir_point_velocities(self):
        """ Returns the velocity with which the nadir point is moving along the surface at each time point."""
        return self.nadir_surface_velocities

    def get_velocities_relative_to_body(self):
        """ Returns the velocity with which the probe is moving relative to body barycenter at each time point."""
        return self.body_relative_velocities

    def get_track_times(self):
        """ Returns an array of time points."""
        return self.times

    def get_track_heights(self):
        """ Returns the height of probe above body surface at each time point."""
        return self.heights

    def get_track_longs_lats(self):
        """ Returns longitudes and latitudes of nadir point at each time point."""
        return (self.longs, self.lats)

    def get_surface_distance_from_ca(self):
        """ Returns the distance of nadir point from CA nadir point at each time point."""
        return self.surface_distances_from_ca

    def get_nadir_resolution(self, instrument_id: int, half_resolution_x: int):
        """ """
        ik_output = spy.getfov(instrument_id, 10)
        instrument_frame_name = ik_output[1]
        if (ik_output[0] != "RECTANGLE"):
            raise RuntimeError("Non-rectangular FOVs not supported.")
        # we don't care which rectangle corner vector we get
        bound_vector = ik_output[4][0]
        # set the y component to 0... so the vector is poiting to the vertical center at
        # either left or right edge of the FOV
        bound_vector[1] = 0.0

        norm_vector = np.array([0.0, 0.0, 1.0])
        half_angle = spy.vsep(bound_vector, norm_vector)
        half_distances_km = np.tan(half_angle) * self.get_track_heights()
        self.px_per_km = half_resolution_x / half_distances_km
        return self.px_per_km

    def get_nadir_solar_angle(self):
        return self.nadir_solar_angle

    def get_pushbroom_solar_incidence(self):
        if self.pushbroom_solar_incidence is not None:
            return self.pushbroom_solar_incidence
        # check occultation conditions
        occult = [spy.occult(self.body, "ELLIPSOID", "IAU_" + self.body, "SUN",
                             "POINT", "J2000", "LT+S", "JUICE", t) != 0 for t in self.times]
        panel_vector = np.array([0.0, 1.0, 0.0])
        sun_positions = [spy.spkezr("SUN", t, "JUICE_SPACECRAFT", "LT+S", "JUICE")[0][0:3] for t in
                         self.get_track_times()]
        angles = np.array([spy.vsep(panel_vector, sun_p) for sun_p in sun_positions])
        solar_incidence = np.sin(angles)
        self.pushbroom_solar_incidence = np.array([0.0 if is_occulted else incidence for
                                                   (is_occulted, incidence) in zip(occult, solar_incidence)])
        return self.pushbroom_solar_incidence

    def get_probe_sun_angles(self):
        return self.probe_sun_angle

    def plot_profile(self, fig: plt.Figure, max_time: float = None, max_altitude: float = None,
                     instrument_id: int = None, half_resolution_x: int = None):
        """ Plots a profile plot of the flyby to given figure. A lot of boilerplate code.
        Parameters:
            fig: figure to plot to, usually plt.gcf() is good
            max_time: time cutoff from CA [s]
            max_altitude: altitude cutoff [km]
            instrument_id: spice instrument id
            half_resolution_x: half of the total resolution of instrument along x-axis
                (e.g. for JANUS this value is 1000)
        """

        def plot_and_set_axis_color(ax, x_data, y_data, color, ylabel, limits=None, logy=False):
            if logy:
                ax.semilogy(x_data, y_data, color)
                ax.set_yscale('log')
            else:
                ax.plot(x_data, y_data, color)
            ax.set_ylabel(ylabel, color=color)
            ax.tick_params(axis='y', colors=color)
            if limits is not None:
                ax.set_ylim(limits)

        if instrument_id is not None and half_resolution_x is None:
            raise RuntimeError("You need to specify instrument resolution!")
        if max_time is not None and max_altitude is not None:
            raise RuntimeError("You cannot specify both constraints.")
        if max_time is not None:
            ids = np.where(np.abs(self.times - self.ca_time) < max_time)
        elif max_altitude is not None:
            ids = np.where(self.heights < max_altitude)
        else:
            ids = np.arange(len(self.times))
        times = self.times[ids] - self.ca_time
        heights = self.heights[ids]
        if len(heights) == 0:
            print("No points to plot because of constraints for flyby {}.".format(self.name))
            return
        plt.figure(fig.number)
        ax = plt.gca()
        if instrument_id is not None:
            plot_and_set_axis_color(ax, times, heights, 'b', 'Altitude [km]', limits=[0.0, 1.1 * max(heights)])

            ax4 = ax.twinx()
            ax4.spines['left'].set_position(('axes', -0.15))
            ax4.yaxis.set_label_position('left')
            ax4.set_frame_on(True)
            ax4.patch.set_visible(False)
            km_per_px = 1.0 / self.get_nadir_resolution(instrument_id, half_resolution_x)[ids]
            plot_and_set_axis_color(ax4, times, km_per_px, 'm',
                                    'Resolution [km/px]', [0.0001, 10.0], logy=True)
            ax4.yaxis.tick_left()
        else:
            plt.plot(times, heights)
            plt.ylabel('Altitude [km]')
            ax.set_ylim([0, 1.1 * max(heights)])
        ax.set_xlabel('Time [s]')
        ax.grid()
        ax2 = plt.twinx()

        ax2.spines['right'].set_position(('axes', 1.1))
        ax2.set_frame_on(True)
        ax2.patch.set_visible(False)
        plot_and_set_axis_color(ax2, times, self.get_nadir_solar_angle()[ids], 'r', 'Nadir Sun angle [deg]',
                                limits=[0.0, 99.0])
        ax2.set_yticks([0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0])

        ax3 = ax.twinx()
        plot_and_set_axis_color(ax3, times, self.get_pushbroom_solar_incidence()[ids], 'g',
                                'Pushbroom panel illumination [-]', [0.0, 1.1])
        axx = ax.twiny()
        axx.set_xlabel('Distance from CA [km]')

        # some magic to get proper rescaling of second axis
        def find_nearest(array, value):
            idx = (np.abs(array - value)).argmin()
            return (idx, array[idx])

        distances = self.get_surface_distance_from_ca()[ids]
        dist_to_time = max(distances) / max(times)
        axx.set_xticks(ax.get_xticks())
        axx.set_xbound(ax.get_xbound())
        axx.set_xticklabels([int(distances[find_nearest(times, a)[0]]) for a in ax.get_xticks()])
        title = ax.set_title('Flyby profile: {}'.format(self.name))
        title.set_y(1.1)
        fig.subplots_adjust(right=0.85, left=0.15, top=0.85)

    def print_properties(self, stream=sys.stdout):
        """ Print properties of the flyby to stdout stream. """
        string = "\nFlyby properties: {}\n".format(self.name) + \
                 " - Body: {}\n".format(self.body) + \
                 " - Closest approach:\n" + \
                 "    - Time: {} \n".format(spy.et2utc(self.ca_time, "C", 0)) + \
                 "    - Alt: {:2.1f} km\n".format(self.ca_altitude) + \
                 "    - Lon: {:2.1f} deg\n".format(self.ca_lonlat[0]) + \
                 "    - Lat: {:2.1f} deg\n".format(self.ca_lonlat[1]) + \
                 " - Start: {}\n".format(spy.et2utc(self.time_interval[0], "C", 0)) + \
                 " - End:   {}\n".format(spy.et2utc(self.time_interval[1], "C", 0)) + \
                 " - Max alt: {:2.1f} km\n".format(self.max_altitude)
        print(string, file=stream)

    def print_properties_to_file(self, filename):
        """ Print properties of flyby to given file.
        Parameters:
            filename: path to file (contents will be overwritten)
        """
        with open(filename, 'w') as f:
            self.print_properties(stream=f)

if __name__ == '__main__':
    # Load the CREMA3.2 metakernels for JUICE
    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)
    # Analyze Callisto flyby
    C = Flyby("CALLISTO", spy.str2et("25 Apr 2031 12:00"), 300000, name="14C6_c3.2", step=1.0, count=5000)
    C.print_properties()
    # Unload metakernel
    spy.unload(MK_C32)

    map = Basemap()
    map.drawmeridians(np.arange(0, 360, 30))
    map.drawparallels(np.arange(-90, 90, 30))
    a = C.plot_ground_track_to_map(map, c=C.get_nadir_solar_angle(), cmap="plasma", vmin=0, vmax=90.0, s=1)
    a.cmap.set_under('g')
    plt.title('Solar incidence (green = shade) [-]')
    plt.colorbar(shrink=0.55)
    plt.show()

    C.plot_profile(plt.gcf())
    plt.show()