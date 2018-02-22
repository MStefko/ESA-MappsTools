import spiceypy as spy
import numpy as np
import scipy.integrate
from datetime import datetime, timedelta
from matplotlib import pyplot as plt

from mosaics.misc import datetime2et

MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
spy.furnsh(MK_C32)
body = "CALLISTO"

FULL_POWER_W = 725
SCIENCE_ENERGY_14C6_Wh = 4065

CAs = {"14C6": datetime.strptime("2031-04-25T22:40:47", "%Y-%m-%dT%H:%M:%S"),
       "22C11": datetime.strptime("2031-09-27T04:38:01", "%Y-%m-%dT%H:%M:%S") }
hours_from_CA = 12
TD_12h = timedelta(hours=hours_from_CA)
step_s = 20

POWER_W = {}
ENERGY_Wh = {}
for (name, CA) in CAs.items():
    start_et = datetime2et(CA - TD_12h)
    end_et = datetime2et(CA + TD_12h)
    times = np.arange(start_et, end_et, step_s)

    occultations = [spy.occult(body, "ELLIPSOID", "IAU_" + body, "SUN",
                              "POINT", "J2000", "LT+S", "JUICE", t) != 0 for t in times]
    panel_vector = np.array([0.0, 1.0, 0.0])
    sun_positions = [spy.spkpos("SUN", t, "JUICE_SPACECRAFT", "LT+S", "JUICE")[0] for t in
                     times]
    angles = np.array([spy.vsep(panel_vector, sun_p) for sun_p in sun_positions])
    solar_incidences = np.sin(angles)

    POWER_W[name] = FULL_POWER_W * np.array([0.0 if is_occulted else incidence for
                                       (is_occulted, incidence) in zip(occultations, solar_incidences)])
    ENERGY_Ws = scipy.integrate.trapz(POWER_W[name], times)
    ENERGY_Wh[name] = ENERGY_Ws / 3600

X_time_hr = (np.arange(0, 2*hours_from_CA*3600, step_s) / 3600) - hours_from_CA


SCIENCE_ENERGY_22C11_Wh = SCIENCE_ENERGY_14C6_Wh - (ENERGY_Wh["14C6"] - ENERGY_Wh["22C11"])

print(f'''
Available energy for 22C11: {SCIENCE_ENERGY_22C11_Wh:.0f} Wh
Based on difference in power provided by solar panels ({FULL_POWER_W} W at EOL), and available energy for 14C6: {SCIENCE_ENERGY_14C6_Wh} Wh.
''')

ax = plt.gca()
for (name, power_w) in POWER_W.items():
    ax.plot(X_time_hr, power_w, label=f"{name}: {ENERGY_Wh[name]:.0f} Wh")
ax.legend()
ax.set_xlabel("Time from CA [h]")
ax.set_ylabel("Immediate power on solar panels [W]")
ax.set_title("Power availability 14C6 vs 22C11")
ax.set_ylim(bottom=0.0)
ax.grid()
plt.show()