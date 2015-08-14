import pytest
import py

__author__ = 'Omer'

from artistworks_downloader.unite import unite_ts_videos

Path = py.path.local

SAMPLE_DIR = Path(__file__).dirpath().join('fixtures').join('samples')