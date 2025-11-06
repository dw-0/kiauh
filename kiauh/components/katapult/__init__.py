# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

# repo
KATAPULT_REPO = "https://github.com/Arksine/katapult"

# names
KATAPULT_LOG_NAME = "katapult.log"

# directories
KATAPULT_DIR = Path.home().joinpath("katapult")
KATAPULT_KCONFIGS_DIR = Path.home().joinpath("katapult-kconfigs")

# scripts
KATAPULT_FLASHTOOL_PATH = KATAPULT_DIR.joinpath("scripts/flashtool.py")

# messages
# EXIT_KATAPULT_SETUP = "Exiting katapult setup ..."
