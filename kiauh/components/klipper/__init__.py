# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.backup_manager import BACKUP_ROOT_DIR

MODULE_PATH = Path(__file__).resolve().parent

KLIPPER_REPO_URL = "https://github.com/Klipper3d/klipper.git"

# names
KLIPPER_LOG_NAME = "klippy.log"
KLIPPER_CFG_NAME = "printer.cfg"
KLIPPER_SERIAL_NAME = "klippy.serial"
KLIPPER_UDS_NAME = "klippy.sock"
KLIPPER_ENV_FILE_NAME = "klipper.env"
KLIPPER_SERVICE_NAME = "klipper.service"

# directories
KLIPPER_DIR = Path.home().joinpath("klipper")
KLIPPER_KCONFIGS_DIR = Path.home().joinpath("klipper-kconfigs")
KLIPPER_ENV_DIR = Path.home().joinpath("klippy-env")
KLIPPER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("klipper-backups")

# files
KLIPPER_REQ_FILE = KLIPPER_DIR.joinpath("scripts/klippy-requirements.txt")
KLIPPER_INSTALL_SCRIPT = KLIPPER_DIR.joinpath("scripts/install-ubuntu-22.04.sh")
KLIPPER_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{KLIPPER_SERVICE_NAME}")
KLIPPER_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{KLIPPER_ENV_FILE_NAME}")


EXIT_KLIPPER_SETUP = "Exiting Klipper setup ..."
