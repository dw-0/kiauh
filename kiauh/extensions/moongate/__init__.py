# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#  Copyright (C) 2026 Paul Sharman <github.com/PEEKYPAUL>                 #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  It integrates Moongate for Klipper:                                    #
#  https://github.com/PEEKYPAUL/Moongate                                  #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

# repository
MOONGATE_REPO = "https://github.com/PEEKYPAUL/moongate.git"
MOONGATE_REPO_URL = "https://github.com/PEEKYPAUL/Moongate"

# directories
MODULE_PATH = Path(__file__).resolve().parent
MOONGATE_DIR = Path.home().joinpath("moongate")
MOONGATE_PLUGIN_DIR = MOONGATE_DIR.joinpath("klipper-plugin")

# installer scripts shipped inside the cloned repo
MOONGATE_INSTALL_SCRIPT = MOONGATE_PLUGIN_DIR.joinpath("install.sh")
MOONGATE_UPDATE_SCRIPT = MOONGATE_PLUGIN_DIR.joinpath("update.sh")
MOONGATE_UNINSTALL_SCRIPT = MOONGATE_PLUGIN_DIR.joinpath("uninstall.sh")

# moonraker.conf sections the installer manages
MOONGATE_UPDATER_NAME = "update_manager moongate"
MOONGATE_CONFIG_SECTION = "moongate"

# default HTTP port the Mainsail/Fluidd UI is served on
MOONGATE_DEFAULT_PORT = 80
