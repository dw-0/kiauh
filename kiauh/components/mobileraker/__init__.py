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

MOBILERAKER_REPO = "https://github.com/Clon1998/mobileraker_companion.git"
MOBILERAKER_DIR = Path.home().joinpath("mobileraker_companion")
MOBILERAKER_ENV = Path.home().joinpath("mobileraker-env")
MOBILERAKER_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("mobileraker-backups")
