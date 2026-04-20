# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

# repo
KAMP_REPO = "https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging"

# directories
MODULE_PATH = Path(__file__).resolve().parent
KAMP_DIR = Path.home().joinpath("Klipper-Adaptive-Meshing-Purging")
KLIPPER_DIR = Path.home().joinpath("klipper")

# names
KAMP_MOONRAKER_UPDATER_NAME = "update_manager Klipper-Adaptive-Meshing-Purging"
