# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

StatusText = Literal["Installed", "Not installed", "Incomplete"]
StatusCode = Literal[0, 1, 2]
StatusMap: Dict[StatusCode, StatusText] = {
    0: "Not installed",
    1: "Incomplete",
    2: "Installed",
}


@dataclass
class ComponentStatus:
    status: StatusCode
    owner: str | None = None
    repo: str | None = None
    repo_url: str | None = None
    branch: str = ""
    local: str | None = None
    remote: str | None = None
    instances: int | None = None
