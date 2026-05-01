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
OA_REPO = "https://github.com/crysxd/OctoApp-Plugin.git"

# directories
OA_DIR = BASE_DIR.joinpath("octoapp")
OA_ENV_DIR = BASE_DIR.joinpath("octoapp-env")

# files
OA_REQ_FILE = OA_DIR.joinpath("requirements.txt")
OA_DEPS_JSON_FILE = OA_DIR.joinpath("moonraker-system-dependencies.json")
OA_INSTALL_SCRIPT = OA_DIR.joinpath("install.sh")
OA_UPDATE_SCRIPT = OA_DIR.joinpath("update.sh")
OA_INSTALLER_LOG_FILE = BASE_DIR.joinpath("octoapp-installer.log")

# filenames
OA_CFG_NAME = "octoapp.conf"
OA_LOG_NAME = "octoapp.log"
OA_SYS_CFG_NAME = "octoapp-system.cfg"
