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
TG_BOT_REPO = "https://github.com/nlef/moonraker-telegram-bot.git"

# names
TG_BOT_CFG_NAME = "telegram.conf"
TG_BOT_LOG_NAME = "telegram.log"
TG_BOT_SERVICE_NAME = "moonraker-telegram-bot.service"
TG_BOT_ENV_FILE_NAME = "moonraker-telegram-bot.env"

# directories
TG_BOT_DIR = Path.home().joinpath("moonraker-telegram-bot")
TG_BOT_ENV = Path.home().joinpath("moonraker-telegram-bot-env")

# files
TG_BOT_SERVICE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{TG_BOT_SERVICE_NAME}")
TG_BOT_ENV_FILE_TEMPLATE = MODULE_PATH.joinpath(f"assets/{TG_BOT_ENV_FILE_NAME}")
TG_BOT_REQ_FILE = TG_BOT_DIR.joinpath("scripts/requirements.txt")
