#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import subprocess
import sys
import textwrap
from abc import abstractmethod, ABC
from typing import Dict, Any, Literal

from kiauh.core.menus import QUIT_FOOTER, BACK_FOOTER, BACK_HELP_FOOTER
from kiauh.utils.constants import (
    COLOR_GREEN,
    COLOR_YELLOW,
    COLOR_RED,
    COLOR_CYAN,
    RESET_FORMAT,
)


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


class BaseMenu(ABC):
    def __init__(
        self,
        options: Dict[int, Any],
        options_offset: int = 0,
        header: bool = True,
        footer_type: Literal[
            "QUIT_FOOTER", "BACK_FOOTER", "BACK_HELP_FOOTER"
        ] = QUIT_FOOTER,
    ):
        self.options = options
        self.options_offset = options_offset
        self.header = header
        self.footer_type = footer_type

    @abstractmethod
    def print_menu(self):
        raise NotImplementedError("Subclasses must implement the print_menu method")

    def print_footer(self):
        footer_type_map = {
            QUIT_FOOTER: print_quit_footer,
            BACK_FOOTER: print_back_footer,
            BACK_HELP_FOOTER: print_back_help_footer,
        }
        footer_function = footer_type_map.get(self.footer_type, print_quit_footer)
        footer_function()

    def display(self):
        # clear()
        if self.header:
            print_header()
        self.print_menu()
        self.print_footer()

    def handle_user_input(self):
        while True:
            choice = input(f"{COLOR_CYAN}###### Perform action: {RESET_FORMAT}")

            error_msg = (
                f"{COLOR_RED}Invalid input.{RESET_FORMAT}"
                if choice.isalpha()
                else f"{COLOR_RED}Invalid input. Select a number between {min(self.options)} and {max(self.options)}.{RESET_FORMAT}"
            )

            if choice.isdigit() and 0 <= int(choice) < len(self.options):
                return choice
            elif choice.isalpha():
                allowed_input = {
                    "quit": ["q"],
                    "back": ["b"],
                    "back_help": ["b", "h"],
                }
                if (
                    self.footer_type in allowed_input
                    and choice.lower() in allowed_input[self.footer_type]
                ):
                    return choice
                else:
                    print(error_msg)
            else:
                print(error_msg)

    def start(self):
        while True:
            self.display()
            choice = self.handle_user_input()

            if choice == "q":
                print(f"{COLOR_GREEN}###### Happy printing!{RESET_FORMAT}")
                sys.exit(0)
            elif choice == "b":
                return
            elif choice == "p":
                print("help!")
            else:
                self.execute_option(int(choice))

    def execute_option(self, choice):
        option = self.options.get(choice, None)

        if isinstance(option, type) and issubclass(option, BaseMenu):
            self.navigate_to_submenu(option)
        elif callable(option):
            option(opt_index=choice)
        elif option is None:
            raise NotImplementedError(f"No implementation for option {choice}")
        else:
            raise TypeError(
                f"Type {type(option)} of option {choice} not of type BaseMenu or Method"
            )

    def navigate_to_submenu(self, submenu_class):
        submenu = submenu_class()
        submenu.previous_menu = self
        submenu.start()
