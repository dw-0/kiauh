# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import csv
import shutil
import textwrap
import urllib.request
from typing import List, Optional, Type, TypedDict, Union

from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    DisplayType,
    print_instance_overview,
)
from core.instance_manager.base_instance import BaseInstance
from core.instance_manager.instance_manager import InstanceManager
from core.menus import Option
from core.menus.base_menu import BaseMenu
from extensions.base_extension import BaseExtension
from utils.constants import COLOR_CYAN, COLOR_YELLOW, RESET_FORMAT
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_selection_input
from utils.logger import Logger


class ThemeData(TypedDict):
    name: str
    short_note: str
    author: str
    repo: str


# noinspection PyMethodMayBeStatic
class MainsailThemeInstallerExtension(BaseExtension):
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances

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
            Logger.print_status(f"Uninstalling theme from {printer.cfg_dir} ...")
            theme_dir = printer.cfg_dir.joinpath(".theme")
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
        self.themes: List[ThemeData] = self.load_themes()
        self.instances = instances

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from extensions.extensions_menu import ExtensionsMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else ExtensionsMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{index}": Option(self.install_theme, False, opt_index=f"{index}")
            for index in range(len(self.themes))
        }

    def print_menu(self) -> None:
        header = " [ Mainsail Theme Installer ] "
        color = COLOR_YELLOW
        line1 = f"{COLOR_CYAN}A preview of each Mainsail theme can be found here:{RESET_FORMAT}"
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {line1:<62} |
            | https://docs.mainsail.xyz/theming/themes              |
            |-------------------------------------------------------|
            """
        )[1:]
        for i, theme in enumerate(self.themes):
            i = f" {i}" if i < 10 else f"{i}"
            row = f"{i}) [{theme.get('name')}]"
            menu += f"| {row:<53} |\n"
        print(menu, end="")

    def load_themes(self) -> List[ThemeData]:
        with urllib.request.urlopen(self.THEMES_URL) as response:
            themes: List[ThemeData] = []
            csv_data: str = response.read().decode().splitlines()
            csv_reader = csv.DictReader(csv_data, delimiter=",")
            for row in csv_reader:
                row: ThemeData = row
                themes.append(row)

        return themes

    def install_theme(self, **kwargs):
        index = int(kwargs.get("opt_index"))
        theme_data: ThemeData = self.themes[index]
        theme_author: str = theme_data.get("author")
        theme_repo: str = theme_data.get("repo")
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
            git_clone_wrapper(theme_repo_url, printer.cfg_dir.joinpath(".theme"))

        if len(theme_data.get("short_note", "")) > 1:
            Logger.print_warn("Info from the creator:", prefix=False, start="\n")
            Logger.print_info(theme_data.get("short_note"), prefix=False, end="\n\n")


def get_printer_selection(
    instances: List[BaseInstance], is_install: bool
) -> Union[List[BaseInstance], None]:
    options = [str(i) for i in range(len(instances))]
    options.extend(["a", "A", "b", "B"])

    if is_install:
        q = "Select the printer to install the theme for"
    else:
        q = "Select the printer to remove the theme from"
    selection = get_selection_input(q, options)

    install_for = []
    if selection == "b".lower():
        return None
    elif selection == "a".lower():
        install_for.extend(instances)
    else:
        instance = instances[int(selection)]
        install_for.append(instance)

    return install_for
