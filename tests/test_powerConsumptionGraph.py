from unittest import TestCase
from os.path import split, join, abspath
from power_analysis import PowerConsumptionGraph


class TestPowerConsumptionGraph(TestCase):
    def setUp(self):
        self.pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
            abspath(join(split(__file__)[0],'14c6_test_attitude_and_data.csv')),
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
