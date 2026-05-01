# ======================================================================= #
#  Copyright (C) 2023 - 2026 Staubgeborener and Tylerjet                  #
#  https://github.com/Staubgeborener/klipper-backup                       #
#  https://klipperbackup.xyz                                              #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.constants import BASE_DIR

EXT_MODULE_NAME = "klipper_backup_extension.py"
MODULE_PATH = Path(__file__).resolve().parent
MOONRAKER_CONF = BASE_DIR.joinpath("printer_data", "config", "moonraker.conf")
KLIPPERBACKUP_DIR = BASE_DIR.joinpath("klipper-backup")
KLIPPERBACKUP_CONFIG_DIR = BASE_DIR.joinpath("config_backup")
KLIPPERBACKUP_REPO_URL = "https://github.com/staubgeborener/klipper-backup"
