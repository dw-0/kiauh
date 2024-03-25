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
from typing import List, Union
from typing import TypedDict

from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    print_instance_overview,
    DisplayType,
)
from core.base_extension import BaseExtension
from core.instance_manager.base_instance import BaseInstance
from core.instance_manager.instance_manager import InstanceManager
from core.menus import BACK_FOOTER
from core.menus.base_menu import BaseMenu
from core.repo_manager.repo_manager import RepoManager
from utils.constants import COLOR_YELLOW, COLOR_CYAN, RESET_FORMAT
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
        install_menu = MainsailThemeInstallMenu(self.instances)
        install_menu.start()

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
        self.instances = instances
        self.themes: List[ThemeData] = self.load_themes()
        options = {f"{index}": self.install_theme for index in range(len(self.themes))}
        super().__init__(
            header=False,
            options=options,
            footer_type=BACK_FOOTER,
        )

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

        repo_manager = RepoManager(theme_repo_url, "")
        for printer in printer_list:
            repo_manager.target_dir = printer.cfg_dir.joinpath(".theme")
            repo_manager.clone_repo()

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
