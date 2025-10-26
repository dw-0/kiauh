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


def test_matching_lines(parser):
    """Alle Zeilen in matching_data.txt sollen als Save-Config-Content erkannt werden."""
    matching_lines = load_testdata_from_file(MATCHING_TEST_DATA_PATH)
    for line in matching_lines:
        assert parser._match_save_config_content(line) is True, f"Line should be a save config content: {line!r}"


def test_non_matching_lines(parser):
    """Alle Zeilen in non_matching_data.txt sollen NICHT als Save-Config-Content erkannt werden."""
    non_matching_lines = load_testdata_from_file(NON_MATCHING_TEST_DATA_PATH)
    for line in non_matching_lines:
        assert parser._match_save_config_content(line) is False, f"Line should not be a save config content: {line!r}"
