#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
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
from typing import Dict, Any

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
    header = textwrap.dedent(
        f"""
        /=======================================================\\
        |     {COLOR_CYAN}~~~~~~~~~~~~~~~~~ [ KIAUH ] ~~~~~~~~~~~~~~~~~{RESET_FORMAT}     |
        |     {COLOR_CYAN}   Klipper Installation And Update Helper    {RESET_FORMAT}     |
        |     {COLOR_CYAN}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{RESET_FORMAT}     |
        \=======================================================/
        """
    )[1:]
    print(header, end="")


def print_quit_footer():
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        |                        {COLOR_RED}Q) Quit{RESET_FORMAT}                        |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_footer():
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        |                       {COLOR_GREEN}B) « Back{RESET_FORMAT}                       |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_help_footer():
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        |         {COLOR_GREEN}B) « Back{RESET_FORMAT}         |          {COLOR_RED}Q) Quit{RESET_FORMAT}          |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_quit_footer():
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        |         {COLOR_GREEN}B) « Back{RESET_FORMAT}         |        {COLOR_YELLOW}H) Help [?]{RESET_FORMAT}        |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


def print_back_quit_help_footer():
    footer = textwrap.dedent(
        f"""
        |-------------------------------------------------------|
        |     {COLOR_GREEN}B) « Back{RESET_FORMAT}    |    {COLOR_RED}Q) Quit{RESET_FORMAT}    |    {COLOR_YELLOW}H) Help [?]{RESET_FORMAT}     |
        \=======================================================/
        """
    )[1:]
    print(footer, end="")


class BaseMenu(ABC):
    QUIT_FOOTER = "quit"
    BACK_FOOTER = "back"
    BACK_HELP_FOOTER = "back_help"
    BACK_QUIT_FOOTER = "back_quit"
    BACK_QUIT_HELP_FOOTER = "back_quit_help"

    def __init__(
        self, options: Dict[int, Any], options_offset=0, header=True, footer_type="quit"
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
            self.QUIT_FOOTER: print_quit_footer,
            self.BACK_FOOTER: print_back_footer,
            self.BACK_HELP_FOOTER: print_back_help_footer,
            self.BACK_QUIT_FOOTER: print_back_quit_footer,
            self.BACK_QUIT_HELP_FOOTER: print_back_quit_help_footer,
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
                    "back_quit": ["b", "q"],
                    "back_quit_help": ["b", "q", "h"],
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
            option()
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
