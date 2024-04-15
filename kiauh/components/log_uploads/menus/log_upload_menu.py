# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import Type, Optional

from components.log_uploads.log_upload_utils import get_logfile_list
from components.log_uploads.log_upload_utils import upload_logfile
from core.menus import Option
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_YELLOW


# noinspection PyMethodMayBeStatic
class LogUploadMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu
        self.logfile_list = get_logfile_list()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self) -> None:
        self.options = {
            f"{index}": Option(self.upload, False, opt_index=f"{index}")
            for index in range(len(self.logfile_list))
        }

    def print_menu(self):
        header = " [ Log Upload ] "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | You can select the following logfiles for uploading:  |
            |                                                       |
            """
        )[1:]

        for logfile in enumerate(self.logfile_list):
            line = f"{logfile[0]}) {logfile[1].get('display_name')}"
            menu += f"| {line:<54}|\n"

        print(menu, end="")

    def upload(self, **kwargs):
        index = int(kwargs.get("opt_index"))
        upload_logfile(self.logfile_list[index])
