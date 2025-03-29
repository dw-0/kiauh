# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from typing import List, Literal, Type

from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings, Repository
from core.types.color import Color
from procedures.switch_repo import run_switch_repo_routine


class RepoSelectMenu(BaseMenu):
    def __init__(
        self,
        name: Literal["klipper", "moonraker"],
        repos: List[Repository],
        previous_menu: Type[BaseMenu] | None = None,
    ) -> None:
        super().__init__()
        self.title_color = Color.CYAN
        self.previous_menu = previous_menu
        self.settings = KiauhSettings()
        self.input_label_txt = "Select repository"
        self.name = name
        self.repos = repos

        if self.name == "klipper":
            self.title = "Klipper Repository Selection Menu"

        elif self.name == "moonraker":
            self.title = "Moonraker Repository Selection Menu"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.settings_menu import SettingsMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else SettingsMenu
        )

    def set_options(self) -> None:
        self.options = {}

        if not self.repos:
            return

        for idx, repo in enumerate(self.repos, start=1):
            self.options[str(idx)] = Option(
                method=self.select_repository, opt_data=repo
            )

    def print_menu(self) -> None:
        menu = "╟───────────────────────────────────────────────────────╢\n"
        menu += "║ Available Repositories:                               ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        for idx, repo in enumerate(self.repos, start=1):
            url = f"● Repo: {repo.url.replace('.git', '')}"
            branch = f"└► Branch: {repo.branch}"
            menu += f"║ {idx}) {Color.apply(url, Color.CYAN):<59} ║\n"
            menu += f"║    {Color.apply(branch, Color.CYAN):<59} ║\n"

        menu += "╟───────────────────────────────────────────────────────╢\n"
        print(menu, end="")

    def select_repository(self, **kwargs) -> None:
        repo: Repository = kwargs.get("opt_data")
        Logger.print_status(
            f"Switching to {self.name.capitalize()}'s new source repository ..."
        )
        run_switch_repo_routine(self.name, repo.url, repo.branch)
