# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

from src.simple_config_parser.simple_config_parser import SimpleConfigParser

BASE_DIR = Path(__file__).parent.parent / "assets"
TEST_DATA_PATH = BASE_DIR / "test_config_1.cfg"


@pytest.fixture
def parser():
    p = SimpleConfigParser()
    p.read_file(TEST_DATA_PATH)
    return p


def test_get_int_conv(parser):
    assert parser.getint("section_1", "option_1_2") == 5


def test_get_float_conv(parser):
    assert pytest.approx(parser.getfloat("section_1", "option_1_3"), rel=1e-9) == 1.123


def test_get_bool_conv(parser):
    assert parser.getboolean("section_1", "option_1_1") is True


def test_get_int_conv_fallback(parser):
    assert parser.getint("section_1", "missing", fallback=128) == 128
    with pytest.raises(Exception):
        parser.getint("section_1", "missing")


def test_get_float_conv_fallback(parser):
    assert parser.getfloat("section_1", "missing", fallback=1.234) == 1.234
    with pytest.raises(Exception):
        parser.getfloat("section_1", "missing")


def test_get_bool_conv_fallback(parser):
    assert parser.getboolean("section_1", "missing", fallback=True) is True
    with pytest.raises(Exception):
        parser.getboolean("section_1", "missing")


def test_get_int_conv_exception(parser):
    with pytest.raises(ValueError):
        parser.getint("section_1", "option_1")


def test_get_float_conv_exception(parser):
    with pytest.raises(ValueError):
        parser.getfloat("section_1", "option_1")


def test_get_bool_conv_exception(parser):
    with pytest.raises(ValueError):
        parser.getboolean("section_1", "option_1")
