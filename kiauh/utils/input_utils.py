# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import re
from typing import Dict, List

from core.constants import INVALID_CHOICE
from core.logger import Logger
from core.types.color import Color


def get_confirm(question: str, default_choice=True, allow_go_back=False) -> bool | None:
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
    question: str,
    min_value: int,
    max_value: int | None = None,
    default: int | None = None,
    allow_go_back: bool = False,
) -> int | None:
    """
    Helper method to get a number input from the user
    :param question: The question to display
    :param min_value: The lowest allowed value
    :param max_value: The highest allowed value (or None)
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

        if _input == "" and default is not None:
            return default

        try:
            return validate_number_input(_input, min_value, max_value)
        except ValueError:
            Logger.print_error(INVALID_CHOICE)


def get_string_input(
    question: str,
    regex: str | None = None,
    exclude: List[str] | None = None,
    allow_empty: bool = False,
    allow_special_chars: bool = False,
    default: str | None = None,
) -> str:
    """
    Helper method to get a string input from the user
    :param question: The question to display
    :param regex: An optional regex pattern to validate the input against
    :param exclude: List of strings which are not allowed
    :param allow_empty: Whether to allow empty input
    :param allow_special_chars: Wheter to allow special characters in the input
    :param default: Optional default value
    :return: The validated string value
    """
    _exclude = [] if exclude is None else exclude
    _question = format_question(question, default)
    _pattern = re.compile(regex) if regex is not None else None
    while True:
        _input = input(_question)

        if default is not None and _input == "":
            return default
        elif _input == "" and not allow_empty:
            Logger.print_error("Input must not be empty!")
        elif _pattern is not None and _pattern.match(_input):
            return _input
        elif _input.lower() in _exclude:
            Logger.print_error("This value is already in use/reserved.")
        elif allow_special_chars:
            return _input
        elif not allow_special_chars and _input.isalnum():
            return _input
        else:
            Logger.print_error(INVALID_CHOICE)


def get_selection_input(question: str, option_list: List | Dict, default=None) -> str:
    """
    Helper method to get a selection from a list of options from the user
    :param question: The question to display
    :param option_list: The list of options the user can select from
    :param default: Optional default value
    :return: The option that was selected by the user
    """
    while True:
        _input = input(format_question(question, default)).strip().lower()

        if isinstance(option_list, list):
            if _input in option_list:
                return _input
        elif isinstance(option_list, dict):
            if _input in option_list.keys():
                return _input
        else:
            raise ValueError("Invalid option_list type")

        Logger.print_error("Invalid option! Please select a valid option.", False)


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

    return Color.apply(f"###### {formatted_q}: ", Color.CYAN)


def validate_number_input(value: str, min_count: int, max_count: int | None) -> int:
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
