# ======================================================================= #
#  Copyright (C) 2023 - 2024 Staubgeborener                               #
#  https://github.com/Staubgeborener/klipper-backup                       #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

EXT_MODULE_NAME = "klipper_backup_extension.py"
MODULE_PATH = Path(__file__).resolve().parent
MODULE_ASSETS = MODULE_PATH.joinpath("assets")
KLIPPER_DIR = Path.home().joinpath("klipper-backup")
KLIPPERBACKUP_DIR = Path.home().joinpath("klipper-backup")
KLIPPERBACKUP_CONFIG_DIR = Path.home().joinpath("config_backup")
DEFAULT_KLIPPERBACKUP_REPO_URL = "https://github.com/staubgeborener/klipper-backup"
KLIPPER_EXTRAS = KLIPPER_DIR.joinpath("klippy/extras")
EXTENSION_SRC = MODULE_ASSETS.joinpath(EXT_MODULE_NAME)
EXTENSION_TARGET_PATH = KLIPPERBACKUP_DIR
EXAMPLE_CFG_SRC = MODULE_ASSETS.joinpath("shell_command.cfg")
