# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import importlib
import inspect
import json
import textwrap
from pathlib import Path
from typing import Dict, List, Type

from core.constants import COLOR_CYAN, COLOR_YELLOW, RESET_FORMAT
from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from extensions import EXTENSION_ROOT
from extensions.base_extension import BaseExtension


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionsMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.extensions: Dict[str, BaseExtension] = self.discover_extensions()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            i: Option(self.extension_submenu, opt_data=self.extensions.get(i))
            for i in self.extensions
        }

    def discover_extensions(self) -> Dict[str, BaseExtension]:
        ext_dict = {}

        for ext in EXTENSION_ROOT.iterdir():
            metadata_json = Path(ext).joinpath("metadata.json")
            if not metadata_json.exists():
                continue

            try:
                with open(metadata_json, "r") as m:
                    # read extension metadata from json
                    metadata = json.load(m).get("metadata")
                    module_name = metadata.get("module")
                    module_path = f"kiauh.extensions.{ext.name}.{module_name}"

                    # get the class name of the extension
                    ext_class: Type[BaseExtension] = inspect.getmembers(
                        importlib.import_module(module_path),
                        predicate=lambda o: inspect.isclass(o)
                        and issubclass(o, BaseExtension)
                        and o != BaseExtension,
                    )[0][1]

                    # instantiate the extension with its metadata and add to dict
                    ext_instance: BaseExtension = ext_class(metadata)
                    ext_dict[f"{metadata.get('index')}"] = ext_instance

            except (IOError, json.JSONDecodeError, ImportError) as e:
                print(f"Failed loading extension {ext}: {e}")

        return dict(sorted(ext_dict.items()))

    def extension_submenu(self, **kwargs):
        ExtensionSubmenu(kwargs.get("opt_data"), self.__class__).run()

    def print_menu(self) -> None:
        header = " [ Extensions Menu ] "
        color = COLOR_CYAN
        line1 = f"{COLOR_YELLOW}Available Extensions:{RESET_FORMAT}"
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            ║ {line1:<62} ║
            ║                                                       ║
            """
        )[1:]
        print(menu, end="")

        for extension in self.extensions.values():
            index = extension.metadata.get("index")
            name = extension.metadata.get("display_name")
            row = f"{index}) {name}"
            print(f"║ {row:<53} ║")
        print("╟───────────────────────────────────────────────────────╢")


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionSubmenu(BaseMenu):
    def __init__(
        self, extension: BaseExtension, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.extension = extension
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu if previous_menu is not None else ExtensionsMenu
        )

    def set_options(self) -> None:
        self.options["1"] = Option(self.extension.install_extension)
        if self.extension.metadata.get("updates"):
            self.options["2"] = Option(self.extension.update_extension)
            self.options["3"] = Option(self.extension.remove_extension)
        else:
            self.options["2"] = Option(self.extension.remove_extension)

    def print_menu(self) -> None:
        header = f" [ {self.extension.metadata.get('display_name')} ] "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        line_width = 53
        description: List[str] = self.extension.metadata.get("description", [])
        description_text = Logger.format_content(
            description,
            line_width,
            border_left="║",
            border_right="║",
        )

        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        menu += f"{description_text}\n"
        menu += textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Install                                            ║
            """
        )[1:]

        if self.extension.metadata.get("updates"):
            menu += "║ 2) Update                                             ║\n"
            menu += "║ 3) Remove                                             ║\n"
        else:
            menu += "║ 2) Remove                                             ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")
