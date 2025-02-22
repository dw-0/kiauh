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

MOONRAKER_REPO_URL = "https://github.com/Arksine/moonraker.git"

# names
MOONRAKER_CFG_NAME = "moonraker.conf"
MOONRAKER_LOG_NAME = "moonraker.log"
MOONRAKER_SERVICE_NAME = "moonraker.service"
MOONRAKER_DEFAULT_PORT = 7125
MOONRAKER_ENV_FILE_NAME = "moonraker.env"

# directories
MOONRAKER_DIR = Path.home().joinpath("moonraker")
MOONRAKER_ENV_DIR = Path.home().joinpath("moonraker-env")
MOONRAKER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("moonraker-backups")
MOONRAKER_DB_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("moonraker-db-backups")

# files
MOONRAKER_INSTALL_SCRIPT = MOONRAKER_DIR.joinpath("scripts/install-moonraker.sh")
MOONRAKER_REQ_FILE = MOONRAKER_DIR.joinpath("scripts/moonraker-requirements.txt")
MOONRAKER_SPEEDUPS_REQ_FILE = MOONRAKER_DIR.joinpath("scripts/moonraker-speedups.txt")
MOONRAKER_DEPS_JSON_FILE = MOONRAKER_DIR.joinpath("scripts/system-dependencies.json")
# introduced due to
# https://github.com/Arksine/moonraker/issues/349
# https://github.com/Arksine/moonraker/pull/346
POLKIT_LEGACY_FILE = Path("/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla")
POLKIT_FILE = Path("/etc/polkit-1/rules.d/moonraker.rules")
POLKIT_USR_FILE = Path("/usr/share/polkit-1/rules.d/moonraker.rules")
POLKIT_SCRIPT = MOONRAKER_DIR.joinpath("scripts/set-policykit-rules.sh")
MOONRAKER_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_SERVICE_NAME}")
MOONRAKER_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{MOONRAKER_ENV_FILE_NAME}")


EXIT_MOONRAKER_SETUP = "Exiting Moonraker setup ..."
