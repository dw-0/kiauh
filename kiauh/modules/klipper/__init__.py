#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

KLIPPER_DIR = f"{Path.home()}/klipper"
KLIPPER_ENV_DIR = f"{Path.home()}/klippy-env"
KLIPPER_REQUIREMENTS_TXT = f"{KLIPPER_DIR}/scripts/klippy-requirements.txt"
DEFAULT_KLIPPER_REPO_URL = "https://github.com/Klipper3D/klipper"

EXIT_KLIPPER_SETUP = "Exiting Klipper setup ..."
