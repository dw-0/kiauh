#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from kiauh.utils.constants import COLOR_GREEN, COLOR_YELLOW, COLOR_RED, \
    COLOR_MAGENTA, RESET_FORMAT


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
    def print_ok(msg, prefix=True, end="\n") -> None:
        message = f"[OK] {msg}" if prefix else msg
        print(f"{COLOR_GREEN}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_warn(msg, prefix=True, end="\n") -> None:
        message = f"[WARN] {msg}" if prefix else msg
        print(f"{COLOR_YELLOW}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_error(msg, prefix=True, end="\n") -> None:
        message = f"[ERROR] {msg}" if prefix else msg
        print(f"{COLOR_RED}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_info(msg, prefix=True, end="\n") -> None:
        message = f"###### {msg}" if prefix else msg
        print(f"{COLOR_MAGENTA}{message}{RESET_FORMAT}", end=end)
