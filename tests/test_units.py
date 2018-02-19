from unittest import TestCase

import numpy as np

from mosaics.units import convertTimeFromTo, convertAngleFromTo


class TestConvertTimeFromTo(TestCase):
    def test_input(self):
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertTimeFromTo(1.3, " min", "sec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertTimeFromTo(1.3, "min", "SEC")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertTimeFromTo(1.3, "", "sec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertTimeFromTo(1.3, None, "sec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertTimeFromTo(1.3, "minaa", "sec")
        with self.assertRaises(TypeError, msg="Invalid value"):
            convertTimeFromTo(None, "min", "sec")
        with self.assertRaises(TypeError, msg="Invalid value"):
            convertTimeFromTo("2.2", "min", "sec")

    def test_conversions(self):
        self.assertEquals(convertTimeFromTo(0.0, "min", "sec"),
                          0.0)
        self.assertEquals(convertTimeFromTo(60.0, "min", "sec"),
                          60.0*60.0)
        self.assertEquals(convertTimeFromTo(2.34, "hour", "sec"),
                          2.34*3600)
        self.assertEquals(convertTimeFromTo(1.0, "hour", "hour"),
                          1.0)
        self.assertEquals(convertTimeFromTo(2.0, "min", "hour"),
                          2.0/60.0)
        self.assertEquals(convertTimeFromTo(-1.3, "min", "sec"),
                          -1.3*60.0)
        self.assertEquals(convertTimeFromTo(-1.3241387498491351, "min", "min"),
                          -1.3241387498491351)


class TestConvertAngleFromTo(TestCase):
    def test_input(self):
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertAngleFromTo(1.3, " min", "sec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertAngleFromTo(1.3, "deg", "sec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertAngleFromTo(1.3, "deg", "ArcSec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertAngleFromTo(1.3, None, "arcSec")
        with self.assertRaises(ValueError, msg="Invalid unit request"):
            convertAngleFromTo(1.3, "deg", "")

    def test_conversions(self):
        self.assertEquals(convertAngleFromTo(0.0, "deg", "rad"),
                          0.0)
        self.assertEquals(convertAngleFromTo(0, "deg", "deg"),
                          0.0)
        self.assertEquals(convertAngleFromTo(0.23184984351384843, "deg", "deg"),
                          0.23184984351384843)
        self.assertEquals(convertAngleFromTo(-3.1689, "deg", "deg"),
                          -3.1689)
        self.assertEquals(convertAngleFromTo(1.0, "deg", "rad"),
                          np.pi/180)
        self.assertAlmostEquals(convertAngleFromTo(4.36, "arcSec", "rad"),
                          2.114e-5, places=4)
        self.assertAlmostEquals(convertAngleFromTo(14.36, "arcSec", "arcMin"),
                          0.23933, places=4)
        self.assertAlmostEquals(convertAngleFromTo(814.21, "deg", "arcMin"),
                          48842.8, places=0)

