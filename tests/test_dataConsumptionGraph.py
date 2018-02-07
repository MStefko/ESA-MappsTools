from unittest import TestCase
from os.path import split, join, abspath

from power_analysis import DataConsumptionGraph


class TestDataConsumptionGraph(TestCase):
    def setUp(self):
        self.dcg = DataConsumptionGraph("14C6", '2031-04-25T22:40:47',
            abspath(join(split(__file__)[0],'14c6_test_attitude_and_data.csv')),
            data_limit_Mbits=30000.0)

    def test_print_total_data_acquired(self):
        ref = "Total data acquired: 36896.2 Mbits (123.0% of limit)."
        self.assertEqual(self.dcg.print_total_data_acquired(), ref)

    def test_print_individual_instrument_data(self):
        ref = \
"""Consumption by instrument:
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
 - UVS  :  1544.9 Mbits -  4.2%
"""
        self.assertEqual(self.dcg.print_individual_instrument_data(), ref)
