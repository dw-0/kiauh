#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from utils.constants import (
    COLOR_WHITE,
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_MAGENTA,
    RESET_FORMAT,
)


class Logger:
    @staticmethod
    def info(msg):
        # log to kiauh.log
        pass

    @staticmethod
    def warn(msg):
        # log to kiauh.log
        pass

    @staticmethod
    def error(msg):
        # log to kiauh.log
        pass

    @staticmethod
    def print_info(msg, prefix=True, start="", end="\n") -> None:
        message = f"[INFO] {msg}" if prefix else msg
        print(f"{COLOR_WHITE}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_ok(msg, prefix=True, start="", end="\n") -> None:
        message = f"[OK] {msg}" if prefix else msg
        print(f"{COLOR_GREEN}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_warn(msg, prefix=True, start="", end="\n") -> None:
        message = f"[WARN] {msg}" if prefix else msg
        print(f"{COLOR_YELLOW}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_error(msg, prefix=True, start="", end="\n") -> None:
        message = f"[ERROR] {msg}" if prefix else msg
        print(f"{COLOR_RED}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_status(msg, prefix=True, start="", end="\n") -> None:
        message = f"\n###### {msg}" if prefix else msg
        print(f"{COLOR_MAGENTA}{start}{message}{RESET_FORMAT}", end=end)
