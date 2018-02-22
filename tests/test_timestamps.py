from unittest import TestCase
import filecmp

import os

from mapps_tools.timestamps import TimestampProcessor
from iso8601 import ParseError

unparseable_inputs = ['24:00:00', '-24:00:00', '00:60:00', '01:65:30', '--1:31:01',
                '-23:59:60', '23:59:60', 'aaa', '+1 day, 0:00:00',
                '', ' ', '\n']

class TestUtc2Delta(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processor = TimestampProcessor('2031-04-25T22:40:47Z')

    def test_positive_delta(self):
        self.assertEqual(self.processor.utc2delta('2031-04-25T23:42:50'),
                         '+01:02:03')
        self.assertEqual(self.processor.utc2delta('2031-04-26T22:40:46Z'),
                         '+23:59:59')

    def test_negative_delta(self):
        self.assertEqual(self.processor.utc2delta('2031-04-25T10:35:40Z'),
                         '-12:05:07')
        self.assertEqual(self.processor.utc2delta('2031-04-24T22:40:48'),
                         '-23:59:59')

    def test_zero_delta(self):
        self.assertEqual(self.processor.utc2delta('2031-04-25T22:40:47Z'),
                         '+00:00:00')

    def test_over_24h_exception(self):
        self.assertRaises(ValueError, self.processor.utc2delta, '2031-04-26T22:40:47Z')
        self.assertRaises(ValueError, self.processor.utc2delta, '2031-04-24T22:40:47Z')

    def test_over_24h_pass(self):
        self.assertEqual(self.processor.utc2delta('2031-04-26T22:40:47', enforce_24h=False),
                         '+1 day, 0:00:00')
        self.assertEqual(self.processor.utc2delta('2031-04-24T21:39:46', enforce_24h=False),
                         '-1 day, 1:01:01')

    def test_unparseable_inputs(self):
        for wrong_input in unparseable_inputs:
            self.assertRaises(ParseError, self.processor.utc2delta, wrong_input)

class TestDelta2Utc(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processor = TimestampProcessor('2031-04-25T22:40:47Z')

    def test_positive_delta(self):
        self.assertEqual(self.processor.delta2utc('+01:02:03'),
                         '2031-04-25T23:42:50')
        self.assertEqual(self.processor.delta2utc('+23:59:59'),
                         '2031-04-26T22:40:46')

    def test_negative_delta(self):
        self.assertEqual(self.processor.delta2utc('-12:05:07'),
                         '2031-04-25T10:35:40')
        self.assertEqual(self.processor.delta2utc('-23:59:59'),
                         '2031-04-24T22:40:48')

    def test_zero_delta(self):
        self.assertEqual(self.processor.delta2utc('+00:00:00'),
                         '2031-04-25T22:40:47')
        self.assertEqual(self.processor.delta2utc('-00:00:00'),
                         '2031-04-25T22:40:47')
        self.assertEqual(self.processor.delta2utc('00:00:00'),
                         '2031-04-25T22:40:47')

    def test_unparseable_inputs(self):
        for wrong_input in unparseable_inputs:
            self.assertRaises(ValueError, self.processor.delta2utc, wrong_input)

class TestItlParser(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processor = TimestampProcessor('2031-04-25T22:40:47Z')

    def test_compare_files(self):
        input_itl = os.path.join(os.path.split(__file__)[0],'itl_file_in.itl')
        output_itl = os.path.join(os.path.split(__file__)[0],'itl_file_out.itl')
        reference_output_itl = os.path.join(os.path.split(__file__)[0],'itl_file_ref.itl')
        self.processor.absolute_to_relative_timestamps_itl(input_itl,
                       output_itl, "CLS_APP_CAL", overwrite=True)
        self.assertTrue(filecmp.cmp(output_itl, reference_output_itl, shallow=False),
            f"Files '{output_itl}' does not match reference '{reference_output_itl}'.")