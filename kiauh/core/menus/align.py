# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""Helpers for building box-drawn menus with correct terminal cell widths.

CJK characters occupy 2 terminal cells while Python's ``len()`` counts 1.
Any menu whose status rows contain CJK translations *cannot* rely on plain
`{:<N}` formatting, since the displayed line will be N chars short and the
right-side border will drift left.  The helpers here account for both
East-Asian wide chars (via ``unicodedata.east_asian_width``) and ANSI escape
sequences (stripped before measuring).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict

# Empirically correct geometry — MainMenu / InstallMenu / UpdateMenu /
# RemoveMenu / BackupMenu / AdvancedMenu / Settings / Language / LogUpload —
# all land at 67 display cells outer = 64 dashes between ╟ and ╢:
#   ╟ ───────────── (×64) ───────────────╢  = 67 chars wide
#   ║ <content-61-wide>                  ║   = 67 chars wide (2+61+4? No 2+61+2=65, use 63 inner  =  63+2+2 = 67.))
# Yes: 63 inner = outer-4  (remove "║ " 2 + " ║" 2)
BOX_OUTER_WIDTH: int = 67
BOX_INNER_CONTENT_WIDTH: int = 63

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def display_width(s: str) -> int:
    """Return the number of terminal columns that *s* will occupy."""
    raw = _ANSI_RE.sub("", s)
    w = 0
    for ch in raw:
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ("W", "F"):
            w += 2
        elif unicodedata.category(ch) == "Cf":
            continue
        else:
            w += 1
    return w


def pad_to(s: str, width: int) -> str:
    """Right-pad *s* with spaces so its total displayed width is *width*."""
    pad = width - display_width(s)
    if pad <= 0:
        return s
    return f"{s}{' ' * pad}"


def box_line(content: str, inner_width: int = BOX_INNER_CONTENT_WIDTH) -> str:
    return f"║ {pad_to(content, inner_width)} ║"


def hrule(inner_width: int = BOX_INNER_CONTENT_WIDTH) -> str:
    return f"╟{'─' * (inner_width + 2)}╢"

