# coding=utf-8
from datetime import datetime
import spiceypy as spy
MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
spy.furnsh(MK_C32)

from mosaics.JanusMosaicGenerator import JanusMosaicGenerator

# JANUS disk mosaic of Callisto during 14C6 ingress
jmg = JanusMosaicGenerator("CALLISTO", "min", "deg")
start_time = datetime.strptime("2031-04-25T18:40:47", "%Y-%m-%dT%H:%M:%S")
dm = jmg.generate_optimized_mosaic_iterative(start_time,
                                             max_exposure_time_s=15,
                                             max_smear=0.25,
                                             stabilization_time_s=5,
                                             no_of_filters=4,
                                             extra_margin=0.05)
print(dm.generate_PTR(decimal_places=3))
dm.plot()

# JANUS mosaic of sun-illuminated surface of Europa during 6E1 egress
start_time = datetime.strptime("2030-09-17T12:30:00", "%Y-%m-%dT%H:%M:%S")
jmg = JanusMosaicGenerator("EUROPA", "min", "deg")
cm = jmg.generate_sunside_mosaic(start_time,
                                 duration_guess_minutes=30,
                                 max_exposure_time_s=20,
                                 max_smear=0.25,
                                 stabilization_time_s=5,
                                 no_of_filters=4,
                                 extra_margin=0.05,
                                 overlap=0.15)

cm.plot()
print(cm.generate_PTR(decimal_places=3))