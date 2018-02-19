from unittest import TestCase
from os.path import split, join, abspath
from power_analysis import PowerConsumptionGraph


class TestPowerConsumptionGraph14C6(TestCase):
    def setUp(self):
        self.pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
            abspath(join(split(__file__)[0],'14c6_test_power_and_data.csv')),
            power_limit_Wh=4065.0)

    def test_print_total_power_consumed(self):
        ref = "Total power consumed: 4199.2 (103.3% of limit)."
        self.assertEqual(self.pcg.print_total_power_consumed(), ref)

    def test_print_individual_instrument_consumption(self):
        ref = \
"""Consumption by instrument:
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
 - UVS  :   105.4 Wh -  2.5%
"""
        self.assertEqual(self.pcg.print_individual_instrument_consumption(), ref)

class TestPowerConsumptionGraph6E1(TestCase):
    def setUp(self):
        self.pcg = PowerConsumptionGraph("6E1", '2030-10-05T02:24:00',
            abspath(join(split(__file__)[0],'6e1_test_power.csv')),
            power_limit_Wh=4000.0, time_interval_h=[-8.0, 12.0],
            add_HAA=False)

    def test_print_total_power_consumed(self):
        ref = "Total power consumed: 3996.7 (99.9% of limit)."
        self.assertEqual(self.pcg.print_total_power_consumed(), ref)

    def test_print_individual_instrument_consumption(self):
        ref = \
"""Consumption by instrument:
 - JMAG :   361.1 Wh -  9.0%
 - PEP  :  1238.6 Wh - 31.0%
 - 3GM  :   941.3 Wh - 23.6%
 - RPWI :   237.1 Wh -  5.9%
 - SWI  :   472.9 Wh - 11.8%
 - RIME :    11.1 Wh -  0.3%
 - JANUS:   344.5 Wh -  8.6%
 - MAJIS:   239.9 Wh -  6.0%
 - GALA :    31.8 Wh -  0.8%
 - UVS  :   118.4 Wh -  3.0%
"""
        self.assertEqual(self.pcg.print_individual_instrument_consumption(), ref)
