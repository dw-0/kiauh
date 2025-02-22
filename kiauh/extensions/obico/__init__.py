# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent

# repo
OBICO_REPO = "https://github.com/TheSpaghettiDetective/moonraker-obico.git"

# names
OBICO_SERVICE_NAME = "moonraker-obico.service"
OBICO_ENV_FILE_NAME = "moonraker-obico.env"
OBICO_CFG_NAME = "moonraker-obico.cfg"
OBICO_CFG_SAMPLE_NAME = "moonraker-obico.cfg.sample"
OBICO_LOG_NAME = "moonraker-obico.log"
OBICO_UPDATE_CFG_NAME = "moonraker-obico-update.cfg"
OBICO_UPDATE_CFG_SAMPLE_NAME = "moonraker-obico-update.cfg.sample"
OBICO_MACROS_CFG_NAME = "moonraker_obico_macros.cfg"

# directories
OBICO_DIR = Path.home().joinpath("moonraker-obico")
OBICO_ENV_DIR = Path.home().joinpath("moonraker-obico-env")

# files
OBICO_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{OBICO_SERVICE_NAME}")
OBICO_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{OBICO_ENV_FILE_NAME}")
OBICO_LINK_SCRIPT = OBICO_DIR.joinpath("scripts/link.sh")
OBICO_REQ_FILE = OBICO_DIR.joinpath("requirements.txt")
