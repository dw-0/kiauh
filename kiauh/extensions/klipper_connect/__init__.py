# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Alejandro Mora <github.com/amd989>                  #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  It integrates klipper-connect (Prusa Connect bridge for Klipper):      #
#  https://github.com/amd989/klipper-connect                              #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent

# repo
KLIPPER_CONNECT_REPO = "https://github.com/amd989/klipper-connect.git"
KLIPPER_CONNECT_BRANCH = "main"

# names
KLIPPER_CONNECT_NAME = "klipper-connect"
KLIPPER_CONNECT_CFG_NAME = "klipper_connect.conf"
KLIPPER_CONNECT_STATE_DIR_NAME = "klipper_connect"

# directories
KLIPPER_CONNECT_DIR = Path.home().joinpath("klipper-connect")
KLIPPER_CONNECT_ENV_DIR = Path.home().joinpath("klipper-connect-env")

# files
KLIPPER_CONNECT_SERVICE_TEMPLATE = MODULE_PATH.joinpath(
    "assets/klipper-connect.service"
)
KLIPPER_CONNECT_CFG_SAMPLE = KLIPPER_CONNECT_DIR.joinpath(
    "klipper_connect.conf.example"
)
KLIPPER_CONNECT_MINI_CFG_SAMPLE = KLIPPER_CONNECT_DIR.joinpath(
    "examples/klipper_connect.mini.conf"
)
KLIPPER_CONNECT_REQ_FILE = KLIPPER_CONNECT_DIR.joinpath("requirements.txt")
KLIPPER_CONNECT_BIN = KLIPPER_CONNECT_ENV_DIR.joinpath("bin/klipper-connect")

# printer types the bridge supports (see klipper_connect/config.py)
KLIPPER_CONNECT_PRINTER_TYPES = ["MK3S", "MK3", "MK25S", "MK25", "MINI"]

# Prusa serial numbers look like CZPX1234X123XC12345
KLIPPER_CONNECT_SN_REGEX = r"^CZPX\d{4}X\d{3}X.\d{5}$"
