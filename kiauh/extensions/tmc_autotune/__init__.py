# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

# repo
TMCA_REPO = "https://github.com/andrewmcgr/klipper_tmc_autotune"

# directories
TMCA_DIR = Path.home().joinpath("klipper_tmc_autotune")
MODULE_PATH = Path(__file__).resolve().parent
KLIPPER_DIR = Path.home().joinpath("klipper")
KLIPPER_EXTRAS = KLIPPER_DIR.joinpath("klippy/extras")
KLIPPER_PLUGINS = KLIPPER_DIR.joinpath("klippy/plugins")

# files
TMCA_EXAMPLE_CONFIG = TMCA_DIR.joinpath("docs/example.cfg")

# names
TMCA_MOONRAKER_UPDATER_NAME = "update_manager klipper_tmc_autotune"


def get_klipper_extensions_path() -> Path:
    # checked on each use, Klipper may have been swapped for Kalico in the meantime
    return KLIPPER_PLUGINS if KLIPPER_PLUGINS.is_dir() else KLIPPER_EXTRAS
