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
CROWSNEST_REPO = "https://github.com/mainsail-crew/crowsnest.git"

# names
CROWSNEST_SERVICE_NAME = "crowsnest.service"

# directories
CROWSNEST_DIR = Path.home().joinpath("crowsnest")
CROWSNEST_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("crowsnest-backups")

# files
CROWSNEST_MULTI_CONFIG = CROWSNEST_DIR.joinpath("tools/.config")
CROWSNEST_INSTALL_SCRIPT = CROWSNEST_DIR.joinpath("tools/install.sh")
CROWSNEST_BIN_FILE = Path("/usr/local/bin/crowsnest")
CROWSNEST_LOGROTATE_FILE = Path("/etc/logrotate.d/crowsnest")
CROWSNEST_SERVICE_FILE = SYSTEMD.joinpath(CROWSNEST_SERVICE_NAME)
