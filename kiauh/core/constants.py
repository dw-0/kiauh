# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import pwd
from pathlib import Path

from core.backup_manager import BACKUP_ROOT_DIR

# global dependencies
GLOBAL_DEPS = ["git", "wget", "curl", "unzip", "dfu-util", "python3-virtualenv"]

# strings
INVALID_CHOICE = "Invalid choice. Please select a valid value."

# current user
CURRENT_USER = pwd.getpwuid(os.getuid())[0]

# dirs
SYSTEMD = Path("/etc/systemd/system")
PRINTER_DATA_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("printer-data-backups")
NGINX_SITES_AVAILABLE = Path("/etc/nginx/sites-available")
NGINX_SITES_ENABLED = Path("/etc/nginx/sites-enabled")
NGINX_CONFD = Path("/etc/nginx/conf.d")
