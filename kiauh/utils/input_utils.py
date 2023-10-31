#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import Optional, List, Union

from kiauh.utils.constants import COLOR_CYAN, RESET_FORMAT
from kiauh.utils.logger import Logger


def get_confirm(
    question: str, default_choice=True, allow_go_back=False
) -> Union[bool, None]:
    options_confirm = ["y", "yes"]
    options_decline = ["n", "no"]
    options_go_back = ["b", "B"]

    if default_choice:
        def_choice = "(Y/n)"
        options_confirm.append("")
    else:
        def_choice = "(y/N)"
        options_decline.append("")

    while True:
        choice = (
            input(f"{COLOR_CYAN}###### {question} {def_choice}: {RESET_FORMAT}")
            .strip()
            .lower()
        )

        if choice in options_confirm:
            return True
        elif choice in options_decline:
            return False
        elif allow_go_back and choice in options_go_back:
            return None
        else:
            Logger.print_error("Invalid choice. Please select 'y' or 'n'.")


def get_number_input(
    question: str, min_count: int, max_count=None, default=None, allow_go_back=False
) -> Union[int, None]:
    options_go_back = ["b", "B"]
    _question = question + f" (default={default})" if default else question
    _question = f"{COLOR_CYAN}###### {_question}: {RESET_FORMAT}"
    while True:
        try:
            _input = input(_question)
            if allow_go_back and _input in options_go_back:
                return None

            if _input == "":
                return default

            if max_count is not None:
                if min_count <= int(_input) <= max_count:
                    return int(_input)
                else:
                    raise ValueError
            elif int(_input) >= min_count:
                return int(_input)
            else:
                raise ValueError
        except ValueError:
            Logger.print_error("Invalid choice. Please select a valid number.")


def get_string_input(question: str, exclude=Optional[List]) -> str:
    while True:
        _input = input(f"{COLOR_CYAN}###### {question}: {RESET_FORMAT}").strip()

        if _input.isalnum() and _input not in exclude:
            return _input

        Logger.print_error("Invalid choice. Please enter a valid value.")
        if _input in exclude:
            Logger.print_error("This value is already in use/reserved.")


def get_selection_input(question: str, option_list: List) -> str:
    while True:
        _input = input(f"{COLOR_CYAN}###### {question}: {RESET_FORMAT}").strip()

        if _input in option_list:
            return _input

        Logger.print_error("Invalid choice. Please enter a valid value.")
