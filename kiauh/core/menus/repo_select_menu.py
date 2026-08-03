# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from typing import List, Literal, Type

from core.i18n import _tr
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings, Repository
from core.types.color import Color
from procedures.switch_repo import run_switch_repo_routine
from utils.input_utils import get_confirm, get_number_input, get_string_input


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
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
        self.input_label_txt = _tr("Select repository")
        self.name = name
        self.repos = repos

        if self.name == "klipper":
            self.title = _tr("Klipper Repository Selection Menu")

        elif self.name == "moonraker":
            self.title = _tr("Moonraker Repository Selection Menu")

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.settings_menu import SettingsMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else SettingsMenu
        )

    def set_options(self) -> None:
        self.options = {}
        if self.repos:
            for idx, repo in enumerate(self.repos, start=1):
                self.options[str(idx)] = Option(
                    method=self.select_repository, opt_data=repo
                )
        self.options["a"] = Option(method=self.add_repository)
        self.options["r"] = Option(method=self.remove_repository)
        self.options["b"] = Option(method=self.go_back)

    def print_menu(self) -> None:
        available_repos_header = _tr("Available Repositories:")
        add_repo_label = _tr("A) Add repository")
        remove_repo_label = _tr("R) Remove repository")
        menu = "╟───────────────────────────────────────────────────────╢\n"
        menu += f"║ {available_repos_header:<55} ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"
        for idx, repo in enumerate(self.repos, start=1):
            url_label = _tr("● Repo:")
            branch_label = _tr("└► Branch:")
            url = f"{url_label} {repo.url.replace('.git', '')}"
            branch = f"{branch_label} {repo.branch}"
            menu += f"║ {idx}) {Color.apply(url, Color.CYAN):<59} ║\n"
            menu += f"║    {Color.apply(branch, Color.CYAN):<59} ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"
        menu += f"║ {add_repo_label:<55} ║\n"
        menu += f"║ {remove_repo_label:<55} ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"
        print(menu, end="")

    def select_repository(self, **kwargs) -> None:
        repo: Repository = kwargs.get("opt_data")
        Logger.print_status(
            _tr("Switching to {name}'s new source repository ...").format(
                name=self.name.capitalize()
            )
        )
        run_switch_repo_routine(self.name, repo.url, repo.branch)

    def add_repository(self, **kwargs) -> None:
        while True:
            Logger.print_dialog(
                DialogType.CUSTOM,
                custom_title=_tr("Enter the repository URL"),
                content=[
                    _tr(
                        "NOTE: There is no input validation in place, "
                        "please check your input for correctness"
                    ),
                ],
            )
            url = get_string_input(
                _tr("Repository URL"), allow_special_chars=True
            ).strip()

            Logger.print_dialog(
                DialogType.CUSTOM,
                custom_title=_tr("Enter the branch name"),
                content=[_tr("Press Enter to use the default branch (master).")],
                center_content=False,
            )
            branch = get_string_input(
                _tr("Branch"), allow_special_chars=True, default="master"
            ).strip()
            Logger.print_dialog(
                DialogType.CUSTOM,
                custom_title=_tr("Summary"),
                content=[
                    f"● URL:    {url}",
                    f"● Branch: {branch}",
                ],
            )
            confirm = get_confirm(_tr("Save repository"))
            if confirm:
                repo = Repository(url, branch)
                if self.name == "klipper":
                    self.settings.klipper.repositories.append(repo)
                    self.settings.save()
                    self.repos = self.settings.klipper.repositories
                else:
                    self.settings.moonraker.repositories.append(repo)
                    self.settings.save()
                    self.repos = self.settings.moonraker.repositories
                Logger.print_ok(_tr("Repository added and saved."))

                self.set_options()
                self.run()
                break
            else:
                Logger.print_info(_tr("Operation cancelled by user."))
                break

    def remove_repository(self, **kwargs) -> None:
        repos = self.repos
        if not repos:
            Logger.print_info(_tr("No repositories configured."))
            return
        repo_lines = [
            f"{idx}) {repo.url} [{repo.branch}]"
            for idx, repo in enumerate(repos, start=1)
        ]
        Logger.print_dialog(
            DialogType.CUSTOM,
            custom_title=_tr("Available Repositories"),
            content=[*repo_lines],
        )
        idx = get_number_input(_tr("Select the repository to remove"), 1, len(repos))
        removed = repos.pop(idx - 1)
        if self.name == "klipper":
            self.settings.klipper.repositories = repos
            self.settings.save()
            self.repos = self.settings.klipper.repositories
        else:
            self.settings.moonraker.repositories = repos
            self.settings.save()
            self.repos = self.settings.moonraker.repositories
        Logger.print_ok(
            _tr("Removed repository: {url} [{branch}]").format(
                url=removed.url, branch=removed.branch
            )
        )

        self.set_options()
        self.run()

    def go_back(self, **kwargs) -> None:
        from core.menus.settings_menu import SettingsMenu
        SettingsMenu().run()
