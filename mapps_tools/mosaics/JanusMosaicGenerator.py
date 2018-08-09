# coding=utf-8
from datetime import datetime, timedelta
from typing import Tuple, Union

import spiceypy as spy

from mapps_tools.mosaics.CustomMosaic import CustomMosaic
from mapps_tools.mosaics.DiskMosaic import DiskMosaic
from mapps_tools.mosaics.MosaicGenerator import MosaicGenerator
from mapps_tools.mosaics.misc import get_smear_px
from mapps_tools.mosaics.units import angular_units, time_units, convertAngleFromTo, convertTimeFromTo


class JanusMosaicGenerator:
    """ Generator for mosaics optimized for JANUS FOV and behavior.

    Methods:
        generate_mosaic(): Creates either a full-body "raster" mosaic symmetric along
            x and y axis, or a "custom" mosaic imaging the sun-illuminated part of body.
    """
    JANUS_FOV_SIZE_DEG = (1.72, 1.29)
    JANUS_FOV_RES = (2000, 1504)
    probe = "JUICE"
    JUICE_SLEW_RATE_DEG_PER_SEC = 0.025
    JANUS_max_Mbits_per_image = JANUS_FOV_RES[0] * JANUS_FOV_RES[1] * 14 / 1_000_000

    def __init__(self, target: str, time_unit: str = "min", angular_unit: str = "deg"):
        """ Creates a JanusMosaicGenerator

        :param target: target body, e.g. "CALLISTO"
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        """
        if not target or not isinstance(target, str):
            raise TypeError(f"target must be a non-empty string, not '{target}'")
        self.target = target
        if time_unit not in time_units:
            raise ValueError(f"Time unit must be one of following: {time_units}")
        self.time_unit = time_unit
        if angular_unit not in angular_units:
            raise ValueError(f"Angular unit must be one of following: {angular_units}")
        self.angular_unit = angular_unit

        # Convert JANUS FOV size from radians to required angular unit
        self.fov_size: Tuple[float, float] = tuple(
            convertAngleFromTo(v_deg, "deg", self.angular_unit) for v_deg in self.JANUS_FOV_SIZE_DEG)
        # the time unit arguments are in opposite order because slew rate has time in denominator
        self.slew_rate_in_required_units = convertTimeFromTo(convertAngleFromTo(self.JUICE_SLEW_RATE_DEG_PER_SEC, "deg", self.angular_unit), self.time_unit, "sec")

    def generate_mosaic(self, time: datetime, exposure_time_s: float,
                        stabilization_time_s: float, no_of_filters: int,
                        filter_switch_duration_s: float, margin: float,
                        overlap: float, sunside: bool) -> Union[DiskMosaic, CustomMosaic]:
        """ Create a mosaic with image positions optimized for minimal frame number,
        and minimal distance between frames, while preserving required overlap between
        frames and margin around the body.

        A report of the generator is printed to standard output.

        :param time: Start time of mosaic as datetime object.
        :param exposure_time_s: Exposure time for one frame in seconds,
        must be larger than 0.
        :param stabilization_time_s: Stabilization time after each position change before
        imaging starts, must be larger or equal to 0.
        :param no_of_filters: Number of imaging filters used per each position. This increases
        dwell time and data volume.
        :param filter_switch_duration_s: How long does it take to switch from one filter to another
        in case of multi-filter imaging [seconds]
        :param margin: Extra space left around the body disk in units of body radii. This
        effectively increases the presumed size of object. For example, a value of 0.1 would
        cause the mosaic to also cover the atmosphere around the object, up to the altitude of
        10% of body radius.
        :param overlap: Minimal required overlap of neighboring frames. For example, if this
        is set to 0.1, then at least 10% of given frame overlaps with its neighbor on each
        of the 4 sides. Must be between 0.0 and 1.0
        :param sunside: If set to True, only the sun-illuminated surface is covered. Otherwise
        the whole body is imaged in a "raster" observation. Default is False - full-disk imaging.
        :return: Optimized mosaic, a DiskMosaic in case of full-body imaging, and a CustomMosaic
        if only sun-illuminated part of body is imaged.
        """
        if exposure_time_s <= 0.0:
            raise ValueError(f"exposure_time must be positive, not {exposure_time_s}")
        if stabilization_time_s < 0.0:
            raise ValueError(f"stabilization_time_s must be non-negative, not {stabilization_time_s}")
        if filter_switch_duration_s < 0.0:
            raise ValueError(f"filter switch duration time must be non-negative, not {filter_switch_duration_s}")
        if margin < 0.0:
            raise ValueError(f"margin must be non-negative, not {margin}")
        if no_of_filters < 1 or not isinstance(no_of_filters, int):
            raise ValueError(f"no_of_filters must be an integer of value at least 1, not {no_of_filters}")
        if not 0.0 <= overlap <= 1.0:
            raise ValueError(f"overlap is out of valid range <0.0, 1.0>. value: {overlap}")

        dwell_time_s = stabilization_time_s + \
            exposure_time_s * no_of_filters + \
            filter_switch_duration_s * (no_of_filters - 1)

        dmg = MosaicGenerator(self.fov_size, self.probe, self.target, time, self.time_unit,
                              self.angular_unit, convertTimeFromTo(dwell_time_s, "sec", self.time_unit),
                              self.slew_rate_in_required_units)
        if sunside:
            dm = dmg.generate_sunside_mosaic(margin=margin, min_overlap=overlap)
        else:
            dm = dmg.generate_symmetric_mosaic(margin=margin, min_overlap=overlap)

        image_count = len(dm.center_points) * no_of_filters
        duration = dm.end_time - dm.start_time

        max_smear = max(get_smear_px(exposure_time_s, self.probe, self.target,
                                     t, self.JANUS_FOV_SIZE_DEG[0], self.JANUS_FOV_RES[0])
                        for t in (dm.start_time + timedelta(seconds=s)
                                  for s in range(0, int(duration.total_seconds()), int(dwell_time_s))))

        report = \
f'''JANUS MOSAIC GENERATOR REPORT:
 Mosaic type: {"Sunside" if sunside else "Full disk"} 
 Target: {self.target}
 No of filters: {no_of_filters}
 Stabilization time: {stabilization_time_s:.3f} s
 Exposure time: {exposure_time_s:.3f} s
 Filter switch time: {filter_switch_duration_s:.3f} s
 Max smear over one exposure: {max_smear:.3f} px
 {self.probe} slew rate: {self.slew_rate_in_required_units:.3f} {self.angular_unit} / {self.time_unit}
 Start time: {dm.start_time.isoformat()}
 End time:   {dm.end_time.isoformat()}
 Duration: {duration} 
 Total number of images: {image_count} ({len(dm.center_points)} positions, {no_of_filters} filters at each position).
 Uncompressed data volume: {image_count * self.JANUS_max_Mbits_per_image:.3f} Mbits
 Uncompressed average data rate: {image_count * self.JANUS_max_Mbits_per_image * 1000 / duration.total_seconds():.3f} kbits/s
 Used dwell time: {dwell_time_s:.3f} s
'''
        print(report)

        return dm


if __name__ == '__main__':
    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2030-09-17T12:30:00", "%Y-%m-%dT%H:%M:%S")
    jmg = JanusMosaicGenerator("EUROPA", "min", "deg")
    cm = jmg.generate_mosaic(start_time,
                             exposure_time_s=20,
                             stabilization_time_s=5,
                             filter_switch_duration_s=2.5,
                             no_of_filters=4,
                             margin=0.05,
                             overlap=0.10,
                             sunside=True)

    cm.plot()
    print(cm.generate_PTR(decimal_places=2))

    """
    start_time = datetime.strptime("2031-04-25T18:40:47", "%Y-%m-%dT%H:%M:%S")
    jmg = JanusMosaicGenerator("CALLISTO", "min", "deg")
    dm = jmg.generate_optimized_mosaic_iterative(start_time,
                                     max_exposure_time_s=15,
                                     max_smear=0.25,
                                     stabilization_time_s=5,
                                     no_of_filters=4,
                                     extra_margin=0.05)
    print(dm.generate_PTR(decimal_places=3))
    dm.plot()

    start_time = datetime.strptime("2031-04-26T00:40:47", "%Y-%m-%dT%H:%M:%S")
    jmg = JanusMosaicGenerator("CALLISTO", "min", "deg")
    dm = jmg.generate_optimized_mosaic_iterative(start_time,
                                               max_exposure_time_s=15,
                                               max_smear=0.25,
                                               stabilization_time_s=5,
                                               no_of_filters=4,
                                               extra_margin=0.05)
    print(dm.generate_PTR(decimal_places=3))
    dm.plot()
    """
