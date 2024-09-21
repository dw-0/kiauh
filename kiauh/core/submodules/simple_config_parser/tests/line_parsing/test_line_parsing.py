# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

from src.simple_config_parser.constants import HEADER_IDENT
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
    assert parser.current_section == "section number 5"
    assert parser.config["section_2"]["_raw"] == "[section_2] ; comment"


def test_option_parsing(parser):
    assert parser.config["section_1"]["option_1"]["value"] == "value_1"
    assert parser.config["section_1"]["option_1"]["_raw"] == "option_1: value_1"
    assert parser.config["section_3"]["option_3"]["value"] == "value_3"
    assert (
        parser.config["section_3"]["option_3"]["_raw"] == "option_3: value_3 # comment"
    )


def test_header_parsing(parser):
    header = parser.config[HEADER_IDENT]
    assert isinstance(header, list)
    assert len(header) > 0


def test_collector_parsing(parser):
    section = "section_2"
    section_content = list(parser.config[section].keys())
    coll_name = [name for name in section_content if name.startswith("#_")][0]
    collector = parser.config[section][coll_name]
    assert collector is not None
    assert isinstance(collector, list)
    assert len(collector) > 0
    assert "; comment" in collector
