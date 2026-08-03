# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

from core.i18n import N_, _tr

StatusText = Literal["Installed", "Not installed", "Incomplete"]
StatusCode = Literal[0, 1, 2]
_STATUS_LABELS: Dict[StatusCode, str] = {
    0: N_("Not installed"),
    1: N_("Incomplete"),
    2: N_("Installed"),
}


def get_status_text(code: StatusCode) -> str:
    return _tr(_STATUS_LABELS[code])


@dataclass
class ComponentStatus:
    status: StatusCode
    owner: str | None = None
    repo: str | None = None
    repo_url: str | None = None
    branch: str | None = None
    local: str | None = None
    remote: str | None = None
    instances: int | None = None
