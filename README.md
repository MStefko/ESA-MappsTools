# SpiceTools
This repository contains assorted modules for working with MAPPS and
Spice, e.g. manipulating timestamps, analyzing power consumption,
and generating mosaic instructions.

# Feature overview

## Resource analysis of MAPPS datapacks

![](doc/img/power_data_graph.png)

## Generation of JANUS mosaics and PTR requests

One can generate either a full-disk mosaic, or mosaic of the sun-illuminated
surface of a body.

<img src="doc/img/mosaic_14C6_sunside_JANUS.png" width="450"> ![](doc/img/video_14C6_sunside_JANUS.mp4)

## Generation of MAJIS slews and PTR requests
Again, the slew can either cover the whole disk, or only the sun-illuminated portion.

<img src="doc/img/scan_22C11_full_MAJIS.png" width="450"> ![](doc/img/video_22C11_full_MAJIS.mp4)

## Timestamp processing
Translating between relative and absolute timestamps in MAPPS config files, e.g.
`CLS_APP_CAL +06:28:00` to `2031-04-26T05:08:47Z`, and vice versa.

## Detailed features & how-tos

## timestamps.py

 - Batch process timestamps in ITL files.

```python
>>> from timestamps import TimestampProcessor
>>> p = TimestampProcessor('2031-04-25T22:40:47')
>>> p.utc2delta('2031-04-25T23:42:50')
'+01:02:03'
>>> p.delta2utc('+01:02:03')
'2031-04-25T23:42:50'
>>> p.absolute_to_relative_timestamps_itl(
...     'tests\\test_itl_file_in.itl',
...     'tests\\test_itl_file_out.itl',
...     "CLS_APP_CAL")
>>> import filecmp
>>> filecmp.cmp('tests\\test_itl_file_out.itl',
...             'tests\\test_itl_file_ref.itl',
...             shallow=False)
True
```

## power_analysis.py
Perform analysis of consumed resources on a MAPPS scenario.
```python
>>> from matplotlib import pyplot as plt
>>> from power_analysis import PowerConsumptionGraph
# Import MAPPS datapack containing spacecraft resource data
>>> pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
...                            r"tests\14c6_test_attitude_and_data.csv",
...                            power_limit_Wh=4065.0)
>>> pcg.print_total_power_consumed()
'Total power consumed: 4199.1 (103.3% of limit).'
>>> pcg.print_individual_instrument_consumption()
'Consumption by instrument:
 - HAA  :   360.0 Wh -  8.6%
 - JMAG :   243.6 Wh -  5.8%
 - PEP  :  1495.1 Wh - 35.6%
 - 3GM  :   670.0 Wh - 16.0%
 - RPWI :   280.1 Wh -  6.7%
 - SWI  :   529.4 Wh - 12.6%
 - RIME :    10.5 Wh -  0.2%
 - JANUS:   316.0 Wh -  7.5%
 - MAJIS:   157.5 Wh -  3.8%
 - GALA :    31.5 Wh -  0.8%
 - UVS  :   105.3 Wh -  2.5%'
>>> pcg.plot()
>>> plt.show()
```

![](doc/img/power_graph.png)

```python
>>> from power_analysis import DataConsumptionGraph
# We can use the same datapack, as long as it contains required fields
# with data consumption values.
>>> dcg = DataConsumptionGraph("14C6", '2031-04-25T22:40:47',
...                            r"tests\14c6_test_attitude_and_data.csv",
...                            data_limit_Mbits=30000.0)
>>> dcg.print_total_data_acquired()
'Total data acquired: 36896.2 Mbits (123.0% of limit).'
>>> dcg.print_individual_instrument_data()
'Consumption by instrument:
 - HAA  :   172.8 Mbits -  0.5%
 - JMAG :   303.4 Mbits -  0.8%
 - PEP  :   561.3 Mbits -  1.5%
 - 3GM  :     5.8 Mbits -  0.0%
 - RPWI :  2054.5 Mbits -  5.6%
 - SWI  :    19.4 Mbits -  0.1%
 - RIME :   249.3 Mbits -  0.7%
 - JANUS:  11184.8 Mbits - 30.3%
 - MAJIS:  20734.1 Mbits - 56.2%
 - GALA :    66.0 Mbits -  0.2%
 - UVS  :  1544.9 Mbits -  4.2%'
>>> dcg.plot()
>>> plt.show()
```

![](doc/img/data_graph.png)

## mosaics
This module allows you to automatically create mosaics and scans of either the full
disk of a certain body, or of the sun-illuminated part.

See tutorials:
 - **[JANUS mosaics](doc/JANUS_mosaics.md)**
 - **[MAJIS scans](doc/MAJIS_scans.md)**

Example scripts are also available in the [examples](examples/) folder.

## flybys.py
Tools for analyzing various properties of flybys such as surface coverage, resolution,
altitude, etc.

```python
>>> import spiceypy as spy
>>> from flybys import Flyby
'CSPICE_N0066
Numpy version: 1.13.3'
>>> # Load the CREMA3.2 metakernels for JUICE
>>> MK_C32 = r"C:\Users\Marcel Stefko\Kernels\JUICE\mk\juice_crema_3_2_v151.tm"
>>> spy.furnsh(MK_C32)
>>> # Analyze Callisto flyby
>>> C = Flyby("CALLISTO", spy.str2et("25 Apr 2031 12:00"), 300000, name="14C6_c3.2", step=1.0, count=5000)
'Analyzing flyby 14C6_c3.2...'
>>> C.print_properties()
'Flyby properties: 14C6_c3.2
 - Body: CALLISTO
 - Closest approach:
    - Time: 2031 APR 25 22:40:46
    - Alt: 199.1 km
    - Lon: 35.3 deg
    - Lat: -25.1 deg
 - Start: 2031 APR 25 05:22:40
 - End:   2031 APR 26 15:55:19
 - Max alt: 300000.0 km'
>>> # Unload metakernel
>>> spy.unload(MK_C32)

>>> from mpl_toolkits.basemap import Basemap
>>> from matplotlib import pyplot as plt
>>> map = Basemap()
>>> map.drawmeridians(np.arange(0,360,30))
>>> map.drawparallels(np.arange(-90,90,30))
>>> a = C.plot_ground_track_to_map(map, c=C.get_nadir_solar_angle(), cmap="plasma", vmin=0, vmax=90.0, s=1)
>>> a.cmap.set_under('g')
>>> plt.title('Solar incidence (green = shade) [-]')
>>> plt.colorbar(shrink=0.55)
>>> plt.show()
```

![](doc/img/14C6_map.png)

```python
>>> C.plot_profile(plt.gcf())
>>> plt.show()
```

![](doc/img/14C6_profile.png)