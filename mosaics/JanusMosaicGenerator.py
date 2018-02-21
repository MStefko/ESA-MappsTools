# coding=utf-8
from datetime import datetime, timedelta
from typing import Tuple, Union

import spiceypy as spy

from mosaics.CustomMosaic import CustomMosaic
from mosaics.DiskMosaic import DiskMosaic
from mosaics.MosaicGenerator import MosaicGenerator
from mosaics.misc import get_max_dwell_time_s, get_body_angular_diameter_rad
from mosaics.units import angular_units, time_units, convertAngleFromTo, convertTimeFromTo


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
    FILTER_SWITCH_DURATION_SECONDS = 2.5
    JANUS_max_Mbits_per_image = JANUS_FOV_RES[0] * JANUS_FOV_RES[1] * 14 / 1_000_000

    def __init__(self, target: str, time_unit: str = "min", angular_unit: str = "deg"):
        """ Creates a JanusMosaicGenerator

        :param target: target body, e.g. "CALLISTO"
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        """
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

    def _get_max_dwell_time_s(self, max_smear: float, time: datetime) -> float:
        return get_max_dwell_time_s(max_smear, self.probe, self.target, time,
            self.JANUS_FOV_SIZE_DEG[0], self.JANUS_FOV_RES[0])

    def generate_mosaic(self, time: datetime, max_exposure_time_s: float,
                        stabilization_time_s: float = 0.0, duration_guess_minutes: float = 30,
                        max_smear: float = 0.25, no_of_filters: int = 1, extra_margin: float = 0.1,
                        overlap: float = 0.1, sunside: bool = False) -> Union[DiskMosaic, CustomMosaic]:
        """ Create a mosaic with image positions optimized for minimal frame number,
        and minimal distance between frames, while preserving required overlap between
        frames and margin around the body.



        :param time: Start time of mosaic as datetime object.
        :param max_exposure_time_s: Maximal exposure time for one frame in seconds,
        must be larger than 0.
        :param stabilization_time_s: Stabilization time after each position change before
        imaging starts, must be larger or equal to 0.
        :param duration_guess_minutes: Initial guess for duration of mosaic in minutes. This is used to
        estimate the shrink / growth rate of target body, so that changing size and velocity
        conditions do not affect the coverage / smear too much. Must be larger or equal to 1.0
        :param max_smear: Maximal allowed smear in units of pixels. This means that per exposure,
        the imaged object cannot move inside the image more than a given amount. For example,
        a value 0.25 would allow the imaged object to move 1/4th of a pixel over one exposure.
        If smear is above this value, exposure time is reduced until this requirement is met.
        :param no_of_filters: Number of imaging filters used per each position. This increases
        dwell time and data volume.
        :param extra_margin: Extra space left around the body disk in units of body radii. This
        effectively increases the presumed size of object. For example, a value of 0.1 would
        cause the mosaic to also cover the atmosphere around the object, up to the altitude of
        10% of body radius.
        :param overlap: Minimal required overlap of neighboring frames. For example, if this
        is set to 0.1, then at least 10% of given frame overlaps with its neighbor on each
        of the 4 sides. Must be between 0.0 and 1.0
        :param sunside: If set to True, only the sun-illuminated surface is covered. Otherwise
        the whole body is imaged in a "raster" observation. Default is False - full-disk imaging..
        :return: Optimized mosaic, a DiskMosaic in case of full-body imaging, and a CustomMosaic
        if only sun-illuminated part of body is imaged.
        """
        if max_exposure_time_s <= 0.0:
            raise ValueError("max_exposure_time must be positive.")
        if duration_guess_minutes < 1.0:
            raise ValueError("duration_guess_minutes must be at least 1.0 .")
        if stabilization_time_s < 0.0:
            raise ValueError("stabilization_time_s must be non-negative.")
        if max_smear <= 0.0:
            raise ValueError("max_smear must be positive")
        if no_of_filters < 1:
            raise ValueError("no_of_filters must be at least 1")

        # check highest possible exposure time based on smear
        exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in
                            range(int(duration_guess_minutes))]
        used_exposure_time_s = min(exposure_times_s + [max_exposure_time_s])
        dwell_time_s = stabilization_time_s + \
            used_exposure_time_s * no_of_filters + \
            self.FILTER_SWITCH_DURATION_SECONDS * (no_of_filters - 1)

        # Compute
        time_interval = (time, time + timedelta(minutes=duration_guess_minutes))
        ang_diameters = [get_body_angular_diameter_rad(self.probe, self.target, t) for t in
                         time_interval]
        ratio = ang_diameters[1] / ang_diameters[0]
        margin = (ratio - 1 if ratio > 1 else 0.0) + extra_margin

        dmg = MosaicGenerator(self.fov_size, "JUICE", self.target, time, self.time_unit,
                              self.angular_unit, convertTimeFromTo(dwell_time_s, "sec", self.time_unit),
                              self.slew_rate_in_required_units)
        if sunside:
            dm = dmg.generate_sunside_mosaic(margin=margin, min_overlap=overlap)
        else:
            dm = dmg.generate_symmetric_mosaic(margin=margin, min_overlap=overlap)

        image_count = len(dm.center_points) * no_of_filters
        duration = dm.end_time - dm.start_time

        report = \
f'''JANUS MOSAIC GENERATOR REPORT:
 Target: {self.target}
 No of filters: {no_of_filters}
 Max smear: {max_smear} px
 Stabilization time: {stabilization_time_s:.3f} s
 {self.probe} slew rate: {self.slew_rate_in_required_units:.3f} {self.angular_unit} / {self.time_unit}
 Start time: {dm.start_time.isoformat()}
 End time:   {dm.end_time.isoformat()}
 Duration: {duration} 
 Total number of images: {image_count} ({len(dm.center_points)} positions, {no_of_filters} filters at each position).
 Uncompressed data volume: {image_count * self.JANUS_max_Mbits_per_image:.3f} Mbits
 Uncompressed average data rate: {image_count * self.JANUS_max_Mbits_per_image * 1000 / duration.total_seconds():.3f} kbits/s
 Calculated max exposure time: {min(exposure_times_s):.3f} s
 Used exposure time: {used_exposure_time_s:.3f} s
 Used dwell time: {dwell_time_s:.3f} s ({dmg.dwell_time:.3f} {dmg.time_unit} in generator)
'''
        print(report)

        # verify zoom coverage
        ang_diameters = [get_body_angular_diameter_rad(self.probe, self.target, t) for t in
                         (dm.start_time, dm.end_time)]
        ratio = ang_diameters[1] / ang_diameters[0]
        if ratio > (1 + margin):
            warning = \
f"""*** POST-GENERATION WARNING ***
 Given margin ({100*margin:.1f}%) is too small - at end of mosaic, the target will have grown by {100*(ratio-1):.1f}%. 
*** END WARNING ***
"""
            print(warning)

        # verify exposure time coverage
        duration_minutes = duration.total_seconds() / 60
        if duration_minutes > duration_guess_minutes:
            exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in
                range(int(duration_minutes))]
            if min(exposure_times_s) < used_exposure_time_s:
                warning = \
f"""*** POST-GENERATION WARNING ***
 Chosen exposure time ({used_exposure_time_s:.3f} s) is larger than maximal allowed exposure time ({min(exposure_times_s):.3f} s).
 Either set duration_guess_minutes to value at least {duration_minutes:.3f}, or set exposure time to less than {min(exposure_times_s):.3f} s. 
*** END WARNING ***
"""
                print(warning)

        return dm

    def generate_optimized_mosaic_iterative(self, time: datetime, max_exposure_time_s: float,
                                            stabilization_time_s: float = 0.0,
                                            max_smear: float = 0.25, no_of_filters: int = 1, extra_margin: float = 0.05,
                                            overlap: float = 0.1, n_iterations: int = 30) -> DiskMosaic:
        """ Iteratively generate and optimizes a JANUS mosaic. Only supports generating "raster" DiskMosaics.

        Iteration takes an initial duration guess, computes required mosaic size while accounting for moon growth
        during this duration, and computes the time required to image this mosaic. This computed time is then
        used as input for the next iteration. The reason iteration is required is because geometry affects
        duration (i.e. it takes longer to slew across larger angular distances, and geometry also determines number
        of required positions), and duration affects geometry in return (target size changes over time so if the
        mosaic takes longer, the target grows larger).

        :param time: Start time of mosaic as datetime object.
        :param max_exposure_time_s: Maximal exposure time for one frame in seconds,
        must be larger than 0.
        :param stabilization_time_s: Stabilization time after each position change before
        imaging starts, must be larger or equal to 0.
        :param max_smear: Maximal allowed smear in units of pixels. This means that per exposure,
        the imaged object cannot move inside the image more than a given amount. For example,
        a value 0.25 would allow the imaged object to move 1/4th of a pixel over one exposure.
        If smear is above this value, exposure time is reduced until this requirement is met.
        :param no_of_filters: Number of imaging filters used per each position. This increases
        dwell time and data volume.
        :param extra_margin: Extra space left around the body disk in units of body radii. This
        effectively increases the presumed size of object. For example, a value of 0.1 would
        cause the mosaic to also cover the atmosphere around the object, up to the altitude of
        10% of body radius.
        :param overlap: Minimal required overlap of neighboring frames. For example, if this
        is set to 0.1, then at least 10% of given frame overlaps with its neighbor on each
        of the 4 sides. Must be between 0.0 and 1.0
        :param n_iterations: Maximal number of iterations before returning the result.
        :return: Optimized DiskMosaic.
        """
        if max_exposure_time_s <= 0.0:
            raise ValueError("max_exposure_time must be positive.")
        if stabilization_time_s < 0.0:
            raise ValueError("stabilization_time_s must be non-negative.")
        if max_smear <= 0.0:
            raise ValueError("max_smear must be positive")
        if no_of_filters < 1:
            raise ValueError("no_of_filters must be at least 1")
        if n_iterations < 1:
            raise ValueError("n_iteration must be at least 1")

        # initial guess for duration - from this we calculate the exposure time
        duration_guess_minutes = 1.0
        time_interval = (time, time + timedelta(minutes=int(duration_guess_minutes)))

        i = 1
        while True:
            # calculate margin needed based on last time interval estimate
            ang_diameters = [get_body_angular_diameter_rad(self.probe, self.target, t) for t in
                             time_interval]
            ratio = ang_diameters[1] / ang_diameters[0]
            margin = (ratio - 1 if ratio > 1 else 0.0) + extra_margin

            iter_report = \
f'''Iteration no. {i} out of {n_iterations}
    Growth factor estimate:    {ratio:.3f}
    Margin estimate:           {margin:.3f}
    Duration estimate:         {duration_guess_minutes:.5f} min
'''
            print(iter_report)

            # calculate exposure time and dwell time based on last time interval estimate
            exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in
                                list(range(int(duration_guess_minutes))) + [duration_guess_minutes]]
            used_exposure_time_s = min(exposure_times_s + [max_exposure_time_s])
            dwell_time_s = stabilization_time_s + \
                used_exposure_time_s * no_of_filters + \
                self.FILTER_SWITCH_DURATION_SECONDS * (no_of_filters - 1)

            dmg = MosaicGenerator(self.fov_size, "JUICE", self.target, time, self.time_unit,
                                  self.angular_unit,
                                  convertTimeFromTo(dwell_time_s, "sec", self.time_unit),
                                  self.slew_rate_in_required_units)
            dm = dmg.generate_symmetric_mosaic(margin=margin, min_overlap=overlap)

            # update time interval estimate
            time_interval = (dm.start_time, dm.end_time)
            duration = dm.end_time - dm.start_time
            if (duration.total_seconds() / 60 == duration_guess_minutes):
                print("*** STOP ITERATION - EQUILLIBRIUM REACHED ***\n")
                break
            else:
                duration_guess_minutes = duration.total_seconds() / 60
                i += 1
                if i > n_iterations:
                    break

        # calculate final growth ratio
        ang_diameters = [get_body_angular_diameter_rad(self.probe, self.target, t) for t in
                         time_interval]
        ratio = max(ang_diameters[1] / ang_diameters[0], 1.0)
        # calculate final max exposure time
        exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in
                            range(int(duration_guess_minutes))] + [max_exposure_time_s]

        image_count = len(dm.center_points) * no_of_filters
        report = \
f'''JANUS MOSAIC ITERATIVE GENERATOR REPORT:
 Target: {self.target}
 No of filters: {no_of_filters}
 Max smear: {max_smear} px
 Overlap: {overlap:.3f}
 Stabilization time: {stabilization_time_s:.3f} s
 {self.probe} slew rate: {self.slew_rate_in_required_units:.3f} {self.angular_unit} / {self.time_unit}
 Start time: {dm.start_time.isoformat()}
 End time:   {dm.end_time.isoformat()}
 Duration: {duration} 
 Total number of images: {image_count} ({len(dm.center_points)} positions, {no_of_filters} filters at each position).
 Uncompressed data volume: {image_count * self.JANUS_max_Mbits_per_image:.3f} Mbits
 Uncompressed average data rate: {image_count * self.JANUS_max_Mbits_per_image * 1000 / duration.total_seconds():.3f} kbits/s
 Calculated max exposure time: {min(exposure_times_s):.3f} s
 Used exposure time:           {used_exposure_time_s:.3f} s
 Used dwell time: {dwell_time_s:.3f} s ({dmg.dwell_time:.3f} {dmg.time_unit} in generator)
 
 No of iterations: {n_iterations}
 Requested margin: {extra_margin*100:.3f} $
 Real margin:      {(margin + 1 - ratio)*100:.3f} %
 Growth factor:    {ang_diameters[1] / ang_diameters[0]:.3f}

'''
        print(report)
        return dm


if __name__ == '__main__':
    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2030-09-17T12:30:00", "%Y-%m-%dT%H:%M:%S")
    jmg = JanusMosaicGenerator("EUROPA", "min", "deg")
    cm = jmg.generate_mosaic(start_time,
                             max_exposure_time_s=20,
                             max_smear=0.25,
                             stabilization_time_s=5,
                             no_of_filters=4,
                             extra_margin=0.05,
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
