# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import pytest
from core.menus.settings_menu import SettingsMenu


@pytest.fixture
def patched_settings_menu(monkeypatch: pytest.MonkeyPatch) -> SettingsMenu:
    class FakeRepo:
        def __init__(self):
            self.repositories = []

    class FakeKiauh:
        backup_before_update = True
        language = None

    class FakeSettings:
        kiauh = FakeKiauh()
        mainsail = type("M", (), {"unstable_releases": False})()
        fluidd = type("F", (), {"unstable_releases": False})()
        klipper = FakeRepo()
        moonraker = FakeRepo()

        def save(self) -> None:
            pass

    monkeypatch.setattr(
        "core.menus.settings_menu.KiauhSettings", lambda: FakeSettings()
    )
    monkeypatch.setattr(
        "core.menus.settings_menu.get_klipper_status",
        lambda: type("S", (), {"repo": None, "repo_url": "", "branch": ""})(),
    )
    monkeypatch.setattr(
        "core.menus.settings_menu.get_moonraker_status",
        lambda: type("S", (), {"repo": None, "repo_url": "", "branch": ""})(),
    )

    return SettingsMenu()


class TestSettingsMenuConstruction:
    def test_options_cover_settings(self, patched_settings_menu: SettingsMenu) -> None:
        assert {"1", "2", "3", "4", "5"}.issubset(patched_settings_menu.options)

    def test_loads_backup_setting(self, patched_settings_menu: SettingsMenu) -> None:
        assert patched_settings_menu.auto_backups_enabled is True


class TestToggleMethods:
    def test_toggle_mainsail_release(self, patched_settings_menu: SettingsMenu) -> None:
        patched_settings_menu.mainsail_unstable = False
        patched_settings_menu.toggle_mainsail_release()
        assert patched_settings_menu.mainsail_unstable is True

    def test_toggle_fluidd_release(self, patched_settings_menu: SettingsMenu) -> None:
        patched_settings_menu.fluidd_unstable = False
        patched_settings_menu.toggle_fluidd_release()
        assert patched_settings_menu.fluidd_unstable is True

    def test_toggle_backup_before_update(
        self, patched_settings_menu: SettingsMenu
    ) -> None:
        patched_settings_menu.auto_backups_enabled = True
        patched_settings_menu.toggle_backup_before_update()
        assert patched_settings_menu.auto_backups_enabled is False
