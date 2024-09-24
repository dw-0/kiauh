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

BASE_DIR = Path(__file__).parent.joinpath("test_data")
MATCHING_TEST_DATA_PATH = BASE_DIR.joinpath("matching_data.txt")
NON_MATCHING_TEST_DATA_PATH = BASE_DIR.joinpath("non_matching_data.txt")


@pytest.fixture
def parser():
    return SimpleConfigParser()


@pytest.mark.parametrize("line", load_testdata_from_file(MATCHING_TEST_DATA_PATH))
def test_match_option(parser, line):
    """Test that a line matches the definition of an option"""
    assert (
        parser._match_option(line) is True
    ), f"Expected line '{line}' to match option definition!"


@pytest.mark.parametrize("line", load_testdata_from_file(NON_MATCHING_TEST_DATA_PATH))
def test_non_matching_option(parser, line):
    """Test that a line does not match the definition of an option"""
    assert (
        parser._match_option(line) is False
    ), f"Expected line '{line}' to not match option definition!"
