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
from tests.utils import load_testdata_from_file

BASE_DIR = Path(__file__).parent.parent.joinpath("assets")
TEST_DATA_PATH = BASE_DIR.joinpath("test_config_1.cfg")


@pytest.fixture
def parser():
    parser = SimpleConfigParser()
    for line in load_testdata_from_file(TEST_DATA_PATH):
        parser._parse_line(line)  # noqa

    return parser


def test_get_int_conv(parser):
    should_be_int = parser._get_conv("section_1", "option_1_2", int)
    assert isinstance(should_be_int, int)


def test_get_float_conv(parser):
    should_be_float = parser._get_conv("section_1", "option_1_3", float)
    assert isinstance(should_be_float, float)


def test_get_bool_conv(parser):
    should_be_bool = parser._get_conv(
        "section_1", "option_1_1", parser._convert_to_boolean
    )
    assert isinstance(should_be_bool, bool)


def test_get_int_conv_fallback(parser):
    should_be_fallback_int = parser._get_conv(
        "section_1", "option_128", int, fallback=128
    )
    assert isinstance(should_be_fallback_int, int)
    assert should_be_fallback_int == 128
    assert parser._get_conv("section_1", "option_128", int, None) is None


def test_get_float_conv_fallback(parser):
    should_be_fallback_float = parser._get_conv(
        "section_1", "option_128", float, fallback=1.234
    )
    assert isinstance(should_be_fallback_float, float)
    assert should_be_fallback_float == 1.234

    assert parser._get_conv("section_1", "option_128", float, None) is None


def test_get_bool_conv_fallback(parser):
    should_be_fallback_bool = parser._get_conv(
        "section_1", "option_128", parser._convert_to_boolean, fallback=True
    )
    assert isinstance(should_be_fallback_bool, bool)
    assert should_be_fallback_bool is True

    assert (
        parser._get_conv("section_1", "option_128", parser._convert_to_boolean, None)
        is None
    )


def test_get_int_conv_exception(parser):
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", int)


def test_get_float_conv_exception(parser):
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", float)


def test_get_bool_conv_exception(parser):
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", parser._convert_to_boolean)
