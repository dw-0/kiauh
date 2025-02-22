# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from enum import Enum


class Color(Enum):
    WHITE = "\033[37m"  # white
    MAGENTA = "\033[35m"  # magenta
    GREEN = "\033[92m"  # bright green
    YELLOW = "\033[93m"  # bright yellow
    RED = "\033[91m"  # bright red
    CYAN = "\033[96m"  # bright cyan
    RST = "\033[0m"  # reset format

    def __str__(self):
        return self.value

    @staticmethod
    def apply(text: str | int, color: "Color") -> str:
        """Apply a given color to a given text string."""
        return f"{color}{text}{Color.RST}"
