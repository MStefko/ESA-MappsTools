# coding=utf-8
""" Mosaics module: This module provides two instrument-specific generators:

- JanusMosaicGenerator: Creating mosaics optimized for JUICE-JANUS imaging.
- MajisScanGenerator: Creating scans (series of vertical slews) optimized for
  JUICE-MAJIS imaging.
"""

from .JanusMosaicGenerator import JanusMosaicGenerator
from .MajisScanGenerator import MajisScanGenerator
