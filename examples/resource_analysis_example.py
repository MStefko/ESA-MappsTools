# coding=utf-8

from resource_analysis import PowerConsumptionGraph
# Import MAPPS datapack containing spacecraft resource data
# First we analyze power consumption
pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
                            r"..\tests\14c6_test_power_and_data.csv",
                            power_limit_Wh=4065.0,
                            add_HAA=True # we manually add HAA because it is not tracked by MAPPS
                            )

# Show total power consumed and individual instruments
pcg.print_total_power_consumed()
pcg.print_individual_instrument_consumption()

pcg.plot()

from resource_analysis import DataConsumptionGraph
# We can use the same datapack, as long as it contains
# required fields with data consumption values.
dcg = DataConsumptionGraph("14C6", '2031-04-25T22:40:47',
                           r"..\tests\14c6_test_power_and_data.csv",
                           data_limit_Mbits=30000.0,
                           add_HAA=True)
dcg.print_total_data_acquired()
dcg.print_individual_instrument_data()

dcg.plot()

# Constraining a time interval
pcg2 = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
                             r"..\tests\14c6_test_power_and_data.csv",
                             power_limit_Wh=3000.0,
                             add_HAA=False,
                             time_interval_h=(-8, +8))

pcg2.plot()