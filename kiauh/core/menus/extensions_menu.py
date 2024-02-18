#!/usr/bin/env python3

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
from typing import List, Dict

from core.base_extension import BaseExtension
from core.menus import BACK_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_CYAN, COLOR_YELLOW


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionsMenu(BaseMenu):
    def __init__(self):
        self.extensions = self.discover_extensions()
        super().__init__(
            header=True,
            options=self.get_options(),
            footer_type=BACK_FOOTER,
        )

    def discover_extensions(self) -> List[BaseExtension]:
        extensions = []
        extensions_dir = Path(__file__).resolve().parents[2].joinpath("extensions")

        for extension in extensions_dir.iterdir():
            metadata_json = Path(extension).joinpath("metadata.json")
            if not metadata_json.exists():
                continue

            try:
                with open(metadata_json, "r") as m:
                    metadata = json.load(m).get("metadata")
                    module_name = (
                        f"kiauh.extensions.{extension.name}.{metadata.get('module')}"
                    )
                    name, extension = inspect.getmembers(
                        importlib.import_module(module_name),
                        predicate=lambda o: inspect.isclass(o)
                        and issubclass(o, BaseExtension)
                        and o != BaseExtension,
                    )[0]
                    extensions.append(extension(metadata))
            except (IOError, json.JSONDecodeError, ImportError) as e:
                print(f"Failed loading extension {extension}: {e}")

        return sorted(extensions, key=lambda ex: ex.metadata.get("index"))

    def get_options(self) -> Dict[str, BaseMenu]:
        options = {}
        for extension in self.extensions:
            index = extension.metadata.get("index")
            options[f"{index}"] = ExtensionSubmenu(extension)

        return options

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

        for extension in self.extensions:
            index = extension.metadata.get("index")
            name = extension.metadata.get("display_name")
            row = f"{index}) {name}"
            print(f"| {row:<53} |")


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class ExtensionSubmenu(BaseMenu):
    def __init__(self, extension: BaseExtension):
        self.extension = extension
        self.extension_name = extension.metadata.get("display_name")
        self.extension_desc = extension.metadata.get("description")
        super().__init__(
            header=False,
            options={
                "1": extension.install_extension,
                "2": extension.remove_extension,
            },
            footer_type=BACK_FOOTER,
        )

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
            | 2) Remove                                             |
            """
        )[1:]
        print(menu, end="")
