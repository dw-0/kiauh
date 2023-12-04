#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import Optional, List, Union

from kiauh.utils import INVALID_CHOICE
from kiauh.utils.constants import COLOR_CYAN, RESET_FORMAT
from kiauh.utils.logger import Logger


def get_confirm(
    question: str, default_choice=True, allow_go_back=False
) -> Union[bool, None]:
    """
    Helper method for validating confirmation (yes/no) user input. |
    :param question: The question to display
    :param default_choice: A default if input was submitted without input
    :param allow_go_back: Navigate back to a previous dialog
    :return: Either True or False, or None on go_back
    """
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
            input(format_question(question + f" {def_choice}", None)).strip().lower()
        )

        if choice in options_confirm:
            return True
        elif choice in options_decline:
            return False
        elif allow_go_back and choice in options_go_back:
            return None
        else:
            Logger.print_error(INVALID_CHOICE)


def get_number_input(
    question: str, min_count: int, max_count=None, default=None, allow_go_back=False
) -> Union[int, None]:
    """
    Helper method to get a number input from the user
    :param question: The question to display
    :param min_count: The lowest allowed value
    :param max_count: The highest allowed value (or None)
    :param default: Optional default value
    :param allow_go_back: Navigate back to a previous dialog
    :return: Either the validated number input, or None on go_back
    """
    options_go_back = ["b", "B"]
    _question = format_question(question, default)
    while True:
        _input = input(_question)
        if allow_go_back and _input in options_go_back:
            return None

        if _input == "":
            return default

        try:
            return validate_number_input(_input, min_count, max_count)
        except ValueError:
            Logger.print_error(INVALID_CHOICE)


def get_string_input(question: str, exclude=Optional[List], default=None) -> str:
    """
    Helper method to get a string input from the user
    :param question: The question to display
    :param exclude: List of strings which are not allowed
    :param default: Optional default value
    :return: The validated string value
    """
    while True:
        _input = input(format_question(question, default)).strip()

        if _input.isalnum() and _input.lower() not in exclude:
            return _input

        Logger.print_error(INVALID_CHOICE)
        if _input in exclude:
            Logger.print_error("This value is already in use/reserved.")


def get_selection_input(question: str, option_list: List, default=None) -> str:
    """
    Helper method to get a selection from a list of options from the user
    :param question: The question to display
    :param option_list: The list of options the user can select from
    :param default: Optional default value
    :return: The option that was selected by the user
    """
    while True:
        _input = input(format_question(question, default)).strip()

        if _input in option_list:
            return _input

        Logger.print_error(INVALID_CHOICE)


def format_question(question: str, default=None) -> str:
    """
    Helper method to have a standardized formatting of questions |
    :param question: The question to display
    :param default: If defined, the default option will be displayed to the user
    :return: The formatted question string
    """
    formatted_q = question
    if default is not None:
        formatted_q += f" (default={default})"

    return f"{COLOR_CYAN}###### {formatted_q}: {RESET_FORMAT}"


def validate_number_input(value: str, min_count: int, max_count: int) -> int:
    """
    Helper method for a simple number input validation. |
    :param value: The value to validate
    :param min_count: The lowest allowed value
    :param max_count: The highest allowed value (or None)
    :return: The validated value as Integer
    :raises: ValueError if value is invalid
    """
    if max_count is not None:
        if min_count <= int(value) <= max_count:
            return int(value)
    elif int(value) >= min_count:
        return int(value)

    raise ValueError
