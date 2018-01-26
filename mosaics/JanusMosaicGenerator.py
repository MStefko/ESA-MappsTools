# coding=utf-8
from datetime import datetime, timedelta

from mosaics.DiskMosaic import DiskMosaic
from mosaics.DiskMosaicGenerator import DiskMosaicGenerator
from mosaics.misc import get_max_dwell_time_s, get_body_angular_diameter_rad

import numpy as np
import spiceypy as spy

class JanusMosaicGenerator:
    JANUS_FOV_SIZE_DEG = (1.72, 1.29)
    JANUS_FOV_RES = (2000, 1504)
    probe = "JUICE"
    JUICE_SLEW_RATE_DEG_PER_SEC = 0.025
    FILTER_SWITCH_DURATION_SECONDS = 5.0
    JANUS_max_Mbits_per_image = JANUS_FOV_RES[0] * JANUS_FOV_RES[1] * 14 / 1_000_000

    time_unit_conversions_from_sec = {"sec": 1.0, "min": 1/60.0, "hour": 1/3600}
    angular_unit_conversions_from_deg = {"deg": 1.0, "rad": np.pi/180, "arcMin": 3438*np.pi/180,
                                         "arcSec": 206265*np.pi/180}

    def __init__(self, target: str, time_unit: str = "min", angular_unit: str = "deg"):
        """ Creates a JanusMosaicGenerator

        :param target: target body, e.g. "CALLISTO"
        :param time_unit: Unit for temporal values - "sec", "min" or "hour"
        :param angular_unit: Unit for angular values - "deg", "rad", "arcMin" or "arcSec"
        """
        self.target = target
        if time_unit not in DiskMosaic.allowed_time_units:
            raise ValueError(f"Time unit must be one of following: {DiskMosaic.allowed_time_units}")
        self.time_unit = time_unit
        if angular_unit not in DiskMosaic.allowed_angular_units:
            raise ValueError(f"Angular unit must be one of following: {DiskMosaic.allowed_angular_units}")
        self.angular_unit = angular_unit

        # Convert JANUS FOV size from radians to required angular unit
        self.fov_size = tuple(v_rad * self.angular_unit_conversions_from_deg[angular_unit] for v_rad in self.JANUS_FOV_SIZE_DEG)

    def _get_max_dwell_time_s(self, max_smear: float, time: datetime) -> float:
        return get_max_dwell_time_s(max_smear, self.probe, self.target, time,
                                    self.JANUS_FOV_SIZE_DEG[0], self.JANUS_FOV_RES[0])

    def create_optimized_mosaic(self, time: datetime, max_exposure_time_s: float,
                                duration_guess_minutes: float = 30, stabilization_time_s: float = 0.0,
                                max_smear: float = 0.25, no_of_filters: int = 1, margin: float = 0.1):
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
        exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in range(int(duration_guess_minutes))]
        used_exposure_time_s = min(exposure_times_s + [max_exposure_time_s])
        dwell_time_s = stabilization_time_s + \
                     used_exposure_time_s * no_of_filters + \
                     self.FILTER_SWITCH_DURATION_SECONDS * (no_of_filters - 1)

        slew_rate_in_required_units = self.JUICE_SLEW_RATE_DEG_PER_SEC \
                                      * self.angular_unit_conversions_from_deg[self.angular_unit] \
                                      / self.time_unit_conversions_from_sec[self.time_unit]


        dmg = DiskMosaicGenerator(self.fov_size, "JUICE", self.target, time, self.time_unit,
                                  self.angular_unit, dwell_time_s * self.time_unit_conversions_from_sec[self.time_unit],
                                  slew_rate_in_required_units)

        overlap = 0.1
        dm = dmg.generate_symmetric_mosaic(margin=margin, min_overlap=overlap)

        image_count = len(dm.center_points) * no_of_filters
        duration = dm.end_time - dm.start_time

        report = \
f'''JANUS MOSAIC GENERATOR REPORT:
 Target: {self.target}
 No of filters: {no_of_filters}
 Max smear: {max_smear} px
 Stabilization time: {stabilization_time_s:.3f} s
 {self.probe} slew rate: {slew_rate_in_required_units:.3f} {self.angular_unit} / {self.time_unit}
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
        duration_minutes = duration.total_seconds()/60
        if duration_minutes > duration_guess_minutes:
            exposure_times_s = [self._get_max_dwell_time_s(max_smear, time + timedelta(minutes=m)) for m in range(int(duration_minutes))]
            if min(exposure_times_s) < used_exposure_time_s:
                warning = \
f"""*** POST-GENERATION WARNING ***
 Chosen exposure time ({used_exposure_time_s:.3f} s) is larger than maximal allowed exposure time ({min(exposure_times_s):.3f} s).
 Either set duration_guess_minutes to value at least {duration_minutes:.3f}, or set exposure time to less than {min(exposure_times_s):.3f} s. 
*** END WARNING ***
"""
                print(warning)

        return dm

if __name__=='__main__':
    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2031-04-25T18:40:47", "%Y-%m-%dT%H:%M:%S")
    jmg = JanusMosaicGenerator("CALLISTO", "min", "deg")
    dm = jmg.create_optimized_mosaic(start_time,
                                     max_exposure_time_s=30,
                                     max_smear=0.25,
                                     stabilization_time_s=5,
                                     no_of_filters=4,
                                     margin=0.20,
                                     duration_guess_minutes=30)
    print(dm.generate_PTR(decimal_places=3))
    dm.plot()



