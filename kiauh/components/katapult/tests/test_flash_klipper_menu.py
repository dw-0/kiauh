# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import re
from typing import List

import pytest
from components.katapult.menus import katapult_flash_klipper_menu
from components.katapult.menus.katapult_flash_klipper_menu import (
    KatapultFlashKlipperMenu,
)

# KIAUH's menus are 57 characters wide
MENU_WIDTH = 57


class TestKatapultFlashKlipperMenu:
    @pytest.mark.parametrize("count", [0, 12])
    def test_menu_is_aligned(self, count: int, capsys, monkeypatch) -> None:
        monkeypatch.setattr(
            katapult_flash_klipper_menu,
            "load_remembered_mcus",
            lambda: [object()] * count,
        )

        KatapultFlashKlipperMenu().print_menu()

        output = re.sub(r"\x1b\[[0-9;]*m", "", capsys.readouterr().out)
        assert f"Remembered MCUs: {count}" in output
        assert {len(line) for line in output.splitlines()} == {MENU_WIDTH}

    def test_options_call_the_actions(self, monkeypatch) -> None:
        called: List[str] = []
        for name in ("flash_klipper_via_katapult", "update_all_mcus", "forget_mcu"):
            monkeypatch.setattr(
                katapult_flash_klipper_menu,
                name,
                lambda name=name: called.append(name),
            )
        menu = KatapultFlashKlipperMenu()
        menu.set_options()

        assert list(menu.options) == ["1", "2", "3"]
        menu.flash_mcu()
        menu.update_all_mcus()
        menu.forget_mcu()

        assert called == ["flash_klipper_via_katapult", "update_all_mcus", "forget_mcu"]
