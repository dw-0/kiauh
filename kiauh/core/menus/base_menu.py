# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
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
from enum import Enum
from typing import Dict, Type

from core.logger import Logger
from core.menus import FooterType, Option
from core.services.message_service import MessageService
from core.spinner import Spinner
from core.types.color import Color
from utils.input_utils import get_selection_input


def clear() -> None:
    subprocess.call("clear -x", shell=True)


def print_header() -> None:
    line1 = " [ KIAUH ] "
    line2 = "Klipper Installation And Update Helper"
    line3 = ""
    color = Color.CYAN
    count = 62 - len(str(color)) - len(str(Color.RST))
    header = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║ {Color.apply(f"{line1:~^{count}}", color)} ║
        ║ {Color.apply(f"{line2:^{count}}", color)} ║
        ║ {Color.apply(f"{line3:~^{count}}", color)} ║
        ╚═══════════════════════════════════════════════════════╝
        """
    )[1:]
    print(header, end="")


def print_quit_footer() -> None:
    text = "Q) Quit"
    color = Color.RED
    count = 62 - len(str(color)) - len(str(Color.RST))
    footer = textwrap.dedent(
        f"""
        ║ {color}{text:^{count}}{Color.RST} ║
        ╚═══════════════════════════════════════════════════════╝
        """
    )[1:]
    print(footer, end="")


def print_back_footer() -> None:
    text = "B) « Back"
    color = Color.GREEN
    count = 62 - len(str(color)) - len(str(Color.RST))
    footer = textwrap.dedent(
        f"""
        ║ {color}{text:^{count}}{Color.RST} ║
        ╚═══════════════════════════════════════════════════════╝
        """
    )[1:]
    print(footer, end="")


def print_back_help_footer() -> None:
    text1 = "B) « Back"
    text2 = "H) Help [?]"
    color1 = Color.GREEN
    color2 = Color.YELLOW
    count = 34 - len(str(color1)) - len(str(Color.RST))
    footer = textwrap.dedent(
        f"""
        ║ {color1}{text1:^{count}}{Color.RST} │ {color2}{text2:^{count}}{Color.RST} ║
        ╚═══════════════════════════╧═══════════════════════════╝
        """
    )[1:]
    print(footer, end="")


def print_blank_footer() -> None:
    print("╚═══════════════════════════════════════════════════════╝")


class MenuTitleStyle(Enum):
    PLAIN = "plain"
    STYLED = "styled"


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

    loading_msg: str = ""
    spinner: Spinner | None = None

    title: str = ""
    title_style: MenuTitleStyle = MenuTitleStyle.STYLED
    title_color: Color = Color.WHITE

    previous_menu: Type[BaseMenu] | None = None
    help_menu: Type[BaseMenu] | None = None
    footer_type: FooterType = FooterType.BACK

    message_service = MessageService()

    def __init__(self, **kwargs) -> None:
        if type(self) is BaseMenu:
            raise NotImplementedError("BaseMenu cannot be instantiated directly.")

    def __post_init__(self) -> None:
        self.set_previous_menu(self.previous_menu)
        self.set_options()

        # conditionally add options based on footer type
        if self.footer_type is FooterType.QUIT:
            self.options["q"] = Option(method=self.__exit)
        if self.footer_type is FooterType.BACK:
            self.options["b"] = Option(method=self.__go_back)
        if self.footer_type is FooterType.BACK_HELP:
            self.options["b"] = Option(method=self.__go_back)
            self.options["h"] = Option(method=self.__go_to_help)
        # if defined, add the default option to the options dict
        if self.default_option is not None:
            self.options[""] = self.default_option

    def __go_back(self, **kwargs) -> None:
        if self.previous_menu is None:
            return
        self.previous_menu().run()

    def __go_to_help(self, **kwargs) -> None:
        if self.help_menu is None:
            return
        self.help_menu(previous_menu=self.__class__).run()

    def __exit(self, **kwargs) -> None:
        Logger.print_ok("###### Happy printing!", False)
        sys.exit(0)

    @abstractmethod
    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_options(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_menu(self) -> None:
        raise NotImplementedError

    def is_loading(self, state: bool) -> None:
        if not self.spinner and state:
            self.spinner = Spinner(self.loading_msg)
            self.spinner.start()
        else:
            self.spinner.stop()
            self.spinner = None

    def __print_menu_title(self) -> None:
        count = 62 - len(str(self.title_color)) - len(str(Color.RST))
        menu_title = "╔═══════════════════════════════════════════════════════╗\n"
        if self.title:
            title = (
                f" [ {self.title} ] "
                if self.title_style == MenuTitleStyle.STYLED
                else self.title
            )
            line = (
                f"{title:~^{count}}"
                if self.title_style == MenuTitleStyle.STYLED
                else f"{title:^{count}}"
            )
            menu_title += f"║ {Color.apply(line, self.title_color)} ║\n"
        print(menu_title, end="")

    def __print_footer(self) -> None:
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

    def __display_menu(self) -> None:
        self.message_service.display_message()

        if self.header:
            print_header()

        self.__print_menu_title()
        self.print_menu()
        self.__print_footer()

    def run(self) -> None:
        """Start the menu lifecycle. When this function returns, the lifecycle of the menu ends."""
        try:
            self.__display_menu()
            option = get_selection_input(self.input_label_txt, self.options)
            selected_option: Option = self.options.get(option)

            selected_option.method(
                opt_index=selected_option.opt_index,
                opt_data=selected_option.opt_data,
            )

            self.run()

        except Exception as e:
            Logger.print_error(
                f"An unexpected error occured:\n{e}\n{traceback.format_exc()}"
            )
