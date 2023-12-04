#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from os.path import join, dirname, abspath
from pathlib import Path

APPLICATION_ROOT = dirname(dirname(abspath(__file__)))
KIAUH_CFG = join(APPLICATION_ROOT, "kiauh.cfg")
KIAUH_BACKUP_DIR = f"{Path.home()}/kiauh-backups"
