# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import importlib
import inspect
import json
import textwrap
from pathlib import Path
from typing import Type, Dict

from extensions import EXTENSION_ROOT
from extensions.base_extension import BaseExtension
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_CYAN, COLOR_YELLOW


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionsMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()

        self.previous_menu: BaseMenu = previous_menu
        self.extensions = self.discover_extensions()
        self.options = {ext: self.extension_submenu for ext in self.extensions}

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

        return ext_dict

    def extension_submenu(self, **kwargs):
        extension = self.extensions.get(kwargs.get("opt_index"))
        ExtensionSubmenu(self, extension).run()

    def print_menu(self):
        header = " [ Extensions Menu ] "
        color = COLOR_CYAN
        line1 = f"{COLOR_YELLOW}Available Extensions:{RESET_FORMAT}"
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {line1:<62} |
            |                                                       |
            """
        )[1:]
        print(menu, end="")

        for extension in self.extensions.values():
            index = extension.metadata.get("index")
            name = extension.metadata.get("display_name")
            row = f"{index}) {name}"
            print(f"| {row:<53} |")


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionSubmenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu, extension: BaseExtension):
        super().__init__()

        self.extension = extension
        self.extension_name = extension.metadata.get("display_name")
        self.extension_desc = extension.metadata.get("description")

        self.previous_menu = previous_menu
        self.options["1"] = extension.install_extension
        if self.extension.metadata.get("updates"):
            self.options["2"] = extension.update_extension
            self.options["3"] = extension.remove_extension
        else:
            self.options["2"] = extension.remove_extension

    def print_menu(self) -> None:
        header = f" [ {self.extension_name} ] "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)

        wrapper = textwrap.TextWrapper(55, initial_indent="| ", subsequent_indent="| ")
        lines = wrapper.wrap(self.extension_desc)
        formatted_lines = [f"{line:<55} |" for line in lines]
        description_text = "\n".join(formatted_lines)

        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            """
        )[1:]
        menu += f"{description_text}\n"
        menu += textwrap.dedent(
            """
            |-------------------------------------------------------|
            | 1) Install                                            |
            """
        )[1:]

        if self.extension.metadata.get("updates"):
            menu += "| 2) Update                                             |\n"
            menu += "| 3) Remove                                             |\n"
        else:
            menu += "| 2) Remove                                             |\n"

        print(menu, end="")
