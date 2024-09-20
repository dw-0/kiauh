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


def test_get_conv(parser):
    # Test conversion to int
    should_be_int = parser._get_conv("section_1", "option_1_2", int)
    assert isinstance(should_be_int, int)

    # Test conversion to float
    should_be_float = parser._get_conv("section_1", "option_1_3", float)
    assert isinstance(should_be_float, float)

    # Test conversion to boolean
    should_be_bool = parser._get_conv(
        "section_1", "option_1_1", parser._convert_to_boolean
    )
    assert isinstance(should_be_bool, bool)

    # Test fallback for int
    should_be_fallback_int = parser._get_conv(
        "section_1", "option_128", int, fallback=128
    )
    assert isinstance(should_be_fallback_int, int)
    assert should_be_fallback_int == 128

    # Test fallback for float
    should_be_fallback_float = parser._get_conv(
        "section_1", "option_128", float, fallback=1.234
    )
    assert isinstance(should_be_fallback_float, float)
    assert should_be_fallback_float == 1.234

    # Test fallback for boolean
    should_be_fallback_bool = parser._get_conv(
        "section_1", "option_128", parser._convert_to_boolean, fallback=True
    )
    assert isinstance(should_be_fallback_bool, bool)
    assert should_be_fallback_bool is True

    # Test ValueError exception for invalid int conversion
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", int)

    # Test ValueError exception for invalid float conversion
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", float)

    # Test ValueError exception for invalid boolean conversion
    with pytest.raises(ValueError):
        parser._get_conv("section_1", "option_1", parser._convert_to_boolean)
