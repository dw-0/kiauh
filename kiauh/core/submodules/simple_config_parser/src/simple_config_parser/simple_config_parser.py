# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List

from ..simple_config_parser.constants import (
    BOOLEAN_STATES,
    EMPTY_LINE_RE,
    HEADER_IDENT,
    LINE_COMMENT_RE,
    OPTION_RE,
    OPTIONS_BLOCK_START_RE,
    SECTION_RE, LineType, INDENT,
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

class UnknownLineError(Exception):
    """Raised when a line is not recognized as any known type"""

    def __init__(self, line: str):
        msg = f"Unknown line: '{line}'"
        super().__init__(msg)


# noinspection PyMethodMayBeStatic
class SimpleConfigParser:
    """A customized config parser targeted at handling Klipper style config files"""

    def __init__(self) -> None:
        self.header: List[str] = []
        self.config: Dict = {}
        self.current_section: str | None = None
        self.current_opt_block: str | None = None
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
            self.current_opt_block = None
            self.current_section = SECTION_RE.match(line).group(1)
            self.config[self.current_section] = {
                "header": line,
                "elements": []
            }

        elif self._match_option(line):
            self.current_opt_block = None
            option = OPTION_RE.match(line).group(1)
            value = OPTION_RE.match(line).group(2)
            self.config[self.current_section]["elements"].append({
                "type": LineType.OPTION.value,
                "name": option,
                "value": value,
                "raw": line
            })

        elif self._match_options_block_start(line):
            option = OPTIONS_BLOCK_START_RE.match(line).group(1)
            self.current_opt_block = option
            self.config[self.current_section]["elements"].append({
                "type": LineType.OPTION_BLOCK.value,
                "name": option,
                "value": [],
                "raw": line
            })

        elif self.current_opt_block is not None:
            # we are in an option block, so we add the line to the option's value
            for element in reversed(self.config[self.current_section]["elements"]):
                if element["type"] == LineType.OPTION_BLOCK.value and element["name"] == self.current_opt_block:
                    element["value"].append(line.strip()) # indentation is removed
                    break

        elif self._match_empty_line(line) or self._match_line_comment(line):
            self.current_opt_block = None

            # if current_section is None, we are at the beginning of the file,
            # so we consider the part up to the first section as the file header
            if not self.current_section:
                self.config.setdefault(HEADER_IDENT, []).append(line)
            else:
                element_type = LineType.BLANK.value if self._match_empty_line(line) else LineType.COMMENT.value
                self.config[self.current_section]["elements"].append({
                    "type": element_type,
                    "content": line
                })

    def read_file(self, file: Path) -> None:
        """Read and parse a config file"""
        with open(file, "r") as file:
            for line in file:
                self._parse_line(line)

    def write_file(self, path: str | Path) -> None:
        """Write the config to a file"""
        if path is None:
            raise ValueError("File path cannot be None")

        with open(path, "w", encoding="utf-8") as f:
            if HEADER_IDENT in self.config:
                for line in self.config[HEADER_IDENT]:
                    f.write(line)

            sections = self.get_sections()
            for i, section in enumerate(sections):
                f.write(self.config[section]["header"])

                for element in self.config[section]["elements"]:
                    if element["type"] == LineType.OPTION.value:
                        f.write(element["raw"])
                    elif element["type"] == LineType.OPTION_BLOCK.value:
                        f.write(element["raw"])
                        for line in element["value"]:
                            f.write(INDENT + line.strip() + "\n")
                    elif element["type"] in [LineType.COMMENT.value, LineType.BLANK.value]:
                        f.write(element["content"])
                    else:
                        raise UnknownLineError(element["raw"])

            # Ensure file ends with a single newline
            if sections:  # Only if we have any sections
                last_section = sections[-1]
                last_elements = self.config[last_section]["elements"]

                if last_elements:
                    last_element = last_elements[-1]
                    if "raw" in last_element:
                        last_line = last_element["raw"]
                    else:  # comment or blank line
                        last_line = last_element["content"]

                    if not last_line.endswith("\n"):
                        f.write("\n")

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

        self.config[section] = {
            "header": f"[{section}]\n",
            "elements": []
        }

    def _check_set_section_spacing(self):
        """Check if there is a blank line between the last section and the new section"""
        prev_section_name: str = self.get_sections()[-1]
        prev_section = self.config[prev_section_name]
        prev_elements = prev_section["elements"]

        if prev_elements:
            last_element = prev_elements[-1]

            # If the last element is a comment or blank line
            if last_element["type"] in [LineType.COMMENT.value, LineType.BLANK.value]:
                last_content = last_element["content"]

                # If the last element doesn't end with a newline, add one
                if not last_content.endswith("\n"):
                    last_element["content"] += "\n"

                # If the last element is not a blank line, add a blank line
                if last_content.strip() != "":
                    prev_elements.append({
                        "type": "blank",
                        "content": "\n"
                    })
            else:
                # If the last element is an option, add a blank line
                prev_elements.append({
                    "type": LineType.BLANK.value,
                    "content": "\n"
                })

    def remove_section(self, section: str) -> None:
        """Remove a section from the config"""
        self.config.pop(section, None)

    def get_options(self, section: str) -> List[str]:
        """Return a list of all option names for a given section"""
        options = []
        if self.has_section(section):
            for element in self.config[section]["elements"]:
                if element["type"] in [LineType.OPTION.value, LineType.OPTION_BLOCK.value]:
                    options.append(element["name"])
        return options

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

        # Check if option already exists
        for element in self.config[section]["elements"]:
            if element["type"] in [LineType.OPTION.value, LineType.OPTION_BLOCK.value] and element["name"] == option:
                # Update existing option
                if isinstance(value, list):
                    element["type"] = LineType.OPTION_BLOCK.value
                    element["value"] = value
                    element["raw"] = f"{option}:\n"
                else:
                    element["type"] = LineType.OPTION.value
                    element["value"] = value
                    element["raw"] = f"{option}: {value}\n"
                return

        # Option doesn't exist, create new one
        if isinstance(value, list):
            new_element = {
                "type": LineType.OPTION_BLOCK.value,
                "name": option,
                "value": value,
                "raw": f"{option}:\n"
            }
        else:
            new_element = {
                "type": LineType.OPTION.value,
                "name": option,
                "value": value,
                "raw": f"{option}: {value}\n"
            }

        # scan through elements to find the last option, after which we insert the new option
        insert_pos = 0
        elements = self.config[section]["elements"]
        for i, element in enumerate(elements):
            if element["type"] in [LineType.OPTION.value, LineType.OPTION_BLOCK.value]:
                insert_pos = i + 1

        elements.insert(insert_pos, new_element)

    def remove_option(self, section: str, option: str) -> None:
        """Remove an option from a section"""
        if self.has_section(section):
            elements = self.config[section]["elements"]
            for i, element in enumerate(elements):
                if element["type"] in [LineType.OPTION.value, LineType.OPTION_BLOCK.value] and element["name"] == option:
                    elements.pop(i)
                    break

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

            # Find the option in the elements list
            for element in self.config[section]["elements"]:
                if element["type"] in [LineType.OPTION.value, LineType.OPTION_BLOCK.value] and element["name"] == option:
                    raw_value = element["value"]
                    if isinstance(raw_value, str) and raw_value.endswith("\n"):
                        return raw_value[:-1].strip()
                    elif isinstance(raw_value, list):
                        values: List[str] = []
                        for i, val in enumerate(raw_value):
                            val = val.strip().strip("\n")
                            if len(val) < 1:
                                continue
                            values.append(val.strip())
                        return values
                    return str(raw_value)
            raise NoOptionError(option, section)
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
