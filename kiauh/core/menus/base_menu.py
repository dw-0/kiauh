# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import subprocess
import sys
import textwrap
from abc import abstractmethod, ABC
from typing import Dict, Union, Callable, Type, Tuple

from core.menus import FooterType, NAVI_OPTIONS, ExitAppException, GoBackException
from utils.constants import (
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_CYAN,
    RESET_FORMAT,
)
from utils.logger import Logger


def clear():
    subprocess.call("clear", shell=True)


def print_header():
    line1 = " [ KIAUH ] "
    line2 = "Klipper Installation And Update Helper"
    line3 = ""
    color = COLOR_CYAN
    count = 62 - len(color) - len(RESET_FORMAT)
    header = textwrap.dedent(
        f"""
        /=======================================================\\
        | {color}{line1:~^{count}}{RESET_FORMAT} |
        | {color}{line2:^{count}}{RESET_FORMAT} |
        | {color}{line3:~^{count}}{RESET_FORMAT} |
        \=======================================================/
        """
    )[1:]
    print(header, end="")


def print_quit_footer():
    text = "Q) Quit"
    color = COLOR_RED
    count = 62 - len(color) - len(RESET_FORMAT)
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        | {color}{text:^{count}}{RESET_FORMAT} |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_footer():
    text = "B) « Back"
    color = COLOR_GREEN
    count = 62 - len(color) - len(RESET_FORMAT)
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        | {color}{text:^{count}}{RESET_FORMAT} |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_help_footer():
    text1 = "B) « Back"
    text2 = "H) Help [?]"
    color1 = COLOR_GREEN
    color2 = COLOR_YELLOW
    count = 34 - len(color1) - len(RESET_FORMAT)
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        | {color1}{text1:^{count}}{RESET_FORMAT} | {color2}{text2:^{count}}{RESET_FORMAT} |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_blank_footer():
    print("\=======================================================/")


Options = Dict[str, Callable]


class BaseMenu(ABC):
    options: Options = {}
    options_offset: int = 0
    default_option: Union[Callable, None] = None
    input_label_txt: str = "Perform action"
    header: bool = False
    previous_menu: Union[Type[BaseMenu], BaseMenu] = None
    footer_type: FooterType = FooterType.BACK

    def __init__(self):
        if type(self) is BaseMenu:
            raise NotImplementedError("BaseMenu cannot be instantiated directly.")

    @abstractmethod
    def print_menu(self) -> None:
        raise NotImplementedError("Subclasses must implement the print_menu method")

    def print_footer(self) -> None:
        if self.footer_type is FooterType.QUIT:
            print_quit_footer()
        elif self.footer_type is FooterType.BACK:
            print_back_footer()
        elif self.footer_type is FooterType.BACK_HELP:
            print_back_help_footer()
        elif self.footer_type is FooterType.BLANK:
            print_blank_footer()
        else:
            raise NotImplementedError("Method for printing footer not implemented.")

    def display_menu(self) -> None:
        # clear()
        if self.header:
            print_header()
        self.print_menu()
        self.print_footer()

    def validate_user_input(self, usr_input: str) -> Tuple[Callable, str]:
        """
        Validate the user input and either return an Option, a string or None
        :param usr_input: The user input in form of a string
        :return: Option, str or None
        """
        usr_input = usr_input.lower()
        option = self.options.get(usr_input, None)

        # check if usr_input contains a character used for basic navigation, e.g. b, h or q
        # and if the current menu has the appropriate footer to allow for that action
        is_valid_navigation = self.footer_type in NAVI_OPTIONS
        user_navigated = usr_input in NAVI_OPTIONS[self.footer_type]
        if is_valid_navigation and user_navigated:
            if usr_input == "q":
                raise ExitAppException()
            elif usr_input == "b":
                raise GoBackException()
            elif usr_input == "h":
                return option, usr_input

        # if usr_input is None or an empty string, we execute the menues default option if specified
        if usr_input == "" and self.default_option is not None:
            return self.default_option, usr_input

        # user selected a regular option
        return option, usr_input

    def handle_user_input(self) -> Tuple[Callable, str]:
        """Handle the user input, return the validated input or print an error."""
        while True:
            print(f"{COLOR_CYAN}###### {self.input_label_txt}: {RESET_FORMAT}", end="")
            usr_input = input().lower()

            if (validated_input := self.validate_user_input(usr_input)) is not None:
                return validated_input
            else:
                Logger.print_error("Invalid input!", False)

    def run(self) -> None:
        """Start the menu lifecycle. When this function returns, the lifecycle of the menu ends."""
        while True:
            try:
                self.display_menu()
                option = self.handle_user_input()
                option[0](opt_index=option[1])
            except GoBackException:
                return
            except ExitAppException:
                Logger.print_ok("###### Happy printing!", False)
                sys.exit(0)
