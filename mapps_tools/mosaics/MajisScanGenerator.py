# coding=utf-8
from datetime import datetime

from .units import angular_units, time_units, convertAngleFromTo, convertTimeFromTo
import spiceypy as spy

from mapps_tools.mosaics.Scan import Scan
from mapps_tools.mosaics.ScanGenerator import ScanGenerator


class MajisScanGenerator:
    """ Generator for scans optimized for MAJIS FOV.

    Methods:
        generate_scan(): Creates either a full-body vertical scan (scanning along y-axis),
        or a vertical scan that covers the sun-illuminated portion of target.
    """
    MAJIS_FOV_WIDTH_DEG = 3.4
    MAJIS_FOV_RES = (480, 1)
    # FOV height is 125 urad
    MAJIS_FOV_HEIGHT_DEG = convertAngleFromTo(125e-6, "rad", "deg")
    probe = "JUICE"
    MAJIS_max_Mbits_per_line = 7.168
    JUICE_SLEW_RATE_DEG_PER_SEC = 0.025

    def __init__(self, target: str, time_unit: str = "min", angular_unit: str = "deg"):
        """ Creates a MajisSlewGenerator

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

        self.fov_width = convertAngleFromTo(self.MAJIS_FOV_WIDTH_DEG, "deg", angular_unit)
        # the time unit arguments are in opposite order because slew rate has time in denominator
        self.transfer_slew_rate_in_required_units = convertTimeFromTo(
            convertAngleFromTo(self.JUICE_SLEW_RATE_DEG_PER_SEC,
                               "deg", self.angular_unit), self.time_unit, "sec")

    def generate_scan(self, time: datetime, exposure_time_s: float,
                      margin: float = 0.1, overlap: float = 0.1, sunside: bool = False) -> Scan:
        """ Creates a scan symmetric about the Y coordinate axis. Positions and lengths of
        individual vertical slews are optimized according to body dimensions and requirements.

        A report of the generator is printed to standard output.

        :param time: Start time of slew as datetime object.
        :param exposure_time_s: Exposure time for one line in the scan
        (meaning one horizontal line of 480x1 pixels), in seconds. Must be larger than 0.
        :param margin: Extra space left around the body disk in units of body radii. This
        effectively increases the presumed size of object. For example, a value of 0.1 would
        cause the scan to also cover the atmosphere around the object, up to the altitude of
        10% of body radius.
        :param overlap: Minimal required overlap of neighboring slews. For example, if this
        is set to 0.1, then at least 10% of given slew overlaps with its neighbor on left
        and right. Must be between 0.0 and 1.0
        :param sunside: If set to True, only the sun-illuminated surface is covered. Otherwise
        the whole body is imaged. Default is False - full-disk imaging.
        :return: Generated Scan.
        """
        if exposure_time_s <= 0.0:
            raise ValueError("Exposure time must be positive.")
        if margin < -1.0:
            raise ValueError("Margin must be more than -1.0")
        if overlap < 0.0 or overlap >= 1.0:
            raise ValueError("Overlap must be between 0.0 and 1.0")

        # compute measurement slew rate
        fov_height_in_required_units = convertAngleFromTo(self.MAJIS_FOV_HEIGHT_DEG, "deg", self.angular_unit)
        exposure_time_in_required_units = convertTimeFromTo(exposure_time_s, "sec", self.time_unit)
        measurement_slew_rate = fov_height_in_required_units / exposure_time_in_required_units

        sg = ScanGenerator(self.fov_width, self.probe, self.target,
                           time, self.time_unit, self.angular_unit,
                           measurement_slew_rate, self.transfer_slew_rate_in_required_units)
        if sunside:
            s = sg.generate_sunside_scan(margin=margin, min_overlap=overlap)
        else:
            s = sg.generate_symmetric_scan(margin=margin, min_overlap=overlap)

        duration = s.end_time - s.start_time
        rectangles = s.rectangles
        total_vertical_length = sum([r.size[1] for r in rectangles])
        no_of_horizontal_lines = total_vertical_length / convertAngleFromTo(self.MAJIS_FOV_HEIGHT_DEG,
                                                                            "deg", self.angular_unit)
        total_data_Mbits = no_of_horizontal_lines * self.MAJIS_max_Mbits_per_line

        report = \
            f'''MAJIS SCAN GENERATOR REPORT:
             Scan type: {"Sunside" if sunside else "Full disk"}
             Target: {self.target}
             {self.probe} slew rate: {self.transfer_slew_rate_in_required_units:.3f} {self.angular_unit} / {self.time_unit}
             Start time: {s.start_time.isoformat()}
             End time:   {s.end_time.isoformat()}
             Duration: {duration} 
             Total number of vertical scans: {len(s.center_points)}
             Uncompressed data volume: {total_data_Mbits:.3f} Mbits
             Uncompressed average data rate: {total_data_Mbits * 1000 / duration.total_seconds():.3f} kbits/s
             Line exposure time: {exposure_time_s:.3f} s
             Scan slew rate: {measurement_slew_rate} {self.angular_unit}/{self.time_unit}
            '''
        print(report)
        return s


if __name__=="__main__":
    MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
    spy.furnsh(MK_C32)

    start_time = datetime.strptime("2031-09-27T09:50:00", "%Y-%m-%dT%H:%M:%S")
    # start_time = datetime.strptime("2031-04-25T19:20:00", "%Y-%m-%dT%H:%M:%S")
    msg = MajisScanGenerator("CALLISTO", "min", "deg")
    sc = msg.generate_scan(start_time,
                           2,
                           margin=0.05,
                           overlap=0.05)

    print(sc.generate_PTR(decimal_places=2))
    sc.plot()

