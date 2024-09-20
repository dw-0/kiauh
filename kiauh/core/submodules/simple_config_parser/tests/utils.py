# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path


def load_testdata_from_file(file_path: Path):
    """Helper function to load test data from a text file"""

    with open(file_path, "r") as f:
        return [line.replace("\n", "") for line in f]
