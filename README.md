# SpiceTools
This repository contains assorted modules for working with MAPPS and
Spice, e.g. manipulating timestamps, analyzing power consumption,
and generating mosaic instructions.

## Available packages

##### timestamps.py
 - Translating between relative and absolute timestamps, e.g.
 `CLS_APP_CAL +06:28:00` to `2031-04-26T05:08:47Z`, and vice versa.
 - Batch processing timestamps in ITL files.

##### power_analysis.py
Performing analysis of consumed resources on MAPPS output data:
```python
from matplotlib import pyplot as plt
from power_analysis import PowerConsumptionGraph

pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
                            r"C:\MAPPS\JUICE_SO\MAPPS\OUTPUT_DATA\14C6_COMPLETE_test_resources.csv",
                            power_limit_Wh=4065.0)
pcg.print_total_power_consumed()
pcg.print_individual_instrument_consumption()
fig = pcg.plot()
plt.show()
```

<img src="img/power_graph.png" style="width: 300px;"/>
