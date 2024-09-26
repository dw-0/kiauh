# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import secrets
import string
from pathlib import Path
from typing import Callable, Dict, List

from ..simple_config_parser.constants import (
    BOOLEAN_STATES,
    EMPTY_LINE_RE,
    HEADER_IDENT,
    LINE_COMMENT_RE,
    OPTION_RE,
    OPTIONS_BLOCK_START_RE,
    SECTION_RE,
)

_UNSET = object()


class NoSectionError(Exception):
    """Raised when a section is not defined"""

    def __init__(self, section: str):
        msg = f"Section '{section}' is not defined"
        super().__init__(msg)


class DuplicateSectionError(Exception):
    """Raised when a section is defined more than once"""

    def __init__(self, section: str):
        msg = f"Section '{section}' is defined more than once"
        super().__init__(msg)


class NoOptionError(Exception):
    """Raised when an option is not defined in a section"""

    def __init__(self, option: str, section: str):
        msg = f"Option '{option}' in section '{section}' is not defined"
        super().__init__(msg)


# noinspection PyMethodMayBeStatic
class SimpleConfigParser:
    """A customized config parser targeted at handling Klipper style config files"""

    def __init__(self) -> None:
        self.header: List[str] = []
        self.config: Dict = {}
        self.current_section: str | None = None
        self.current_opt_block: str | None = None
        self.current_collector: str | None = None
        self.in_option_block: bool = False

    def _match_section(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of a section"""
        return SECTION_RE.match(line) is not None

    def _match_option(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of an option"""
        return OPTION_RE.match(line) is not None

    def _match_options_block_start(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of a multiline option"""
        return OPTIONS_BLOCK_START_RE.match(line) is not None

    def _match_line_comment(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of a comment"""
        return LINE_COMMENT_RE.match(line) is not None

    def _match_empty_line(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of an empty line"""
        return EMPTY_LINE_RE.match(line) is not None

    def _parse_line(self, line: str) -> None:
        """Parses a line and determines its type"""
        if self._match_section(line):
            self.current_collector = None
            self.current_opt_block = None
            self.current_section = SECTION_RE.match(line).group(1)
            self.config[self.current_section] = {"_raw": line}

        elif self._match_option(line):
            self.current_collector = None
            self.current_opt_block = None
            option = OPTION_RE.match(line).group(1)
            value = OPTION_RE.match(line).group(2)
            self.config[self.current_section][option] = {"_raw": line, "value": value}

        elif self._match_options_block_start(line):
            self.current_collector = None
            option = OPTIONS_BLOCK_START_RE.match(line).group(1)
            self.current_opt_block = option
            self.config[self.current_section][option] = {"_raw": line, "value": []}

        elif self.current_opt_block is not None:
            self.config[self.current_section][self.current_opt_block]["value"].append(
                line
            )

        elif self._match_empty_line(line) or self._match_line_comment(line):
            self.current_opt_block = None

            # if current_section is None, we are at the beginning of the file,
            # so we consider the part up to the first section as the file header
            if not self.current_section:
                self.config.setdefault(HEADER_IDENT, []).append(line)
            else:
                section = self.config[self.current_section]

                # set the current collector to a new value, so that continuous
                # empty lines or comments are collected into the same collector
                if not self.current_collector:
                    self.current_collector = self._generate_rand_id()
                    section[self.current_collector] = []

                section[self.current_collector].append(line)

    def read_file(self, file: Path) -> None:
        """Read and parse a config file"""
        with open(file, "r") as file:
            for line in file:
                self._parse_line(line)

        # print(json.dumps(self.config, indent=4))

    def write_file(self, file: Path) -> None:
        """Write the current config to the config file"""
        if not file:
            raise ValueError("No config file specified")

        with open(file, "w") as file:
            self._write_header(file)
            self._write_sections(file)

    def _write_header(self, file) -> None:
        """Write the header to the config file"""
        for line in self.config.get(HEADER_IDENT, []):
            file.write(line)

    def _write_sections(self, file) -> None:
        """Write the sections to the config file"""
        for section in self.get_sections():
            for key, value in self.config[section].items():
                self._write_section_content(file, key, value)

    def _write_section_content(self, file, key, value) -> None:
        """Write the content of a section to the config file"""
        if key == "_raw":
            file.write(value)
        elif key.startswith("#_"):
            for line in value:
                file.write(line)
        elif isinstance(value["value"], list):
            file.write(value["_raw"])
            for line in value["value"]:
                file.write(line)
        else:
            file.write(value["_raw"])

    def get_sections(self) -> List[str]:
        """Return a list of all section names, but exclude any section starting with '#_'"""
        return list(
            filter(
                lambda section: not section.startswith("#_"),
                self.config.keys(),
            )
        )

    def has_section(self, section: str) -> bool:
        """Check if a section exists"""
        return section in self.get_sections()

    def add_section(self, section: str) -> None:
        """Add a new section to the config"""
        if section in self.get_sections():
            raise DuplicateSectionError(section)

        if len(self.get_sections()) >= 1:
            self._check_set_section_spacing()

        self.config[section] = {"_raw": f"[{section}]\n"}

    def _check_set_section_spacing(self):
        prev_section_name: str = self.get_sections()[-1]
        prev_section_content: Dict = self.config[prev_section_name]
        last_option_name: str = list(prev_section_content.keys())[-1]

        if last_option_name.startswith("#_"):
            last_elem_value: str = prev_section_content[last_option_name][-1]

            # if the last section is a collector, we first check if the last element
            # in the collector ends with a newline. if it does not, we append a newline.
            # this can happen if the config file does not end with a newline.
            if not last_elem_value.endswith("\n"):
                prev_section_content[last_option_name][-1] = f"{last_elem_value}\n"

            # if the last item in a collector is not a newline, we append a newline, so
            # that the new section is seperated from the options of the previous section
            # by a newline
            if last_elem_value != "\n":
                prev_section_content[last_option_name].append("\n")
        else:
            prev_section_content[self._generate_rand_id()] = ["\n"]

    def remove_section(self, section: str) -> None:
        """Remove a section from the config"""
        self.config.pop(section, None)

    def get_options(self, section: str) -> List[str]:
        """Return a list of all option names for a given section"""
        return list(
            filter(
                lambda option: option != "_raw" and not option.startswith("#_"),
                self.config[section].keys(),
            )
        )

    def has_option(self, section: str, option: str) -> bool:
        """Check if an option exists in a section"""
        return self.has_section(section) and option in self.get_options(section)

    def set_option(self, section: str, option: str, value: str | List[str]) -> None:
        """
        Set the value of an option in a section. If the section does not exist,
        it is created. If the option does not exist, it is created.
        """
        if not self.has_section(section):
            self.add_section(section)

        if not self.has_option(section, option):
            self.config[section][option] = {
                "_raw": f"{option}:\n"
                if isinstance(value, list)
                else f"{option}: {value}\n",
                "value": value,
            }
        else:
            opt = self.config[section][option]
            if not isinstance(value, list):
                opt["_raw"] = opt["_raw"].replace(opt["value"], value)
            opt["value"] = value

    def remove_option(self, section: str, option: str) -> None:
        """Remove an option from a section"""
        self.config[section].pop(option, None)

    def getval(
        self, section: str, option: str, fallback: str | _UNSET = _UNSET
    ) -> str | List[str]:
        """
        Return the value of the given option in the given section

        If the key is not found and 'fallback' is provided, it is used as
        a fallback value.
        """
        try:
            if section not in self.get_sections():
                raise NoSectionError(section)
            if option not in self.get_options(section):
                raise NoOptionError(option, section)
            return self.config[section][option]["value"]
        except (NoSectionError, NoOptionError):
            if fallback is _UNSET:
                raise
            return fallback

    def getint(self, section: str, option: str, fallback: int | _UNSET = _UNSET) -> int:
        """Return the value of the given option in the given section as an int"""
        return self._get_conv(section, option, int, fallback=fallback)

    def getfloat(
        self, section: str, option: str, fallback: float | _UNSET = _UNSET
    ) -> float:
        """Return the value of the given option in the given section as a float"""
        return self._get_conv(section, option, float, fallback=fallback)

    def getboolean(
        self, section: str, option: str, fallback: bool | _UNSET = _UNSET
    ) -> bool:
        """Return the value of the given option in the given section as a boolean"""
        return self._get_conv(
            section, option, self._convert_to_boolean, fallback=fallback
        )

    def _convert_to_boolean(self, value: str) -> bool:
        """Convert a string to a boolean"""
        if isinstance(value, bool):
            return value
        if value.lower() not in BOOLEAN_STATES:
            raise ValueError("Not a boolean: %s" % value)
        return BOOLEAN_STATES[value.lower()]

    def _get_conv(
        self,
        section: str,
        option: str,
        conv: Callable[[str], int | float | bool],
        fallback: _UNSET = _UNSET,
    ) -> int | float | bool:
        """Return the value of the given option in the given section as a converted value"""
        try:
            return conv(self.getval(section, option, fallback))
        except (ValueError, TypeError, AttributeError) as e:
            if fallback is not _UNSET:
                return fallback
            raise ValueError(
                f"Cannot convert {self.getval(section, option)} to {conv.__name__}"
            ) from e

    def _generate_rand_id(self) -> str:
        """Generate a random id with 6 characters"""
        chars = string.ascii_letters + string.digits
        rand_string = "".join(secrets.choice(chars) for _ in range(12))
        return f"#_{rand_string}"
