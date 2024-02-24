#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.backup_manager import BACKUP_ROOT_DIR

MODULE_PATH = Path(__file__).resolve().parent
FLUIDD_DIR = Path.home().joinpath("fluidd")
FLUIDD_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("fluidd-backups")
FLUIDD_CONFIG_DIR = Path.home().joinpath("fluidd-config")
FLUIDD_NGINX_CFG = Path("/etc/nginx/sites-enabled/fluidd")
FLUIDD_URL = "https://github.com/fluidd-core/fluidd/releases/latest/download/fluidd.zip"
FLUIDD_UNSTABLE_URL = (
    "https://github.com/fluidd-core/fluidd/releases/download/%TAG%/fluidd.zip"
)
FLUIDD_CONFIG_REPO_URL = "https://github.com/fluidd-core/fluidd-config.git"

