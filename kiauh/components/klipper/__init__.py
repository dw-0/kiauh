# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.backup_manager import BACKUP_ROOT_DIR

MODULE_PATH = Path(__file__).resolve().parent

KLIPPER_DIR = Path.home().joinpath("klipper")
KLIPPER_ENV_DIR = Path.home().joinpath("klippy-env")
KLIPPER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("klipper-backups")
KLIPPER_REQUIREMENTS_TXT = KLIPPER_DIR.joinpath("scripts/klippy-requirements.txt")
DEFAULT_KLIPPER_REPO_URL = "https://github.com/Klipper3D/klipper"

EXIT_KLIPPER_SETUP = "Exiting Klipper setup ..."
