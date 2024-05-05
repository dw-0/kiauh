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

CROWSNEST_DIR = Path.home().joinpath("crowsnest")
CROWSNEST_REPO = "https://github.com/mainsail-crew/crowsnest.git"
CROWSNEST_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("crowsnest-backups")
