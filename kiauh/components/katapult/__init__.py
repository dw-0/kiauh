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

# directories
KATAPULT_DIR = Path.home().joinpath("katapult")
KATAPULT_KCONFIGS_DIR = Path.home().joinpath("katapult-kconfigs")
KATAPULT_OUT_DIR = KATAPULT_DIR.joinpath("out")

# build outputs
KATAPULT_BIN = KATAPULT_OUT_DIR.joinpath("katapult.bin")
KATAPULT_UF2 = KATAPULT_OUT_DIR.joinpath("katapult.uf2")
KATAPULT_DEPLOYER_BIN = KATAPULT_OUT_DIR.joinpath("deployer.bin")

# scripts
KATAPULT_FLASHTOOL_PATH = KATAPULT_DIR.joinpath("scripts/flashtool.py")
