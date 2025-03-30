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
SPOOLMAN_DOCKER_IMAGE = "ghcr.io/donkie/spoolman:latest"
SPOOLMAN_DIR = Path.home().joinpath("spoolman")
SPOOLMAN_DATA_DIR = SPOOLMAN_DIR.joinpath("data")
SPOOLMAN_COMPOSE_FILE = SPOOLMAN_DIR.joinpath("docker-compose.yml")
SPOOLMAN_DEFAULT_PORT = 7912
