# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.constants import SYSTEMD
from core.install_paths import install_root_join

# repo
MOBILERAKER_REPO = "https://github.com/Clon1998/mobileraker_companion.git"

# names
MOBILERAKER_SERVICE_NAME = "mobileraker.service"
MOBILERAKER_UPDATER_SECTION_NAME = "update_manager mobileraker"
MOBILERAKER_LOG_NAME = "mobileraker.log"

# directories
MOBILERAKER_DIR = install_root_join("mobileraker_companion")
MOBILERAKER_ENV_DIR = install_root_join("mobileraker-env")

# files
MOBILERAKER_INSTALL_SCRIPT = MOBILERAKER_DIR.joinpath("scripts/install.sh")
MOBILERAKER_REQ_FILE = MOBILERAKER_DIR.joinpath("scripts/mobileraker-requirements.txt")
MOBILERAKER_SERVICE_FILE = SYSTEMD.joinpath(MOBILERAKER_SERVICE_NAME)
