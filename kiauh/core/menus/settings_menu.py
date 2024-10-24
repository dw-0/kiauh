# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Literal, Tuple, Type

from components.klipper.klipper_utils import get_klipper_status
from components.moonraker.moonraker_utils import get_moonraker_status
from core.constants import COLOR_CYAN, COLOR_GREEN, RESET_FORMAT
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings, RepoSettings
from procedures.switch_repo import run_switch_repo_routine
from utils.input_utils import get_confirm, get_string_input


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class SettingsMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.klipper_status = get_klipper_status()
        self.moonraker_status = get_moonraker_status()
        self.mainsail_unstable: bool | None = None
        self.fluidd_unstable: bool | None = None
        self.auto_backups_enabled: bool | None = None
        self._load_settings()

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
        header = " [ KIAUH Settings ] "
        color, rst = COLOR_CYAN, RESET_FORMAT
        count = 62 - len(color) - len(rst)
        checked = f"[{COLOR_GREEN}x{rst}]"
        unchecked = "[ ]"

        kl_repo: str = f"{color}{self.klipper_status.repo}{rst}"
        kl_branch: str = f"{color}{self.klipper_status.branch}{rst}"
        kl_owner: str = f"{color}{self.klipper_status.owner}{rst}"
        mr_repo: str = f"{color}{self.moonraker_status.repo}{rst}"
        mr_branch: str = f"{color}{self.moonraker_status.branch}{rst}"
        mr_owner: str = f"{color}{self.moonraker_status.owner}{rst}"
        o1 = checked if self.mainsail_unstable else unchecked
        o2 = checked if self.fluidd_unstable else unchecked
        o3 = checked if self.auto_backups_enabled else unchecked
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{rst} ║
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

    def _gather_input(self) -> Tuple[str, str]:
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "There is no input validation in place! Make sure your the input is "
                "valid and has no typos or invalid characters! For the change to take "
                "effect, the new repository will be cloned. A backup of the old "
                "repository will be created.",
                "\n\n",
                "Make sure you don't have any ongoing prints running, as the services "
                "will be restarted during this process! You will loose any ongoing print!",
            ],
        )
        repo = get_string_input(
            "Enter new repository URL",
            allow_special_chars=True,
        )
        branch = get_string_input(
            "Enter new branch name",
            allow_special_chars=True,
        )

        return repo, branch

    def _set_repo(self, repo_name: Literal["klipper", "moonraker"]) -> None:
        repo_url, branch = self._gather_input()
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
                f"Skipping change of {display_name} source repository  ..."
            )
            return

        Logger.print_status(f"Switching to {display_name}'s new source repository ...")
        self._switch_repo(repo_name)

    def _switch_repo(self, name: Literal["klipper", "moonraker"]) -> None:
        repo: RepoSettings = self.settings[name]
        run_switch_repo_routine(name, repo)

    def set_klipper_repo(self, **kwargs) -> None:
        self._set_repo("klipper")

    def set_moonraker_repo(self, **kwargs) -> None:
        self._set_repo("moonraker")

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
