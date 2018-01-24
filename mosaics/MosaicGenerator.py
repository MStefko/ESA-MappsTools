# -*- coding: utf-8 -*-
""" Tools for generating and exploring mosaic acquisitions.

@author: Marcel Stefko
"""
from typing import List, NamedTuple, Tuple
import numpy as np
from shapely.geometry import Polygon, Point
from matplotlib import pyplot as plt

Rectangle = NamedTuple("Rectangle", (("center", Tuple[float, float]), ("polygon", Polygon)))

class MosaicGenerator:
    """ Creates mosaics from specified FOV dimensions and disk dimensions.

    """
    def __init__(self, fov_x: float, fov_y: float, disk_radius: float,
                 overlap: float = 0.1, edge_margin: float = 0.2, pos_x: float = 0.0,
                 pos_y: float = 0.0):
        """All numbers should be provided in the same units (e.g. degrees), unless specified
        otherwise.
        :param fov_x: Total width of instrument FOV
        :param fov_y: Total height of instrument FOV
        :param disk_radius: Radius of planetary disk
        :param overlap: Required fraction of overlap between neighboring frames.
        E.g. for 10% overlap, set to 0.1
        :param edge_margin: Margin around planetary disk to also be covered by the mosaic
        :param pos_x: Optional requirement on x-position of center of one of mosaic's frames.
        :param pos_y: Optional requirement on x-position of center of one of mosaic's frames.
        """
        if overlap < 0.0 or overlap > 1.0:
            raise ValueError("Overlap must be between 0 and 1!")
        if edge_margin < 0.0:
            raise ValueError("Edge margin must be non-negative!")
        if fov_x <= 0.0 or fov_y <= 0.0 or disk_radius<=0.0:
            raise ValueError("FOV and disk dimensions must be positive!")

        self.fov_x = fov_x
        self.pos_x = pos_x
        self.fov_y = fov_y
        self.pos_y = pos_y
        self.disk_radius = disk_radius
        self.overlap = overlap
        self.edge_margin = edge_margin

        self.rectangles_all = None
        self.rectangles_trimmed = None

    def get_rectangles_all(self):
        if self.rectangles_all is None:
            self._generate_rectangles()
        return self.rectangles_all

    def _generate_rectangles(self):
        dx = 0.5 * self.fov_x
        dy = 0.5 * self.fov_y

        def make_rect(x_center: float, y_center: float) -> Rectangle:
            coords = [(x_center-dx, y_center-dy), (x_center-dx, y_center+dy),
                      (x_center+dx, y_center+dy), (x_center+dx, y_center-dy)]
            return Rectangle((x_center, y_center), Polygon(coords))

        xx, yy = self._get_xy_positions()
        self.rectangles_all = []
        for (idx, x) in enumerate(xx):
            column = [make_rect(x,y) for y in yy]
            if idx%2:
                column = list(reversed(column))
            self.rectangles_all += column

    def get_rectangles_trimmed(self) -> List[Rectangle]:
        if self.rectangles_trimmed is None:
            self._trim_rectangles()
        return self.rectangles_trimmed

    def _trim_rectangles(self):
        circle = Point(0.0, 0.0).buffer(self.disk_radius)
        self.rectangles_trimmed = [r for r in self.get_rectangles_all() if circle.intersects(r.polygon)]

    def plot_mosaic(self, trimmed=True, condition: str = None):
        fig, ax = plt.subplots()
        circle = plt.Circle((0, 0), radius=self.disk_radius, color='r')
        circle_margin = plt.Circle((0, 0), radius=self.disk_radius+self.edge_margin, color='g', fill=False)
        ax.add_artist(circle_margin)
        ax.add_artist(circle)
        rects = self.get_rectangles_trimmed() if trimmed else self.get_rectangles_all()
        if condition is not None:
            rects = self.get_rectangles_filtered(condition)
        for rect in rects:
            x,y = rect.polygon.exterior.xy
            ax.plot(x,y,color='b')

    def _get_xy_positions(self):
        return tuple([self._get_positions_along_axis(fov_dim, force_pos=pos)
                      for (fov_dim, pos) in ((self.fov_x, self.pos_x), (self.fov_y, self.pos_y))])

    def _get_positions_along_axis(self, fov_dim: float, force_pos: float = 0.0) -> List[float]:
        if fov_dim<=0.0:
            raise ValueError()

        if force_pos!=0.0:
            limit = self.disk_radius + self.edge_margin - 0.5*fov_dim
            if abs(force_pos) > limit:
                raise ValueError(f"Forced position too close to disk edge. Value: {force_pos}, Limit: {limit}")

        required_covered_radius = self.disk_radius + self.edge_margin
        edge_fov_center_position_min_requirement = required_covered_radius - 0.5 * fov_dim

        below_fov_centers = np.flip(np.arange(force_pos, -(required_covered_radius+fov_dim), - fov_dim * (1 - self.overlap)),0)
        above_fov_centers = np.arange(force_pos + fov_dim * (1 - self.overlap), required_covered_radius+fov_dim, fov_dim * (1 - self.overlap))
        fov_center_candidates = np.concatenate((below_fov_centers, above_fov_centers))
        fov_centers = []
        i = 0
        while fov_center_candidates[i] <= -edge_fov_center_position_min_requirement:
            last_center = fov_center_candidates[i]
            i += 1
        fov_centers.append(last_center)
        while fov_center_candidates[i] < edge_fov_center_position_min_requirement:
            fov_centers.append(fov_center_candidates[i])
            i +=1
        fov_centers.append(fov_center_candidates[i])
        return fov_centers

    def get_rectangles_filtered(self, condition: str):
        return eval(f"[r for r in self.get_rectangles_trimmed() if {condition}]")

    def generate_offsetAngles(self, dwell_time_minutes: float, slew_time_minutes: float, decimal_places: int = 2,
                              condition: str = "True"):
        if decimal_places < 0:
            raise ValueError()
        if dwell_time_minutes <= 0.0 or slew_time_minutes <= 0.0:
            raise ValueError("Dwell and slew times must be positive.")
        # max nondecimal digits not including minus sign
        mnd = max([(len(f"{t:.0f}")) for t in (slew_time_minutes, dwell_time_minutes)])
        # one extra for decimal point and one for sign
        f_length = mnd + decimal_places + 2

        rects = self.get_rectangles_filtered(condition)

        #deltaTimes
        deltaTimes = "<deltaTimes units='min'> " + \
                     (f" {dwell_time_minutes: {f_length}.{decimal_places}}" +
                      f" {slew_time_minutes: {f_length}.{decimal_places}}" )*len(rects) + \
                     " </deltaTimes>\n"

        xAngles =    "<xAngles units='deg'>    " + \
                     "".join([2*f" {r.center[0]: {f_length}.{decimal_places}}" for r in rects]) + \
                     " </xAngles>\n"

        xRates =     "<xRates units='deg/min'> " + f" {0.0:{f_length}.{decimal_places}}"*2*len(rects) + " </xRates>\n"

        yAngles =    "<yAngles units='deg'>    " + \
                     "".join([2 * f" { r.center[1]:{f_length}.{decimal_places}}" for r in rects]) + \
                     " </yAngles>\n"

        yRates =     "<yRates units='deg/min'> " + f" {0.0: {f_length}.{decimal_places}}"*2*len(rects) + " </yRates>"

        print(f"No of points: {len(rects)}.")
        print(f"Total time duration: {(dwell_time_minutes + slew_time_minutes)*len(rects):.2f} min.")

        return deltaTimes + xAngles + xRates + yAngles + yRates

    def print_centers(self):
        rects = self.get_rectangles_filtered("r.center[0]>-1.0")
        l = [r.center for r in rects]
        print(l)

if __name__=='__main__':

    # A simple 3x4 JANUS mosaic.
    #m = MosaicGenerator(1.72, 1.29, 2.25, overlap=0.1, edge_margin=0.1, pos_y=-1.29*0.9/2.0)
    #m.plot_mosaic(trimmed=True)
    #print(m.generate_offsetAngles(2.0, 1.0))
    #plt.grid(True)
    #plt.show()

    # A large JANUS mosaic with only imaging of illuminated side.
    m = MosaicGenerator(1.72, 1.29, 7.7 / 2, overlap=0.2, edge_margin=0.1, pos_x=-0.4, pos_y=0.645)
    m.plot_mosaic(trimmed=True, condition="r.center[0]>-1.0")
    print(m.generate_offsetAngles(0.5, 0.3, condition="r.center[0]>-1.0"))
    plt.grid(True)
    plt.show()
    m.print_centers()






