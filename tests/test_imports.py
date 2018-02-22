# coding=utf-8

from unittest import TestCase

class TestImports(TestCase):

    def test_import_spiceypy(self):
        import spiceypy
        self.assertTrue(spiceypy.tkvrsn('TOOLKIT') >= "CSPICE_N0066")