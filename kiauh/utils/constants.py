#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import pwd
from pathlib import Path

# text colors and formats
COLOR_MAGENTA = "\033[35m"  # magenta
COLOR_GREEN = "\033[92m"  # bright green
COLOR_YELLOW = "\033[93m"  # bright yellow
COLOR_RED = "\033[91m"  # bright red
COLOR_CYAN = "\033[96m"  # bright cyan
RESET_FORMAT = "\033[0m"  # reset format
# kiauh
KIAUH_BACKUP_DIR = f"{Path.home()}/kiauh-backups"
# current user
CURRENT_USER = pwd.getpwuid(os.getuid())[0]
SYSTEMD = "/etc/systemd/system"
