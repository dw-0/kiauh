# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import warnings
from typing import Callable


def deprecated(info: str = "", replaced_by: Callable = None) -> Callable:
    def decorator(func):
        def wrapper(*args, **kwargs):
            msg = f"{info}{replaced_by.__name__ if replaced_by else ''}"
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
