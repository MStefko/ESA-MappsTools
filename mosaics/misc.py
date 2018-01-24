# coding=utf-8
from datetime import datetime

from matplotlib import pyplot as plt
from typing import Tuple

from shapely.geometry import Polygon
import spiceypy as spy


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

if __name__=="__main__":
    r = Rectangle( (0.0, 0.0), (1.0, 3.0))
    print(f"Corners: {r.corners}")
    print(f"Polygon: {r.polygon}")
    print(f"Center: {r.center}")



