# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

from src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)

BASE_DIR = Path(__file__).parent.parent.joinpath("assets")
TEST_DATA_PATH = BASE_DIR.joinpath("test_config_1.cfg")


def test_write_file_exception():
    parser = SimpleConfigParser()
    with pytest.raises(ValueError):
        parser.write_file(None)  # noqa


def test_write_to_file(tmp_path):
    tmp_file = Path(tmp_path).joinpath("tmp_config.cfg")
    parser1 = SimpleConfigParser()
    parser1.read_file(TEST_DATA_PATH)
    parser1.write_file(tmp_file)

    parser2 = SimpleConfigParser()
    parser2.read_file(tmp_file)

    assert tmp_file.exists()
    assert parser2.config is not None
    assert parser1.config == parser2.config

    with open(TEST_DATA_PATH, "r") as original, open(tmp_file, "r") as written:
        assert original.read() == written.read()
