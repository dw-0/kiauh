# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import TypeVar

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from extensions.obico.moonraker_obico import MoonrakerObico
from extensions.octoeverywhere.octoeverywhere import Octoeverywhere
from extensions.octoapp.octoapp import Octoapp
from extensions.telegram_bot.moonraker_telegram_bot import MoonrakerTelegramBot

InstanceType = TypeVar(
    "InstanceType",
    Klipper,
    Moonraker,
    MoonrakerTelegramBot,
    MoonrakerObico,
    Octoeverywhere,
    Octoapp,
)
