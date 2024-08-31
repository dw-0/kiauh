# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from enum import Enum
from typing import List

from core.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_MAGENTA,
    COLOR_RED,
    COLOR_WHITE,
    COLOR_YELLOW,
    RESET_FORMAT,
)


class DialogType(Enum):
    INFO = ("INFO", COLOR_WHITE)
    SUCCESS = ("SUCCESS", COLOR_GREEN)
    ATTENTION = ("ATTENTION", COLOR_YELLOW)
    WARNING = ("WARNING", COLOR_YELLOW)
    ERROR = ("ERROR", COLOR_RED)
    CUSTOM = (None, None)


class DialogCustomColor(Enum):
    WHITE = COLOR_WHITE
    GREEN = COLOR_GREEN
    YELLOW = COLOR_YELLOW
    RED = COLOR_RED
    CYAN = COLOR_CYAN
    MAGENTA = COLOR_MAGENTA


LINE_WIDTH = 53


class Logger:
    @staticmethod
    def info(msg) -> None:
        # log to kiauh.log
        pass

    @staticmethod
    def warn(msg) -> None:
        # log to kiauh.log
        pass

    @staticmethod
    def error(msg) -> None:
        # log to kiauh.log
        pass

    @staticmethod
    def print_info(msg, prefix=True, start="", end="\n") -> None:
        message = f"[INFO] {msg}" if prefix else msg
        print(f"{COLOR_WHITE}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_ok(msg: str = "Success!", prefix=True, start="", end="\n") -> None:
        message = f"[OK] {msg}" if prefix else msg
        print(f"{COLOR_GREEN}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_warn(msg, prefix=True, start="", end="\n") -> None:
        message = f"[WARN] {msg}" if prefix else msg
        print(f"{COLOR_YELLOW}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_error(msg, prefix=True, start="", end="\n") -> None:
        message = f"[ERROR] {msg}" if prefix else msg
        print(f"{COLOR_RED}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_status(msg, prefix=True, start="", end="\n") -> None:
        message = f"\n###### {msg}" if prefix else msg
        print(f"{COLOR_MAGENTA}{start}{message}{RESET_FORMAT}", end=end)

    @staticmethod
    def print_dialog(
        title: DialogType,
        content: List[str],
        center_content: bool = False,
        custom_title: str | None = None,
        custom_color: DialogCustomColor | None = None,
        margin_top: int = 0,
        margin_bottom: int = 0,
    ) -> None:
        """
        Prints a dialog with the given title and content.
        Those dialogs should be used to display verbose messages to the user which
        require simple interaction like confirmation or input. Do not use this for
        navigating through the application.

        :param title: The type of the dialog.
        :param content: The content of the dialog.
        :param center_content: Whether to center the content or not.
        :param custom_title: A custom title for the dialog.
        :param custom_color: A custom color for the dialog.
        :param margin_top: The number of empty lines to print before the dialog.
        :param margin_bottom: The number of empty lines to print after the dialog.
        """
        dialog_color = Logger._get_dialog_color(title, custom_color)
        dialog_title = Logger._get_dialog_title(title, custom_title)
        dialog_title_formatted = Logger._format_dialog_title(dialog_title)
        dialog_content = Logger.format_content(content, LINE_WIDTH, center_content)
        top = Logger._format_top_border(dialog_color)
        bottom = Logger._format_bottom_border()

        print("\n" * margin_top)
        print(
            f"{top}{dialog_title_formatted}{dialog_content}{bottom}",
            end="",
        )
        print("\n" * margin_bottom)

    @staticmethod
    def _get_dialog_title(
        title: DialogType, custom_title: str | None = None
    ) -> str | None:
        if title == DialogType.CUSTOM and custom_title:
            return f"[ {custom_title} ]"
        return f"[ {title.value[0]} ]" if title.value[0] else None

    @staticmethod
    def _get_dialog_color(
        title: DialogType, custom_color: DialogCustomColor | None = None
    ) -> str:
        if title == DialogType.CUSTOM and custom_color:
            return str(custom_color.value)

        color: str = title.value[1] if title.value[1] else DialogCustomColor.WHITE.value

        return color

    @staticmethod
    def _format_top_border(color: str) -> str:
        return f"{color}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"

    @staticmethod
    def _format_bottom_border() -> str:
        return (
            f"\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET_FORMAT}"
        )

    @staticmethod
    def _format_dialog_title(title: str | None) -> str:
        if title is not None:
            return textwrap.dedent(f"""
                ┃ {title:^{LINE_WIDTH}} ┃
                ┠───────────────────────────────────────────────────────┨
                """)
        else:
            return "\n"

    @staticmethod
    def format_content(
        content: List[str],
        line_width: int,
        center_content: bool = False,
        border_left: str = "┃",
        border_right: str = "┃",
    ) -> str:
        wrapper = textwrap.TextWrapper(line_width)

        lines = []
        for i, c in enumerate(content):
            paragraph = wrapper.wrap(c)
            lines.extend(paragraph)

            # add a full blank line if we have a double newline
            # character unless we are at the end of the list
            if c == "\n\n" and i < len(content) - 1:
                lines.append(" " * line_width)

        if not center_content:
            formatted_lines = [
                f"{border_left} {line:<{line_width}} {border_right}" for line in lines
            ]
        else:
            formatted_lines = [
                f"{border_left} {line:^{line_width}} {border_right}" for line in lines
            ]

        return "\n".join(formatted_lines)
