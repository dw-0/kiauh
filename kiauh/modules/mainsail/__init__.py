#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

import os

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
MAINSAIL_DIR = os.path.join(Path.home(), "mainsail")
MAINSAIL_CONFIG_DIR = os.path.join(Path.home(), "mainsail-config")
MAINSAIL_CONFIG_JSON = os.path.join(MAINSAIL_DIR, "config.json")
MAINSAIL_URL = (
    "https://github.com/mainsail-crew/mainsail/releases/latest/download/mainsail.zip"
)
MAINSAIL_UNSTABLE_URL = (
    "https://github.com/mainsail-crew/mainsail/releases/download/%TAG%/mainsail.zip"
)
MAINSAIL_CONFIG_REPO_URL = "https://github.com/mainsail-crew/mainsail-config.git"
