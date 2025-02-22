# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import warnings
from typing import Callable


def deprecated(info: str = "", replaced_by: Callable | None = None) -> Callable:
    def decorator(func) -> Callable:
        def wrapper(*args, **kwargs):
            msg = f"{info}{replaced_by.__name__ if replaced_by else ''}"
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
