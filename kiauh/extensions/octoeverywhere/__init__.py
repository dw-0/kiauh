# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from core.constants import BASE_DIR

# repo
OE_REPO = "https://github.com/QuinnDamerell/OctoPrint-OctoEverywhere.git"

# directories
OE_DIR = BASE_DIR.joinpath("octoeverywhere")
OE_ENV_DIR = BASE_DIR.joinpath("octoeverywhere-env")
OE_STORE_DIR = OE_DIR.joinpath("octoeverywhere-store")

# files
OE_REQ_FILE = OE_DIR.joinpath("requirements.txt")
OE_DEPS_JSON_FILE = OE_DIR.joinpath("moonraker-system-dependencies.json")
OE_INSTALL_SCRIPT = OE_DIR.joinpath("install.sh")
OE_UPDATE_SCRIPT = OE_DIR.joinpath("update.sh")
OE_INSTALLER_LOG_FILE = BASE_DIR.joinpath("octoeverywhere-installer.log")

# filenames
OE_CFG_NAME = "octoeverywhere.conf"
OE_LOG_NAME = "octoeverywhere.log"
OE_SYS_CFG_NAME = "octoeverywhere-system.cfg"
