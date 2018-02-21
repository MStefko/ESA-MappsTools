# coding=utf-8

from datetime import datetime

# Load the CREMA3.2 metakernel
import spiceypy as spy
MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
spy.furnsh(MK_C32)

from mosaics import JanusMosaicGenerator

# Start time of mosaic during 14C6 ingress
# This function parses the iso8601 timestamp into a datetime object
start_time = datetime.strptime("2031-04-25T18:40:47", "%Y-%m-%dT%H:%M:%S")

# We want a mosaic of Callisto, with units of minutes and degrees
generator = JanusMosaicGenerator("CALLISTO", "min", "deg")

# Generate a DiskMosaic
disk_mosaic = generator.generate_mosaic(
    start_time, # mandatory first argument, the start time
    max_exposure_time_s=15, # maximal time of one exposure, the generator can decide to make it lower
    duration_guess_minutes=30, # estimate of how long the mosaic will be, to compensate for growth over time
    max_smear=0.25, # set max smearing during one exposure to 1/4 of pixel
    stabilization_time_s=5, # stabilization time after each position change
    no_of_filters=4, # number of filters used at each position
    extra_margin=0.05, # margin of 5% around the edge of body (e.g. to capture the atmosphere)
    overlap=0.1, # minimal overlap of 10% between neighboring frames
    sunside=False # we want a full-disk mosaic
    )

print(disk_mosaic.generate_PTR(decimal_places=2))

disk_mosaic.plot()

sunside_mosaic = generator.generate_mosaic(
    start_time,
    max_exposure_time_s=15,
    duration_guess_minutes=30,
    max_smear=0.25,
    stabilization_time_s=5,
    no_of_filters=4,
    extra_margin=0.05,
    overlap=0.1,
    sunside=True # we want to image the sun-illuminated side of Callisto
    )

print(sunside_mosaic.generate_PTR(decimal_places=2))

sunside_mosaic.plot()

