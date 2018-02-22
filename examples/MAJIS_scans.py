# coding=utf-8

from datetime import datetime

# Load the CREMA3.2 metakernel
import spiceypy as spy
MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
spy.furnsh(MK_C32)

from spice_tools.mosaics import MajisScanGenerator

# Start time of scan during 22C11 egress
# This function parses the iso8601 timestamp into a datetime object
start_time = datetime.strptime("2031-09-27T09:50:00", "%Y-%m-%dT%H:%M:%S")

# We want a scan of Callisto, with units of minutes and degrees
generator = MajisScanGenerator("CALLISTO", "min", "deg")

# Generate a disk scan
disk_scan = generator.generate_scan(
    start_time,
    exposure_time_s=2,  # 2 seconds exposure per one horizontal line
    margin=0.05, # margin of 5% around the edge of body (e.g. to capture the atmosphere)
    overlap=0.05 # minimal overlap of 5% between neighboring vertical slews
    )

print(disk_scan.generate_PTR(decimal_places=2))

disk_scan.plot()

# Generate a sunside scan during 14C6 ingress
start_time_14C6 = datetime.strptime("2031-04-25T19:20:00", "%Y-%m-%dT%H:%M:%S")
sunside_scan = disk_scan = generator.generate_scan(
    start_time_14C6,
    exposure_time_s=2,
    margin=0.30, # we need a larger margin because Callisto grows over the course of scan
    overlap=0.05,
    sunside=True # we want a sunside scan
    )

print(sunside_scan.generate_PTR(decimal_places=2))

sunside_scan.plot()