# ======================================================================= #
#  Copyright (C) 2023 - 2024 Staubgeborener and Tylerjet                  #
#  https://github.com/Staubgeborener/klipper-backup                       #
#  https://klipperbackup.xyz                                              #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.install_paths import get_install_root

EXT_MODULE_NAME = "klipper_backup_extension.py"
MODULE_PATH = Path(__file__).resolve().parent
INSTALL_ROOT = get_install_root()
MOONRAKER_CONF = INSTALL_ROOT.joinpath("printer_data", "config", "moonraker.conf")
KLIPPERBACKUP_DIR = INSTALL_ROOT.joinpath("klipper-backup")
KLIPPERBACKUP_CONFIG_DIR = INSTALL_ROOT.joinpath("config_backup")
KLIPPERBACKUP_REPO_URL = "https://github.com/staubgeborener/klipper-backup"
