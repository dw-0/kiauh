# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Type

from components.klipper.klipper_utils import get_klipper_status
from components.moonraker.utils.utils import get_moonraker_status
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.menus.repo_select_menu import RepoSelectMenu
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from core.types.component_status import ComponentStatus


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class SettingsMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Settings Menu"
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu

        self.mainsail_unstable: bool | None = None
        self.fluidd_unstable: bool | None = None
        self.auto_backups_enabled: bool | None = None

        na: str = "Not available!"
        self.kl_repo_url: str = Color.apply(na, Color.RED)
        self.kl_branch: str = Color.apply(na, Color.RED)
        self.mr_repo_url: str = Color.apply(na, Color.RED)
        self.mr_branch: str = Color.apply(na, Color.RED)

        self._load_settings()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.switch_klipper_repo),
            "2": Option(method=self.switch_moonraker_repo),
            "3": Option(method=self.toggle_mainsail_release),
            "4": Option(method=self.toggle_fluidd_release),
            "5": Option(method=self.toggle_backup_before_update),
        }

    def print_menu(self) -> None:
        checked = f"[{Color.apply('x', Color.GREEN)}]"
        unchecked = "[ ]"

        o1 = checked if self.mainsail_unstable else unchecked
        o2 = checked if self.fluidd_unstable else unchecked
        o3 = checked if self.auto_backups_enabled else unchecked
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Switch Klipper source repository                   ║
            ║    ● Current repository:                              ║
            ║    └► Repo: {self.kl_repo_url:50} ║
            ║    └► Branch: {self.kl_branch:48} ║
            ╟───────────────────────────────────────────────────────╢
            ║ 2) Switch Moonraker source repository                 ║
            ║    ● Current repository:                              ║
            ║    └► Repo: {self.mr_repo_url:50} ║
            ║    └► Branch: {self.mr_branch:48} ║
            ╟───────────────────────────────────────────────────────╢
            ║ Install unstable releases:                            ║
            ║ 3) {o1} Mainsail                                       ║
            ║ 4) {o2} Fluidd                                         ║
            ╟───────────────────────────────────────────────────────╢
            ║ Auto-Backup:                                          ║
            ║ 5) {o3} Backup before update                           ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def _load_settings(self) -> None:
        self.settings = KiauhSettings()
        self.auto_backups_enabled = self.settings.kiauh.backup_before_update
        self.mainsail_unstable = self.settings.mainsail.unstable_releases
        self.fluidd_unstable = self.settings.fluidd.unstable_releases

        klipper_status: ComponentStatus = get_klipper_status()
        moonraker_status: ComponentStatus = get_moonraker_status()

        def trim_repo_url(repo: str) -> str:
            return repo.replace(".git", "").replace("https://", "").replace("git@", "")

        if klipper_status.repo:
            url = trim_repo_url(klipper_status.repo_url)
            self.kl_repo_url = Color.apply(url, Color.CYAN)
            self.kl_branch = Color.apply(klipper_status.branch, Color.CYAN)
        if moonraker_status.repo:
            url = trim_repo_url(moonraker_status.repo_url)
            self.mr_repo_url = Color.apply(url, Color.CYAN)
            self.mr_branch = Color.apply(moonraker_status.branch, Color.CYAN)

    def _warn_no_repos(self, name: str) -> None:
        Logger.print_dialog(
            DialogType.WARNING,
            [f"No {name} repositories configured in kiauh.cfg!"],
            center_content=True,
        )

    def switch_klipper_repo(self, **kwargs) -> None:
        repos = self.settings.klipper.repositories
        RepoSelectMenu("klipper", repos=repos, previous_menu=self.__class__).run()

    def switch_moonraker_repo(self, **kwargs) -> None:
        repos = self.settings.moonraker.repositories
        RepoSelectMenu("moonraker", repos=repos, previous_menu=self.__class__).run()

    def toggle_mainsail_release(self, **kwargs) -> None:
        self.mainsail_unstable = not self.mainsail_unstable
        self.settings.mainsail.unstable_releases = self.mainsail_unstable
        self.settings.save()

    def toggle_fluidd_release(self, **kwargs) -> None:
        self.fluidd_unstable = not self.fluidd_unstable
        self.settings.fluidd.unstable_releases = self.fluidd_unstable
        self.settings.save()

    def toggle_backup_before_update(self, **kwargs) -> None:
        self.auto_backups_enabled = not self.auto_backups_enabled
        self.settings.kiauh.backup_before_update = self.auto_backups_enabled
        self.settings.save()
