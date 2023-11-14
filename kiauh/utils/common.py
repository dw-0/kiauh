#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from datetime import datetime
from typing import Dict, Literal


def get_current_date() -> Dict[Literal["date", "time"], str]:
    """
    Get the current date |
    :return: a Dict holding a date and time key:value pair
    """
    now: datetime = datetime.today()
    date: str = now.strftime("%Y-%m-%d")
    time: str = now.strftime("%H-%M-%S")

    return {"date": date, "time": time}
