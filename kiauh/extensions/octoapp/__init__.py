# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

# repo
OA_REPO = "https://github.com/crysxd/OctoApp-Plugin.git"

# directories
OA_DIR = Path.home().joinpath("octoapp")
OA_ENV_DIR = Path.home().joinpath("octoapp-env")

# files
OA_REQ_FILE = OA_DIR.joinpath("requirements.txt")
OA_DEPS_JSON_FILE = OA_DIR.joinpath("moonraker-system-dependencies.json")
OA_INSTALL_SCRIPT = OA_DIR.joinpath("install.sh")
OA_UPDATE_SCRIPT = OA_DIR.joinpath("update.sh")
OA_INSTALLER_LOG_FILE = Path.home().joinpath("octoapp-installer.log")

# filenames
OA_CFG_NAME = "octoapp.conf"
OA_LOG_NAME = "octoapp.log"
OA_SYS_CFG_NAME = "octoapp-system.cfg"
