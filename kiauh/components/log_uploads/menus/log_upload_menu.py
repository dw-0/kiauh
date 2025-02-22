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
from typing import Type

from components.log_uploads.log_upload_utils import get_logfile_list, upload_logfile
from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color


# noinspection PyMethodMayBeStatic
class LogUploadMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Log Upload"
        self.title_color = Color.YELLOW
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.logfile_list = get_logfile_list()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            f"{index}": Option(self.upload, opt_index=f"{index}")
            for index in range(len(self.logfile_list))
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ You can select the following logfiles for uploading:  ║
            ║                                                       ║
            """
        )[1:]

        for logfile in enumerate(self.logfile_list):
            line = f"{logfile[0]}) {logfile[1].get('display_name')}"
            menu += f"║ {line:<54}║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def upload(self, **kwargs):
        try:
            index: int | None = kwargs.get("opt_index", None)
            if index is None:
                raise Exception("opt_index is None")

            index = int(index)
            upload_logfile(self.logfile_list[index])
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Log upload failed!")
