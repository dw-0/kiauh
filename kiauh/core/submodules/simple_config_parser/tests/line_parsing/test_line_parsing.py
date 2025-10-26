# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import json
from pathlib import Path

import pytest

from src.simple_config_parser.constants import HEADER_IDENT, LineType
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


def test_section_parsing(parser):
    expected_keys = {"section_1", "section_2", "section_3", "section_4"}
    assert expected_keys.issubset(
        parser.config.keys()
    ), f"Expected keys: {expected_keys}, got: {parser.config.keys()}"
    assert parser.in_option_block is False
    assert parser.current_section == parser.get_sections()[-1]
    assert parser.config["section_2"] is not None
    assert parser.config["section_2"]["header"] == "[section_2] ; comment"
    assert parser.config["section_2"]["elements"] is not None
    assert len(parser.config["section_2"]["elements"]) > 0


def test_option_parsing(parser):
    assert parser.config["section_1"]["elements"][0]["type"] == LineType.OPTION.value
    assert parser.config["section_1"]["elements"][0]["name"] == "option_1"
    assert parser.config["section_1"]["elements"][0]["value"] == "value_1"
    assert parser.config["section_1"]["elements"][0]["raw"] == "option_1: value_1"


def test_header_parsing(parser):
    header = parser.config[HEADER_IDENT]
    assert isinstance(header, list)
    assert len(header) > 0


def test_option_block_parsing(parser):
    section = "section number 5"
    option_block = None
    for element in parser.config[section]["elements"]:
        if (element["type"] == LineType.OPTION_BLOCK.value and
            element["name"] == "multi_option"):
            option_block = element
            break

    assert option_block is not None, "multi_option block not found"
    assert option_block["type"] == LineType.OPTION_BLOCK.value
    assert option_block["name"] == "multi_option"
    assert option_block["raw"] == "multi_option:"

    expected_values = [
        "# these are multi-line values",
        "value_5_1",
        "value_5_2 ; here is a comment",
        "value_5_3"
    ]
    assert option_block["value"] == expected_values, (
        f"Expected values: {expected_values}, "
        f"got: {option_block['value']}"
    )
