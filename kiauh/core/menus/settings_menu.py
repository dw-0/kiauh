# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Literal, Tuple, Type

from components.klipper import KLIPPER_DIR, KLIPPER_REPO_URL
from components.klipper.klipper_utils import get_klipper_status
from components.moonraker import MOONRAKER_DIR, MOONRAKER_REPO_URL
from components.moonraker.utils.utils import get_moonraker_status
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings, RepoSettings
from core.types.color import Color
from procedures.switch_repo import run_switch_repo_routine
from utils.input_utils import get_confirm, get_string_input


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
        self._load_settings()
        print(self.klipper_status)

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.set_klipper_repo),
            "2": Option(method=self.set_moonraker_repo),
            "3": Option(method=self.toggle_mainsail_release),
            "4": Option(method=self.toggle_fluidd_release),
            "5": Option(method=self.toggle_backup_before_update),
        }

    def print_menu(self) -> None:
        color = Color.CYAN
        checked = f"[{Color.apply('x', Color.GREEN)}]"
        unchecked = "[ ]"

        kl_repo: str = Color.apply(self.klipper_status.repo, color)
        kl_branch: str = Color.apply(self.klipper_status.branch, color)
        kl_owner: str = Color.apply(self.klipper_status.owner, color)
        mr_repo: str = Color.apply(self.moonraker_status.repo, color)
        mr_branch: str = Color.apply(self.moonraker_status.branch, color)
        mr_owner: str = Color.apply(self.moonraker_status.owner, color)
        o1 = checked if self.mainsail_unstable else unchecked
        o2 = checked if self.fluidd_unstable else unchecked
        o3 = checked if self.auto_backups_enabled else unchecked
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Klipper:                                              ║
            ║  ● Repo:   {kl_repo:51} ║
            ║  ● Owner:  {kl_owner:51} ║
            ║  ● Branch: {kl_branch:51} ║
            ╟───────────────────────────────────────────────────────╢
            ║ Moonraker:                                            ║
            ║  ● Repo:   {mr_repo:51} ║
            ║  ● Owner:  {mr_owner:51} ║
            ║  ● Branch: {mr_branch:51} ║
            ╟───────────────────────────────────────────────────────╢
            ║ Install unstable releases:                            ║
            ║  {o1} Mainsail                                         ║
            ║  {o2} Fluidd                                           ║
            ╟───────────────────────────────────────────────────────╢
            ║ Auto-Backup:                                          ║
            ║  {o3} Automatic backup before update                   ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Set Klipper source repository                      ║
            ║ 2) Set Moonraker source repository                    ║
            ║                                                       ║
            ║ 3) Toggle unstable Mainsail releases                  ║
            ║ 4) Toggle unstable Fluidd releases                    ║
            ║                                                       ║
            ║ 5) Toggle automatic backups before updates            ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def _load_settings(self) -> None:
        self.settings = KiauhSettings()
        self.auto_backups_enabled = self.settings.kiauh.backup_before_update
        self.mainsail_unstable = self.settings.mainsail.unstable_releases
        self.fluidd_unstable = self.settings.fluidd.unstable_releases

        # by default, we show the status of the installed repositories
        self.klipper_status = get_klipper_status()
        self.moonraker_status = get_moonraker_status()
        # if the repository is not installed, we show the status of the settings from the config file
        if self.klipper_status.repo == "-":
            url_parts = self.settings.klipper.repo_url.split("/")
            self.klipper_status.repo = url_parts[-1]
            self.klipper_status.owner = url_parts[-2]
            self.klipper_status.branch = self.settings.klipper.branch
        if self.moonraker_status.repo == "-":
            url_parts = self.settings.moonraker.repo_url.split("/")
            self.moonraker_status.repo = url_parts[-1]
            self.moonraker_status.owner = url_parts[-2]
            self.moonraker_status.branch = self.settings.moonraker.branch

    def _gather_input(
        self, repo_name: Literal["klipper", "moonraker"], repo_dir: Path
    ) -> Tuple[str, str]:
        warn_msg = [
            "There is only basic input validation in place! "
            "Make sure your the input is valid and has no typos or invalid characters!"
        ]

        if repo_dir.exists():
            warn_msg.extend(
                [
                    "For the change to take effect, the new repository will be cloned. "
                    "A backup of the old repository will be created.",
                    "\n\n",
                    "Make sure you don't have any ongoing prints running, as the services "
                    "will be restarted during this process! You will loose any ongoing print!",
                ]
            )

        Logger.print_dialog(DialogType.ATTENTION, warn_msg)

        repo = get_string_input(
            "Enter new repository URL",
            regex=r"^[\w/.:-]+$",
            default=KLIPPER_REPO_URL if repo_name == "klipper" else MOONRAKER_REPO_URL,
        )
        branch = get_string_input(
            "Enter new branch name", regex=r"^.+$", default="master"
        )

        return repo, branch

    def _set_repo(
        self, repo_name: Literal["klipper", "moonraker"], repo_dir: Path
    ) -> None:
        repo_url, branch = self._gather_input(repo_name, repo_dir)
        display_name = repo_name.capitalize()
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                f"New {display_name} repository URL:",
                f"● {repo_url}",
                f"New {display_name} repository branch:",
                f"● {branch}",
            ],
        )

        if get_confirm("Apply changes?", allow_go_back=True):
            repo: RepoSettings = self.settings[repo_name]
            repo.repo_url = repo_url
            repo.branch = branch

            self.settings.save()
            self._load_settings()

            Logger.print_ok("Changes saved!")
        else:
            Logger.print_info(
                f"Changing of {display_name} source repository canceled ..."
            )
            return

        self._switch_repo(repo_name, repo_dir)

    def _switch_repo(
        self, name: Literal["klipper", "moonraker"], repo_dir: Path
    ) -> None:
        if not repo_dir.exists():
            return

        Logger.print_status(
            f"Switching to {name.capitalize()}'s new source repository ..."
        )

        repo: RepoSettings = self.settings[name]
        run_switch_repo_routine(name, repo)

    def set_klipper_repo(self, **kwargs) -> None:
        self._set_repo("klipper", KLIPPER_DIR)

    def set_moonraker_repo(self, **kwargs) -> None:
        self._set_repo("moonraker", MOONRAKER_DIR)

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
