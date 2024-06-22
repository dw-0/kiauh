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
import traceback
from abc import abstractmethod
from typing import Dict, Optional, Type

from core.menus import FooterType, Option
from utils.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
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
        ╔═══════════════════════════════════════════════════════╗
        ║ {color}{line1:~^{count}}{RESET_FORMAT} ║
        ║ {color}{line2:^{count}}{RESET_FORMAT} ║
        ║ {color}{line3:~^{count}}{RESET_FORMAT} ║
        ╚═══════════════════════════════════════════════════════╝
        """
    )[1:]
    print(header, end="")


def print_quit_footer():
    text = "Q) Quit"
    color = COLOR_RED
    count = 62 - len(color) - len(RESET_FORMAT)
    footer = textwrap.dedent(
        f"""
        ║ {color}{text:^{count}}{RESET_FORMAT} ║
        ╚═══════════════════════════════════════════════════════╝
        """
    )[1:]
    print(footer, end="")


def print_back_footer():
    text = "B) « Back"
    color = COLOR_GREEN
    count = 62 - len(color) - len(RESET_FORMAT)
    footer = textwrap.dedent(
        f"""
        ║ {color}{text:^{count}}{RESET_FORMAT} ║
        ╚═══════════════════════════════════════════════════════╝
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
        ║ {color1}{text1:^{count}}{RESET_FORMAT} │ {color2}{text2:^{count}}{RESET_FORMAT} ║
        ╚═══════════════════════════╧═══════════════════════════╝
        """
    )[1:]
    print(footer, end="")


def print_blank_footer():
    print("╚═══════════════════════════════════════════════════════╝")


class PostInitCaller(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BaseMenu(metaclass=PostInitCaller):
    options: Dict[str, Option] = {}
    options_offset: int = 0
    default_option: Option = None
    input_label_txt: str = "Perform action"
    header: bool = False
    previous_menu: Type[BaseMenu] = None
    help_menu: Type[BaseMenu] = None
    footer_type: FooterType = FooterType.BACK

    def __init__(self, **kwargs):
        if type(self) is BaseMenu:
            raise NotImplementedError("BaseMenu cannot be instantiated directly.")

    def __post_init__(self):
        self.set_previous_menu(self.previous_menu)
        self.set_options()

        # conditionally add options based on footer type
        if self.footer_type is FooterType.QUIT:
            self.options["q"] = Option(method=self.__exit, menu=False)
        if self.footer_type is FooterType.BACK:
            self.options["b"] = Option(method=self.__go_back, menu=False)
        if self.footer_type is FooterType.BACK_HELP:
            self.options["b"] = Option(method=self.__go_back, menu=False)
            self.options["h"] = Option(method=self.__go_to_help, menu=False)
        # if defined, add the default option to the options dict
        if self.default_option is not None:
            self.options[""] = self.default_option

    def __go_back(self, **kwargs):
        self.previous_menu().run()

    def __go_to_help(self, **kwargs):
        self.help_menu(previous_menu=self).run()

    def __exit(self, **kwargs):
        Logger.print_ok("###### Happy printing!", False)
        sys.exit(0)

    @abstractmethod
    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_options(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_menu(self) -> None:
        raise NotImplementedError

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
            raise NotImplementedError("FooterType not correctly implemented!")

    def display_menu(self) -> None:
        if self.header:
            print_header()
        self.print_menu()
        self.print_footer()

    def validate_user_input(self, usr_input: str) -> Option:
        """
        Validate the user input and either return an Option, a string or None
        :param usr_input: The user input in form of a string
        :return: Option, str or None
        """
        usr_input = usr_input.lower()
        option = self.options.get(usr_input, Option(None, False, "", None))

        # if option/usr_input is None/empty string, we execute the menus default option if specified
        if (option is None or usr_input == "") and self.default_option is not None:
            self.default_option.opt_index = usr_input
            return self.default_option

        # user selected a regular option
        option.opt_index = usr_input
        return option

    def handle_user_input(self) -> Option:
        """Handle the user input, return the validated input or print an error."""
        while True:
            print(f"{COLOR_CYAN}###### {self.input_label_txt}: {RESET_FORMAT}", end="")
            usr_input = input().lower()
            validated_input = self.validate_user_input(usr_input)

            if validated_input.method is not None:
                return validated_input
            else:
                Logger.print_error("Invalid input!", False)

    def run(self) -> None:
        """Start the menu lifecycle. When this function returns, the lifecycle of the menu ends."""
        try:
            self.display_menu()
            option = self.handle_user_input()
            option.method(opt_index=option.opt_index, opt_data=option.opt_data)
            self.run()
        except Exception as e:
            Logger.print_error(
                f"An unexpected error occured:\n{e}\n{traceback.format_exc()}"
            )
