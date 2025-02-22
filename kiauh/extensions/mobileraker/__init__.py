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
from core.constants import SYSTEMD

# repo
MOBILERAKER_REPO = "https://github.com/Clon1998/mobileraker_companion.git"

# names
MOBILERAKER_SERVICE_NAME = "mobileraker.service"
MOBILERAKER_UPDATER_SECTION_NAME = "update_manager mobileraker"
MOBILERAKER_LOG_NAME = "mobileraker.log"

# directories
MOBILERAKER_DIR = Path.home().joinpath("mobileraker_companion")
MOBILERAKER_ENV_DIR = Path.home().joinpath("mobileraker-env")
MOBILERAKER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("mobileraker-backups")

# files
MOBILERAKER_INSTALL_SCRIPT = MOBILERAKER_DIR.joinpath("scripts/install.sh")
MOBILERAKER_REQ_FILE = MOBILERAKER_DIR.joinpath("scripts/mobileraker-requirements.txt")
MOBILERAKER_SERVICE_FILE = SYSTEMD.joinpath(MOBILERAKER_SERVICE_NAME)
