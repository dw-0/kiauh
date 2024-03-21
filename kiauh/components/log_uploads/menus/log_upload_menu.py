# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.log_uploads.log_upload_utils import get_logfile_list
from components.log_uploads.log_upload_utils import upload_logfile
from core.menus import BACK_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_YELLOW


# noinspection PyMethodMayBeStatic
class LogUploadMenu(BaseMenu):
    def __init__(self):
        self.logfile_list = get_logfile_list()
        options = {index: self.upload for index in range(len(self.logfile_list))}
        super().__init__(
            header=True,
            options=options,
            footer_type=BACK_FOOTER,
        )

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

        logfile_list = get_logfile_list()
        for logfile in enumerate(logfile_list):
            line = f"{logfile[0]}) {logfile[1].get('display_name')}"
            menu += f"| {line:<54}|\n"

        print(menu, end="")

    def upload(self, **kwargs):
        upload_logfile(self.logfile_list[kwargs.get("opt_index")])
