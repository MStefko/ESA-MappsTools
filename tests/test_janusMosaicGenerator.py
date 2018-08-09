from unittest import TestCase
from mapps_tools.mosaics.JanusMosaicGenerator import JanusMosaicGenerator

class TestJanusMosaicGenerator(TestCase):

    def test_initializations(self):
        with self.assertRaises(TypeError):
            JanusMosaicGenerator("")
        with self.assertRaises(TypeError):
            JanusMosaicGenerator(None)
        with self.assertRaises(ValueError):
            JanusMosaicGenerator("CALLISTO", None)
        with self.assertRaises(ValueError):
            JanusMosaicGenerator("CALLISTO", "min", None)
        with self.assertRaises(ValueError):
            JanusMosaicGenerator("CALLISTO", "minute", "deg")
        with self.assertRaises(ValueError):
            JanusMosaicGenerator("CALLISTO", "m", "deg")
        JanusMosaicGenerator("CALLISTO")
        JanusMosaicGenerator("RANCOM_TEXT")
        JanusMosaicGenerator("CALLISTO", "min", "rad")

