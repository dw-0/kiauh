# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
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

from core.types.color import Color


class DialogType(Enum):
    INFO = ("INFO", Color.WHITE)
    SUCCESS = ("SUCCESS", Color.GREEN)
    ATTENTION = ("ATTENTION", Color.YELLOW)
    WARNING = ("WARNING", Color.YELLOW)
    ERROR = ("ERROR", Color.RED)
    CUSTOM = (None, None)


LINE_WIDTH = 53


class Logger:
    @staticmethod
    def print_info(msg, prefix=True, start="", end="\n") -> None:
        message = f"[INFO] {msg}" if prefix else msg
        Logger.__print(Color.WHITE, start, message, end)

    @staticmethod
    def print_ok(msg: str = "Success!", prefix=True, start="", end="\n") -> None:
        message = f"[OK] {msg}" if prefix else msg
        Logger.__print(Color.GREEN, start, message, end)

    @staticmethod
    def print_warn(msg, prefix=True, start="", end="\n") -> None:
        message = f"[WARN] {msg}" if prefix else msg
        Logger.__print(Color.YELLOW, start, message, end)

    @staticmethod
    def print_error(msg, prefix=True, start="", end="\n") -> None:
        message = f"[ERROR] {msg}" if prefix else msg
        Logger.__print(Color.RED, start, message, end)

    @staticmethod
    def print_status(msg, prefix=True, start="", end="\n") -> None:
        message = f"\n###### {msg}" if prefix else msg
        Logger.__print(Color.MAGENTA, start, message, end)

    @staticmethod
    def __print(color: Color, start: str, message: str, end: str) -> None:
        print(Color.apply(f"{start}{message}", color), end=end)

    @staticmethod
    def print_dialog(
        title: DialogType,
        content: List[str],
        center_content: bool = False,
        custom_title: str | None = None,
        custom_color: Color | None = None,
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
        dialog_title_formatted = Logger._format_dialog_title(dialog_title, dialog_color)
        dialog_content = Logger.format_content(
            content,
            LINE_WIDTH,
            dialog_color,
            center_content,
        )
        top = Logger._format_top_border(dialog_color)
        bottom = Logger._format_bottom_border(dialog_color)

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
        title: DialogType, custom_color: Color | None = None
    ) -> Color:
        if title == DialogType.CUSTOM and custom_color:
            return custom_color

        color: Color = title.value[1] if title.value[1] else Color.WHITE

        return color

    @staticmethod
    def _format_top_border(color: Color) -> str:
        _border = Color.apply(
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n", color
        )
        return _border

    @staticmethod
    def _format_bottom_border(color: Color) -> str:
        _border = Color.apply(
            "\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛", color
        )
        return _border

    @staticmethod
    def _format_dialog_title(title: str | None, color: Color) -> str:
        if title is None:
            return ""

        _title = Color.apply(f"┃ {title:^{LINE_WIDTH}} ┃\n", color)
        _title += Color.apply(
            "┠───────────────────────────────────────────────────────┨\n", color
        )
        return _title

    @staticmethod
    def format_content(
        content: List[str],
        line_width: int,
        color: Color = Color.WHITE,
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
                Color.apply(f"{border_left} {line:<{line_width}} {border_right}", color)
                for line in lines
            ]
        else:
            formatted_lines = [
                Color.apply(f"{border_left} {line:^{line_width}} {border_right}", color)
                for line in lines
            ]

        return "\n".join(formatted_lines)
