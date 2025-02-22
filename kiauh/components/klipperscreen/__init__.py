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
KLIPPERSCREEN_REPO = "https://github.com/KlipperScreen/KlipperScreen.git"

# names
KLIPPERSCREEN_SERVICE_NAME = "KlipperScreen.service"
KLIPPERSCREEN_UPDATER_SECTION_NAME = "update_manager KlipperScreen"
KLIPPERSCREEN_LOG_NAME = "KlipperScreen.log"

# directories
KLIPPERSCREEN_DIR = Path.home().joinpath("KlipperScreen")
KLIPPERSCREEN_ENV_DIR = Path.home().joinpath(".KlipperScreen-env")
KLIPPERSCREEN_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("klipperscreen-backups")

# files
KLIPPERSCREEN_REQ_FILE = KLIPPERSCREEN_DIR.joinpath(
    "scripts/KlipperScreen-requirements.txt"
)
KLIPPERSCREEN_INSTALL_SCRIPT = KLIPPERSCREEN_DIR.joinpath(
    "scripts/KlipperScreen-install.sh"
)
KLIPPERSCREEN_SERVICE_FILE = SYSTEMD.joinpath(KLIPPERSCREEN_SERVICE_NAME)
