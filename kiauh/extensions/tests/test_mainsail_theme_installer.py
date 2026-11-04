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
from extensions.mainsail_theme_installer.mainsail_theme_installer_extension import (
    MainsailThemeInstallMenu,
    ThemeData,
)

MODULE = "extensions.mainsail_theme_installer.mainsail_theme_installer_extension"

# current format of the list in mainsail-crew/docs
DOCS_CSV = (
    "name,short_note,author,repo,branch,preview\n"
    "Dracula,,steadyjaw,dracula-mainsail-theme,master,screenshot.jpg\n"
    "Printables,(unofficial),8bitmcu,mainsail-printables,main,screenshot.jpg\n"
)

# legacy format of the list in mainsail-crew/gb-docs
LEGACY_CSV = (
    "name,short_note,author,repo\n"
    "Dracula,,steadyjaw,dracula-mainsail-theme\n"
    "Printables,(unofficial),8bitmcu,mainsail-printables\n"
)

EXPECTED_THEMES = [
    ThemeData("Dracula", "", "steadyjaw", "dracula-mainsail-theme"),
    ThemeData("Printables", "(unofficial)", "8bitmcu", "mainsail-printables"),
]


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self._body


def _patch_themes_csv(monkeypatch: pytest.MonkeyPatch, body: str) -> None:
    class FakeUrlLib:
        @staticmethod
        def urlopen(url: str):
            return _FakeResponse(body)

    monkeypatch.setattr(f"{MODULE}.urllib.request", FakeUrlLib())


@pytest.fixture
def menu(monkeypatch: pytest.MonkeyPatch) -> MainsailThemeInstallMenu:
    _patch_themes_csv(monkeypatch, DOCS_CSV)
    return MainsailThemeInstallMenu([])


class TestLoadThemes:
    def test_parses_docs_format_and_ignores_extra_columns(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_themes_csv(monkeypatch, DOCS_CSV)
        assert MainsailThemeInstallMenu([]).themes == EXPECTED_THEMES

    def test_parses_legacy_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _patch_themes_csv(monkeypatch, LEGACY_CSV)
        assert MainsailThemeInstallMenu([]).themes == EXPECTED_THEMES

    def test_skips_blank_and_incomplete_rows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_themes_csv(monkeypatch, DOCS_CSV + "\n" + "Broken,,,,,\n")
        assert MainsailThemeInstallMenu([]).themes == EXPECTED_THEMES


class TestThemeMenuNumbering:
    def test_options_start_at_one_to_match_docs_ids(
        self, menu: MainsailThemeInstallMenu
    ) -> None:
        menu.set_options()
        assert list(menu.options) == ["1", "2"]
        assert menu.options["1"].opt_index == "0"
        assert menu.options["2"].opt_index == "1"

    def test_menu_lists_themes_from_one(
        self, menu: MainsailThemeInstallMenu, capsys
    ) -> None:
        menu.print_menu()
        out = capsys.readouterr().out
        assert " 1) [Dracula]" in out
        assert " 2) [Printables]" in out
        assert " 0) [" not in out

    def test_menu_links_to_current_docs(
        self, menu: MainsailThemeInstallMenu, capsys
    ) -> None:
        menu.print_menu()
        out = capsys.readouterr().out
        # the url is too long for the menu box, so it is wrapped over two lines
        assert "║ https://docs.mainsail.xyz/features/custom-            ║" in out
        assert "║ themes/community-themes/                              ║" in out
        assert "theming/themes" not in out
