# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from enum import Enum
from typing import Optional, TypedDict


class StatusInfo:
    def __init__(self, txt: str, code: int):
        self.txt: str = txt
        self.code: int = code


class InstallStatus(Enum):
    INSTALLED = StatusInfo("Installed", 1)
    NOT_INSTALLED = StatusInfo("Not installed", 2)
    INCOMPLETE = StatusInfo("Incomplete", 3)


class ComponentStatus(TypedDict):
    status: InstallStatus
    repo: Optional[str]
    local: Optional[str]
    remote: Optional[str]
    instances: Optional[int]
