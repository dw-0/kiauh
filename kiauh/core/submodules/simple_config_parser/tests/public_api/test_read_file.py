# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

from src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)

BASE_DIR = Path(__file__).parent.parent.joinpath("assets")
TEST_DATA_PATH = BASE_DIR.joinpath("test_config_1.cfg")


def test_read_file():
    parser = SimpleConfigParser()
    parser.read_file(TEST_DATA_PATH)
    assert parser.config is not None
    assert parser.config.keys() is not None
