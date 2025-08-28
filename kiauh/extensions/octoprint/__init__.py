# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

# Constants
OP_DEFAULT_PORT = 5000

# OctoPrint instance naming/prefixes
OP_ENV_PREFIX = "OctoPrint"
OP_BASEDIR_PREFIX = ".octoprint"

# Service/log filenames
OP_LOG_NAME = "octoprint.log"

# Files/paths (computed per-instance where applicable)
OP_SUDOERS_FILE = Path("/etc/sudoers.d/octoprint-shutdown")
