#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from kiauh.core.backup_manager import BACKUP_ROOT_DIR

MODULE_PATH = Path(__file__).resolve().parent

MOONRAKER_DIR = Path.home().joinpath("moonraker")
MOONRAKER_ENV_DIR = Path.home().joinpath("moonraker-env")
MOONRAKER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("moonraker-backups")
MOONRAKER_DB_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("moonraker-db-backups")
MOONRAKER_REQUIREMENTS_TXT = MOONRAKER_DIR.joinpath(
    "scripts/moonraker-requirements.txt"
)
DEFAULT_MOONRAKER_REPO_URL = "https://github.com/Arksine/moonraker"
DEFAULT_MOONRAKER_PORT = 7125

# introduced due to
# https://github.com/Arksine/moonraker/issues/349
# https://github.com/Arksine/moonraker/pull/346
POLKIT_LEGACY_FILE = Path("/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla")
POLKIT_FILE = Path("/etc/polkit-1/rules.d/moonraker.rules")
POLKIT_USR_FILE = Path("/usr/share/polkit-1/rules.d/moonraker.rules")
POLKIT_SCRIPT = Path.home().joinpath("moonraker/scripts/set-policykit-rules.sh")

EXIT_MOONRAKER_SETUP = "Exiting Moonraker setup ..."
