#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from datetime import datetime
from typing import Dict, Literal, List

from kiauh.utils.constants import COLOR_CYAN, RESET_FORMAT
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import check_package_install, install_system_packages


def get_current_date() -> Dict[Literal["date", "time"], str]:
    """
    Get the current date |
    :return: Dict holding a date and time key:value pair
    """
    now: datetime = datetime.today()
    date: str = now.strftime("%Y-%m-%d")
    time: str = now.strftime("%H-%M-%S")

    return {"date": date, "time": time}


def check_install_dependencies(deps: List[str]) -> None:
    """
    Common helper method to check if dependencies are installed
    and if not, install them automatically |
    :param deps: List of strings of package names to check if installed
    :return: None
    """
    requirements = check_package_install(deps)
    if requirements:
        Logger.print_status("Installing dependencies ...")
        Logger.print_info("The following packages need installation:")
        for _ in requirements:
            print(f"{COLOR_CYAN}● {_}{RESET_FORMAT}")
        install_system_packages(requirements)
