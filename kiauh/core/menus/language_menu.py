# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import textwrap
from typing import Type

from core.i18n import (
    LANGUAGE_DISPLAY_NAMES,
    SUPPORTED_LANGUAGES,
    _tr,
    current_language,
    setup_i18n,
)
from core.menus import Option
from core.menus.align import BOX_INNER_CONTENT_WIDTH, box_line, display_width, hrule, pad_to
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color

_INNER_CONTENT_WIDTH = BOX_INNER_CONTENT_WIDTH  # 58, matches original base_menu chrome


def _secondary_label(code: str) -> str:
    return {
        "en": _tr("English"),
        "zh_CN": _tr("Simplified Chinese"),
        "zh_TW": _tr("Traditional Chinese"),
    }[code]


class LanguageMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = _tr("Language")
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {}
        for i, code in enumerate(SUPPORTED_LANGUAGES, start=1):
            self.options[str(i)] = Option(
                method=self.select_language, opt_data=code
            )

    def _display_rows(self) -> list[str]:
        rows: list[str] = []
        active = current_language() or "en"
        for i, code in enumerate(SUPPORTED_LANGUAGES, start=1):
            native = LANGUAGE_DISPLAY_NAMES.get(code, code)
            secondary = _secondary_label(code)
            if native == secondary:
                label = native
            else:
                label = f"{native} · {secondary}"
            if code == active:
                check = Color.apply("✔", Color.GREEN)
            else:
                check = " "
            rows.append(f"{i:>2}) {check} {label}")
        return rows

    def _hrule(self) -> str:
        return hrule(_INNER_CONTENT_WIDTH)

    def print_menu(self) -> None:
        active_code = current_language() or "en"
        native_active = LANGUAGE_DISPLAY_NAMES.get(active_code, active_code)
        secondary_active = _secondary_label(active_code)
        if native_active == secondary_active:
            status = native_active
        else:
            status = f"{native_active} ({secondary_active})"
        status_line = Color.apply(
            _tr("Currently active: {}").format(status), Color.CYAN
        )
        rows = self._display_rows()
        section_hint = _tr("Select a language from the list below.")
        hr = self._hrule()
        menu = (
            f"{hr}\n"
            f"{box_line(status_line, _INNER_CONTENT_WIDTH)}\n"
            f"{hr}\n"
            f"{box_line(section_hint, _INNER_CONTENT_WIDTH)}\n"
            f"{hr}\n"
        )
        for r in rows:
            menu += f"{box_line(r, _INNER_CONTENT_WIDTH)}\n"
        menu += f"{hr}\n"
        print(menu, end="")

    def select_language(self, **kwargs) -> None:
        code: str = kwargs.get("opt_data", "")
        if code not in SUPPORTED_LANGUAGES:
            return
        settings = KiauhSettings()
        settings.kiauh.language = code
        settings.save()
        setup_i18n(code)
        self.title = _tr("Language")
