# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

EXT_MODULE_NAME = "gcode_shell_command.py"
MODULE_PATH = Path(__file__).resolve().parent
MODULE_ASSETS = MODULE_PATH.joinpath("assets")
KLIPPER_DIR = Path.home().joinpath("klipper")
KLIPPER_EXTRAS = KLIPPER_DIR.joinpath("klippy/extras")
EXTENSION_SRC = MODULE_ASSETS.joinpath(EXT_MODULE_NAME)
EXTENSION_TARGET_PATH = KLIPPER_EXTRAS.joinpath(EXT_MODULE_NAME)
EXAMPLE_CFG_SRC = MODULE_ASSETS.joinpath("shell_command.cfg")
