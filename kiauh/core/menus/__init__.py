# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from enum import Enum


class FooterType(Enum):
    QUIT = "QUIT"
    BACK = "BACK"
    BACK_HELP = "BACK_HELP"
    BLANK = "BLANK"


class ExitAppException(Exception):
    pass


class GoBackException(Exception):
    pass
