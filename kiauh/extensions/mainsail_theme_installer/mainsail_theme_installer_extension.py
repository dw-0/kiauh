# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import csv
import shutil
import textwrap
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Type

from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    DisplayType,
    print_instance_overview,
)
from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color
from extensions.base_extension import BaseExtension
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_selection_input
from utils.instance_type import InstanceType
from utils.instance_utils import get_instances


@dataclass
class ThemeData:
    name: str
    short_note: str
    author: str
    repo: str


# noinspection PyMethodMayBeStatic
class MainsailThemeInstallerExtension(BaseExtension):
    instances: List[Klipper] = get_instances(Klipper)

    def install_extension(self, **kwargs) -> None:
        MainsailThemeInstallMenu(self.instances).run()

    def remove_extension(self, **kwargs) -> None:
        print_instance_overview(
            self.instances,
            display_type=DisplayType.PRINTER_NAME,
            show_headline=True,
            show_index=True,
            show_select_all=True,
        )
        printer_list = get_printer_selection(self.instances, True)
        if printer_list is None:
            return

        for printer in printer_list:
            Logger.print_status(f"Uninstalling theme from {printer.base.cfg_dir} ...")
            theme_dir = printer.base.cfg_dir.joinpath(".theme")
            if not theme_dir.exists():
                Logger.print_info(f"{theme_dir} not found. Skipping ...")
                continue
            try:
                shutil.rmtree(theme_dir)
                Logger.print_ok("Theme successfully uninstalled!")
            except OSError as e:
                Logger.print_error("Unable to uninstall theme")
                Logger.print_error(e)


# noinspection PyMethodMayBeStatic
class MainsailThemeInstallMenu(BaseMenu):
    THEMES_URL: str = (
        "https://raw.githubusercontent.com/mainsail-crew/gb-docs/main/_data/themes.csv"
    )

    def __init__(self, instances: List[Klipper]):
        super().__init__()
        self.title = "Mainsail Theme Installer"
        self.title_color = Color.YELLOW
        self.themes: List[ThemeData] = self.load_themes()
        self.instances = instances

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from extensions.extensions_menu import ExtensionsMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else ExtensionsMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{index}": Option(self.install_theme, opt_index=f"{index}")
            for index in range(len(self.themes))
        }

    def print_menu(self) -> None:
        line1 = Color.apply(
            "A preview of each Mainsail theme can be found here:", Color.YELLOW
        )
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {line1:<62} ║
            ║ https://docs.mainsail.xyz/theming/themes              ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        for i, theme in enumerate(self.themes):
            j: str = f" {i}" if i < 10 else f"{i}"
            row: str = f"{j}) [{theme.name}]"
            menu += f"║ {row:<53} ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"
        print(menu, end="")

    def load_themes(self) -> List[ThemeData]:
        with urllib.request.urlopen(self.THEMES_URL) as response:
            themes: List[ThemeData] = []
            content: str = response.read().decode()
            csv_data: List[str] = content.splitlines()
            fieldnames = ["name", "short_note", "author", "repo"]
            csv_reader = csv.DictReader(csv_data, fieldnames=fieldnames, delimiter=",")
            next(csv_reader)  # skip the header of the csv file
            for row in csv_reader:
                row: Dict[str, str]  # type: ignore
                theme: ThemeData = ThemeData(**row)
                themes.append(theme)

        return themes

    def install_theme(self, **kwargs: Any):
        opt_index: str | None = kwargs.get("opt_index", None)

        if not opt_index:
            raise ValueError("No option index provided")

        index: int = int(opt_index)
        theme_data: ThemeData = self.themes[index]
        theme_author: str = theme_data.author
        theme_repo: str = theme_data.repo
        theme_repo_url: str = f"https://github.com/{theme_author}/{theme_repo}"

        print_instance_overview(
            self.instances,
            display_type=DisplayType.PRINTER_NAME,
            show_headline=True,
            show_index=True,
            show_select_all=True,
        )

        printer_list = get_printer_selection(self.instances, True)
        if printer_list is None:
            return

        for printer in printer_list:
            git_clone_wrapper(theme_repo_url, printer.base.cfg_dir.joinpath(".theme"))

        if len(theme_data.short_note) > 1:
            Logger.print_warn("Info from the creator:", prefix=False, start="\n")
            Logger.print_info(theme_data.short_note, prefix=False, end="\n\n")


def get_printer_selection(
    instances: List[InstanceType], is_install: bool
) -> List[InstanceType] | None:
    options = [str(i) for i in range(len(instances))]
    options.extend(["a", "b"])

    if is_install:
        q = "Select the printer to install the theme for"
    else:
        q = "Select the printer to remove the theme from"
    selection = get_selection_input(q, options)

    install_for = []
    if selection == "b":
        return None
    elif selection == "a":
        install_for.extend(instances)
    else:
        instance = instances[int(selection)]
        install_for.append(instance)

    return install_for
