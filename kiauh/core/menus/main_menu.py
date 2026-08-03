# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import sys
import textwrap
from typing import Callable, Type

from components.crowsnest.crowsnest import get_crowsnest_status
from components.klipper.klipper_utils import get_klipper_status
from components.klipperscreen.klipperscreen import get_klipperscreen_status
from components.log_uploads.menus.log_upload_menu import LogUploadMenu
from components.moonraker.utils.utils import get_moonraker_status
from components.webui_client.client_utils import (
    get_client_status,
    get_current_client_config,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.i18n import (
    LANGUAGE_DISPLAY_NAMES,
    _tr,
    current_language,
)
from core.logger import Logger
from core.menus import FooterType
from core.menus.advanced_menu import AdvancedMenu
from core.menus.align import display_width
from core.menus.backup_menu import BackupMenu
from core.menus.base_menu import BaseMenu, Option
from core.menus.install_menu import InstallMenu
from core.menus.language_menu import LanguageMenu
from core.menus.remove_menu import RemoveMenu
from core.menus.settings_menu import SettingsMenu
from core.menus.update_menu import UpdateMenu
from core.types.color import Color
from core.types.component_status import ComponentStatus, get_status_text
from extensions.extensions_menu import ExtensionsMenu
from utils.common import get_kiauh_version, trunc_string


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MainMenu(BaseMenu):
    def __init__(self) -> None:
        super().__init__()

        self.header: bool = True
        self.title = _tr("Main Menu")
        self.title_color = Color.CYAN
        self.footer_type: FooterType = FooterType.QUIT

        self.version = ""
        self.kl_status, self.kl_owner, self.kl_repo = "", "", ""
        self.mr_status, self.mr_owner, self.mr_repo = "", "", ""
        self.ms_status, self.fl_status, self.ks_status = "", "", ""
        self.cn_status, self.cc_status = "", ""
        self._init_status()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        """MainMenu does not have a previous menu"""
        pass

    def set_options(self) -> None:
        self.options = {
            "0": Option(method=self.log_upload_menu),
            "1": Option(method=self.install_menu),
            "2": Option(method=self.update_menu),
            "3": Option(method=self.remove_menu),
            "4": Option(method=self.advanced_menu),
            "5": Option(method=self.backup_menu),
            "e": Option(method=self.extension_menu),
            "s": Option(method=self.settings_menu),
            "l": Option(method=self.language_picker),
        }

    def _init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "cn"]
        for var in status_vars:
            setattr(
                self,
                f"{var}_status",
                Color.apply(_tr("Not installed"), Color.RED),
            )

    def _fetch_status(self) -> None:
        self.version = get_kiauh_version()
        self._get_component_status("kl", get_klipper_status)
        self._get_component_status("mr", get_moonraker_status)
        self._get_component_status("ms", get_client_status, MainsailData())
        self._get_component_status("fl", get_client_status, FluiddData())
        self._get_component_status("ks", get_klipperscreen_status)
        self._get_component_status("cn", get_crowsnest_status)
        self.cc_status = get_current_client_config()

    def _get_component_status(self, name: str, status_fn: Callable, *args) -> None:
        status_data: ComponentStatus = status_fn(*args)
        code: int = status_data.status
        status: str = get_status_text(code)
        owner: str = trunc_string(status_data.owner, 23) if status_data.owner else '-'
        repo: str = trunc_string(status_data.repo, 23) if status_data.repo else '-'
        instance_count: int = status_data.instances

        count_txt: str = ""
        if instance_count > 0 and code == 2:
            count_txt = f": {instance_count}"

        setattr(self, f"{name}_status", self._format_by_code(code, status, count_txt))
        setattr(self, f"{name}_owner", Color.apply(owner, Color.CYAN))
        setattr(self, f"{name}_repo", Color.apply(repo, Color.CYAN))

    def _format_by_code(self, code: int, status: str, count: str) -> str:
        color = Color.RED
        if code == 0:
            color = Color.RED
        elif code == 1:
            color = Color.YELLOW
        elif code == 2:
            color = Color.GREEN

        return Color.apply(f"{status}{count}", color)

    def print_menu(self) -> None:
        self._fetch_status()
        current_lang = current_language() or "en"
        lang_display = LANGUAGE_DISPLAY_NAMES.get(current_lang, "English")

        footer1 = Color.apply(self.version, Color.CYAN)
        link = Color.apply("https://git.io/JnmlX", Color.MAGENTA)
        footer2 = f"{_tr('Changelog:')} {link}"

        # Match the original KIAUH 66-wide box used by InstallMenu/UpdateMenu/
        # RemoveMenu/BackupMenu/AdvancedMenu (measured in earlier script capture).
        # Content layout: ║<sp>LEFT<sp>│<sp>RIGHT<sp>║  →  2+LEFT+3+RIGHT+2 = 67
        #   → LEFT + RIGHT = 60.  Use 17 / 43.
        # Divider column must be consistent across all rows:
        # left dashes/spaces = LEFT + 2, right dashes = RIGHT + 2.
        LEFT_COL_CONTENT = 17
        RIGHT_COL_CONTENT = 43
        # Check LEFT+RIGHT+7 = 17+43+7 = 67 ✓ outer target.

        def right_padded(text: str) -> str:
            pad = RIGHT_COL_CONTENT - display_width(text)
            if pad <= 0:
                return text
            return f"{text}{' ' * pad}"

        def left_padded(content: str) -> str:
            pad = LEFT_COL_CONTENT - display_width(content)
            if pad < 0:
                pad = 0
            return f"║ {content}{' ' * pad} │"

        kl = right_padded(f"Klipper: {self.kl_status}")
        klo = right_padded(f"Owner: {self.kl_owner}")
        klr = right_padded(f"Repo: {self.kl_repo}")
        mr = right_padded(f"Moonraker: {self.mr_status}")
        mro = right_padded(f"Owner: {self.mr_owner}")
        mrr = right_padded(f"Repo: {self.mr_repo}")
        ms = right_padded(f"Mainsail: {self.ms_status}")
        fl = right_padded(f"Fluidd: {self.fl_status}")
        cc = right_padded(f"Client-Config: {self.cc_status}")
        ks = right_padded(f"KlipperScreen: {self.ks_status}")
        cn = right_padded(f"Crowsnest: {self.cn_status}")
        lang_status = right_padded(f"{_tr('Language')}: {lang_display}")
        t_0 = f"0) [{_tr('Log-Upload')}]"
        t_1 = f"1) [{_tr('Install')}]"
        t_2 = f"2) [{_tr('Update')}]"
        t_3 = f"3) [{_tr('Remove')}]"
        t_4 = f"4) [{_tr('Advanced')}]"
        t_5 = f"5) [{_tr('Backup')}]"
        t_s = f"S) [{_tr('Settings')}]"
        t_l = f"L) [{_tr('Language')}]"
        t_comm = _tr("Community:")
        t_e = f"E) [{_tr('Extensions')}]"

        left_dash = LEFT_COL_CONTENT + 2
        right_dash = RIGHT_COL_CONTENT + 2

        hdr_hr = "╟" + "─" * left_dash + "┬" + "─" * right_dash + "╢"
        mid_hr = "║" + " " * (left_dash - 1) + " ├" + "─" * right_dash + "╢"
        sep_hr = "╟" + "─" * left_dash + "┼" + "─" * right_dash + "╢"
        footer_hr = "╟" + "─" * left_dash + "┼" + "─" * right_dash + "╢"
        bot_hr = "╟" + "─" * left_dash + "┴" + "─" * right_dash + "╢"

        def center_to(text: str, w: int) -> str:
            pad = w - display_width(text)
            if pad <= 0:
                return text
            lp = pad // 2
            rp = pad - lp
            return f"{' ' * lp}{text}{' ' * rp}"

        lines = [
            hdr_hr,
            f"{left_padded(t_0)} {kl} ║",
            f"{left_padded('')} {klo} ║",
            f"{left_padded(t_1)} {klr} ║",
            mid_hr,
            f"{left_padded(t_2)} {mr} ║",
            f"{left_padded(t_3)} {mro} ║",
            f"{left_padded(t_4)} {mrr} ║",
            f"{left_padded(t_5)} {mrr} ║",
            mid_hr,
            f"{left_padded(t_s)} {ms} ║",
            f"{left_padded('')} {fl} ║",
            f"{left_padded(t_l)} {cc} ║",
            f"{left_padded('')} {lang_status} ║",
            f"{left_padded(t_comm)} {right_padded('')} ║",
            f"{left_padded(t_e)} {ks} ║",
            f"{left_padded('')} {cn} ║",
            footer_hr,
            f"║ {center_to(footer1, 17)} │ {center_to(footer2, 43)} ║",
            bot_hr,
        ]
        print("\n".join(lines) + "\n", end="")

    def language_picker(self, **kwargs) -> None:
        LanguageMenu(previous_menu=self.__class__).run()

    def exit(self, **kwargs) -> None:
        Logger.print_ok(_tr("###### Happy printing!"), False)
        sys.exit(0)

    def log_upload_menu(self, **kwargs) -> None:
        LogUploadMenu().run()

    def install_menu(self, **kwargs) -> None:
        InstallMenu(previous_menu=self.__class__).run()

    def update_menu(self, **kwargs) -> None:
        UpdateMenu(previous_menu=self.__class__).run()

    def remove_menu(self, **kwargs) -> None:
        RemoveMenu(previous_menu=self.__class__).run()

    def advanced_menu(self, **kwargs) -> None:
        AdvancedMenu(previous_menu=self.__class__).run()

    def backup_menu(self, **kwargs) -> None:
        BackupMenu(previous_menu=self.__class__).run()

    def settings_menu(self, **kwargs) -> None:
        SettingsMenu(previous_menu=self.__class__).run()

    def extension_menu(self, **kwargs) -> None:
        ExtensionsMenu(previous_menu=self.__class__).run()
