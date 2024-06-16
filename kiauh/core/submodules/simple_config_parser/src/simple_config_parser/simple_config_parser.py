# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Match, Tuple, TypedDict

_UNSET = object()


class Section(TypedDict):
    """
    A single section in the config file

    - _raw: The raw representation of the section name
    - options: A list of options in the section
    """

    _raw: str
    options: List[Option]


class Option(TypedDict, total=False):
    """
    A single option in a section in the config file

    - is_multiline: Whether the option is a multiline option
    - option: The name of the option
    - value: The value of the option
    - _raw: The raw representation of the option
    - _raw_value: The raw value of the option

    A multinline option is an option that contains multiple lines of text following
    the option name in the next line. The value of a multiline option is a list of
    strings, where each string represents a single line of text.
    """

    is_multiline: bool
    option: str
    value: str | List[str]
    _raw: str
    _raw_value: str | List[str]


class NoSectionError(Exception):
    """Raised when a section is not defined"""

    def __init__(self, section: str):
        msg = f"Section '{section}' is not defined"
        super().__init__(msg)


class NoOptionError(Exception):
    """Raised when an option is not defined in a section"""

    def __init__(self, option: str, section: str):
        msg = f"Option '{option}' in section '{section}' is not defined"
        super().__init__(msg)


class DuplicateSectionError(Exception):
    """Raised when a section is defined more than once"""

    def __init__(self, section: str):
        msg = f"Section '{section}' is defined more than once"
        super().__init__(msg)


class DuplicateOptionError(Exception):
    """Raised when an option is defined more than once"""

    def __init__(self, option: str, section: str):
        msg = f"Option '{option}' in section '{section}' is defined more than once"
        super().__init__(msg)


# noinspection PyMethodMayBeStatic
class SimpleConfigParser:
    """A customized config parser targeted at handling Klipper style config files"""

    _SECTION_RE = re.compile(r"\s*\[(\w+ ?\w+)]\s*([#;].*)?$")
    _OPTION_RE = re.compile(r"^\s*(\w+)\s*[:=]\s*([^=:].*)\s*([#;].*)?$")
    _MLOPTION_RE = re.compile(r"^\s*(\w+)\s*[:=]\s*([#;].*)?$")
    _COMMENT_RE = re.compile(r"^\s*([#;].*)?$")
    _EMPTY_LINE_RE = re.compile(r"^\s*$")

    BOOLEAN_STATES = {
        "1": True,
        "yes": True,
        "true": True,
        "on": True,
        "0": False,
        "no": False,
        "false": False,
        "off": False,
    }

    def __init__(self):
        self._config: Dict = {}
        self._header: List[str] = []
        self._all_sections: List[str] = []
        self._all_options: Dict = {}
        self.section_name: str = ""
        self.in_option_block: bool = False  # whether we are in a multiline option block

    def read(self, file: Path) -> None:
        """Read the given file and store the result in the internal state"""

        try:
            with open(file, "r") as f:
                self._parse_config(f.readlines())

        except OSError:
            raise

    def write(self, filename):
        """Write the internal state to the given file"""

        content = self._construct_content()

        with open(filename, "w") as f:
            f.write(content)

    def _construct_content(self) -> str:
        """
        Constructs the content of the configuration file based on the internal state of
        the _config object by iterating over the sections and their options. It starts
        by checking if a header is present and extends the content list with its elements.
        Then, for each section, it appends the raw representation of the section to the
        content list. If the section has a body, it iterates over its options and extends
        the content list with their raw representations. If an option is multiline, it
        also extends the content list with its raw value. Finally, the content list is
        joined into a single string and returned.

        :return: The content of the configuration file as a string
        """
        content: List[str] = []
        if self._header is not None:
            content.extend(self._header)
        for section in self._config:
            content.append(self._config[section]["_raw"])

            if (sec_body := self._config[section].get("body")) is not None:
                for option in sec_body:
                    content.extend(option["_raw"])
                    if option["is_multiline"]:
                        content.extend(option["_raw_value"])
        content: str = "".join(content)

        return content

    def sections(self) -> List[str]:
        """Return a list of section names"""

        return self._all_sections

    def add_section(self, section: str) -> None:
        """Add a new section to the internal state"""

        if section in self._all_sections:
            raise DuplicateSectionError(section)
        self._all_sections.append(section)
        self._all_options[section] = {}
        self._config[section] = {"_raw": f"\n[{section}]\n", "body": []}

    def remove_section(self, section: str) -> None:
        """Remove the given section"""

        if section not in self._all_sections:
            raise NoSectionError(section)

        del self._all_sections[self._all_sections.index(section)]
        del self._all_options[section]
        del self._config[section]

    def options(self, section) -> List[str]:
        """Return a list of option names for the given section name"""

        return self._all_options.get(section)

    def get(self, section: str, option: str, fallback: str | _UNSET = _UNSET) -> str:
        """
        Return the value of the given option in the given section

        If the key is not found and 'fallback' is provided, it is used as
        a fallback value.
        """

        try:
            if section not in self._all_sections:
                raise NoSectionError(section)

            if option not in self._all_options.get(section):
                raise NoOptionError(option, section)

            return self._all_options[section][option]
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
        return self._get_conv(section, option, float, fallback=fallback)

    def getboolean(
        self, section: str, option: str, fallback: bool | _UNSET = _UNSET
    ) -> bool:
        return self._get_conv(
            section, option, self._convert_to_boolean, fallback=fallback
        )

    def _convert_to_boolean(self, value) -> bool:
        if value.lower() not in self.BOOLEAN_STATES:
            raise ValueError("Not a boolean: %s" % value)
        return self.BOOLEAN_STATES[value.lower()]

    def _get_conv(
        self,
        section: str,
        option: str,
        conv: Callable[[str], int | float | bool],
        fallback: _UNSET = _UNSET,
    ) -> int | float | bool:
        try:
            return conv(self.get(section, option, fallback))
        except:
            if fallback is not _UNSET:
                return fallback
            raise

    def items(self, section: str) -> List[Tuple[str, str]]:
        """Return a list of (option, value) tuples for a specific section"""

        if section not in self._all_sections:
            raise NoSectionError(section)

        result = []
        for _option in self._all_options[section]:
            result.append((_option, self._all_options[section][_option]))

        return result

    def set(
        self,
        section: str,
        option: str,
        value: str,
        multiline: bool = False,
        indent: int = 2,
    ) -> None:
        """Set the given option to the given value in the given section

        If the option is already defined, it will be overwritten. If the option
        is not defined yet, it will be added to the section body.

        The multiline parameter can be used to specify whether the value is
        multiline or not. If it is not specified, the value will be considered
        as multiline if it contains a newline character. The value will then be split
        into multiple lines. If the value does not contain a newline character, it
        will be considered as a single line value. The indent parameter can be used
        to specify the indentation of the multiline value. Indentations are with spaces.

        :param section: The section to set the option in
        :param option: The option to set
        :param value: The value to set
        :param multiline: Whether the value is multiline or not
        :param indent: The indentation for multiline values
        """

        if section not in self._all_sections:
            raise NoSectionError(section)

        # prepare the options value and raw value depending on the multiline flag
        _raw_value: List[str] | None = None
        if multiline or "\n" in value:
            _multiline = True
            _raw: str = f"{option}:\n"
            _value: List[str] = value.split("\n")
            _raw_value: List[str] = [f"{' ' * indent}{v}\n" for v in _value]
        else:
            _multiline = False
            _raw: str = f"{option}: {value}\n"
            _value: str = value

        # the option does not exist yet
        if option not in self._all_options.get(section):
            _option: Option = {
                "is_multiline": _multiline,
                "option": option,
                "value": _value,
                "_raw": _raw,
            }
            if _raw_value is not None:
                _option["_raw_value"] = _raw_value
            self._config[section]["body"].insert(0, _option)

        # the option exists and we need to update it
        else:
            for _option in self._config[section]["body"]:
                if _option["option"] == option:
                    # we preserve inline comments by replacing the old value with the new one
                    _option["_raw"] = _option["_raw"].replace(_option["value"], _value)
                    _option["value"] = _value
                    if _raw_value is not None:
                        _option["_raw_value"] = _raw_value
                    break

        self._all_options[section][option] = _value

    def remove_option(self, section: str, option: str) -> None:
        """Remove the given option from the given section"""

        if section not in self._all_sections:
            raise NoSectionError(section)

        if option not in self._all_options.get(section):
            raise NoOptionError(option, section)

        for _option in self._config[section]["body"]:
            if _option["option"] == option:
                del self._all_options[section][option]
                self._config[section]["body"].remove(_option)
                break

    def has_section(self, section: str) -> bool:
        """Return True if the given section exists, False otherwise"""
        return section in self._all_sections

    def has_option(self, section: str, option: str) -> bool:
        """Return True if the given option exists in the given section, False otherwise"""
        return option in self._all_options.get(section)

    def _is_section(self, line: str) -> bool:
        """Check if the given line contains a section definition"""
        return self._SECTION_RE.match(line) is not None

    def _is_option(self, line: str) -> bool:
        """Check if the given line contains an option definition"""

        match: Match[str] | None = self._OPTION_RE.match(line)

        if not match:
            return False

        # if there is no value, it's not a regular option but a multiline option
        if match.group(2).strip() == "":
            return False

        if not match.group(1).strip() == "":
            return True

        return False

    def _is_comment(self, line: str) -> bool:
        """Check if the given line is a comment"""
        return self._COMMENT_RE.match(line) is not None

    def _is_empty_line(self, line: str) -> bool:
        """Check if the given line is an empty line"""
        return self._EMPTY_LINE_RE.match(line) is not None

    def _is_multiline_option(self, line: str) -> bool:
        """Check if the given line starts a multiline option block"""

        match: Match[str] | None = self._MLOPTION_RE.match(line)

        if not match:
            return False

        return True

    def _parse_config(self, content: List[str]) -> None:
        """Parse the given content and store the result in the internal state"""

        _curr_multi_opt = ""

        # THE ORDER MATTERS, DO NOT REORDER THE CONDITIONS!
        for line in content:
            if self._is_section(line):
                self._parse_section(line)

            elif self._is_option(line):
                self._parse_option(line)

            # if it's not a regular option with the value inline,
            # it might be a might be a multiline option block
            elif self._is_multiline_option(line):
                self.in_option_block = True
                _curr_multi_opt = self._OPTION_RE.match(line).group(1).strip()
                self._add_option_to_section_body(_curr_multi_opt, "", line)

            elif self.in_option_block:
                self._parse_multiline_option(_curr_multi_opt, line)

            # if it's nothing from above, it's probably a comment or an empty line
            elif self._is_comment(line) or self._is_empty_line(line):
                self._parse_comment(line)

    def _parse_section(self, line: str) -> None:
        """Parse a section line and store the result in the internal state"""

        match: Match[str] | None = self._SECTION_RE.match(line)
        if not match:
            return

        self.in_option_block = False

        section_name: str = match.group(1).strip()
        self._store_internal_state_section(section_name, line)

    def _store_internal_state_section(self, section: str, raw_value: str) -> None:
        """Store the given section and its raw value in the internal state"""

        if section in self._all_sections:
            raise DuplicateSectionError(section)

        self.section_name = section
        self._all_sections.append(section)
        self._config[section]: Section = {"_raw": raw_value, "body": []}

    def _parse_option(self, line: str) -> None:
        """Parse an option line and store the result in the internal state"""

        self.in_option_block = False

        match: Match[str] | None = self._OPTION_RE.match(line)
        if not match:
            return

        option: str = match.group(1).strip()
        value: str = match.group(2).strip()

        if ";" in value:
            i = value.index(";")
            value = value[:i].strip()
        elif "#" in value:
            i = value.index("#")
            value = value[:i].strip()

        self._store_internal_state_option(option, value, line)

    def _store_internal_state_option(
        self, option: str, value: str, raw_value: str
    ) -> None:
        """Store the given option and its raw value in the internal state"""

        section_options = self._all_options.setdefault(self.section_name, {})

        if option in section_options:
            raise DuplicateOptionError(option, self.section_name)

        section_options[option] = value
        self._add_option_to_section_body(option, value, raw_value)

    def _parse_multiline_option(self, curr_ml_opt: str, line: str) -> None:
        """Parse a multiline option line and store the result in the internal state"""

        section_options = self._all_options.setdefault(self.section_name, {})
        multiline_options = section_options.setdefault(curr_ml_opt, [])

        _cleaned_line = line.strip().strip("\n")
        if _cleaned_line and not self._is_comment(line):
            multiline_options.append(_cleaned_line)

        # add the option to the internal multiline option value state
        self._ensure_section_body_exists()
        for _option in self._config[self.section_name]["body"]:
            if _option.get("option") == curr_ml_opt:
                _option.update(
                    is_multiline=True,
                    _raw_value=_option.get("_raw_value", []) + [line],
                    value=multiline_options,
                )

    def _parse_comment(self, line: str) -> None:
        """
        Parse a comment line and store the result in the internal state

        If the there was no previous section parsed, the lines are handled as
        the file header and added to the internal header list as it means, that
        we are at the very top of the file.
        """

        self.in_option_block = False

        if not self.section_name:
            self._header.append(line)
        else:
            self._add_option_to_section_body("", "", line)

    def _ensure_section_body_exists(self) -> None:
        """
        Ensure that the section body exists in the internal state.
        If the section body does not exist, it is created as an empty list
        """
        if self.section_name not in self._config:
            self._config.setdefault(self.section_name, {}).setdefault("body", [])

    def _add_option_to_section_body(
        self, option: str, value: str, line: str, is_multiline: bool = False
    ) -> None:
        """Add a raw option line to the internal state"""

        self._ensure_section_body_exists()

        new_option: Option = {
            "is_multiline": is_multiline,
            "option": option,
            "value": value,
            "_raw": line,
        }

        option_body = self._config[self.section_name]["body"]
        option_body.append(new_option)
