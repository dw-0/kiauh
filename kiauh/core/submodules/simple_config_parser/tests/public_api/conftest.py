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
CONFIG_FILES = ["test_config_1.cfg", "test_config_2.cfg", "test_config_3.cfg"]


@pytest.fixture(params=CONFIG_FILES)
def parser(request):
    parser = SimpleConfigParser()
    file_path = BASE_DIR.joinpath(request.param)
    for line in load_testdata_from_file(file_path):
        parser._parse_line(line)  # noqa

    return parser
