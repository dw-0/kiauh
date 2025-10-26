# ======================================================================= #
#  Copyright (C) 2025 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Set, Union

# definition of section line:
#  - the line MUST start with an opening square bracket - it is the first section marker
#  - the section marker MUST be followed by at least one character - it is the section name
#  - the section name MUST be followed by a closing square bracket - it is the second section marker
#  - the second section marker MAY be followed by any amount of whitespace characters
#  - the second section marker MAY be followed by a # or ; - it is the comment marker
#  - the inline comment MAY be of any length and character
SECTION_RE = re.compile(r"^\[(\S.*\S|\S)]\s*([#;].*)?$")

# definition of option line:
#  - the line MUST start with a word - it is the option name
#  - the option name MUST be followed by a colon or an equal sign - it is the separator
#  - the separator MUST be followed by a value
#    - the separator MAY have any amount of leading or trailing whitespaces
#    - the separator MUST NOT be directly followed by a colon or equal sign
#  - the value MAY be of any length and character
#    - the value MAY contain any amount of trailing whitespaces
#    - the value MAY be followed by a # or ; - it is the comment marker
#  - the inline comment MAY be of any length and character
OPTION_RE = re.compile(r"^([^;#:=\s]+)\s?[:=]\s*([^;#:=\s][^;#]*?)\s*([#;].*)?$")

# definition of options block start line:
#  - the line MUST start with a word - it is the option name
#  - the option name MUST NOT be "gcode"
#  - the option name MUST be followed by a colon or an equal sign - it is the separator
#  - the separator MUST NOT be followed by a value
#    - the separator MAY have any amount of leading or trailing whitespaces
#    - the separator MUST NOT be directly followed by a colon or equal sign
#    - the separator MAY be followed by a # or ; - it is the comment marker
#  - the inline comment MAY be of any length and character
OPTIONS_BLOCK_START_RE = re.compile(
    r"^(?!\s*gcode\s*[:=])([^;#:=\s]+)\s*[:=]\s*([#;].*)?$"
)

# definition of gcode block start line:
#  - the line MUST start with the word "gcode"
#  - the word "gcode" MUST be followed by a colon or an equal sign - it is the separator
#  - the separator MUST NOT be followed by a value
#    - the separator MAY have any amount of leading or trailing whitespaces
#    - the separator MUST NOT be directly followed by a colon or equal sign
#    - the separator MAY be followed by a # or ; - it is the comment marker
#  - the inline comment MAY be of any length and character
GCODE_BLOCK_START_RE = re.compile(r"^\s*gcode\s*[:=]\s*(?:[#;].*)?$")

# definition of comment line:
#  - the line MAY start with any amount of whitespace characters
#  - the line MUST contain a # or ; - it is the comment marker
#  - the comment marker MAY be followed by any amount of whitespace characters
#  - the comment MAY be of any length and character
LINE_COMMENT_RE = re.compile(r"^\s*[#;].*")

# definition of empty line:
#  - the line MUST contain only whitespace characters
EMPTY_LINE_RE = re.compile(r"^\s*$")

SAVE_CONFIG_START_RE = re.compile(r"^#\*# <-+ SAVE_CONFIG -+>$")
SAVE_CONFIG_CONTENT_RE = re.compile(r"^#\*#.*$")

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


class LineType(Enum):
    OPTION = "option"
    OPTION_BLOCK = "option_block"
    COMMENT = "comment"
    BLANK = "blank"


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


@dataclass
class Option:
    """Dataclass representing a (pseudo) config option"""

    name: str
    raw: str
    value: str


@dataclass
class MultiLineOption:
    """Dataclass representing a multi-line config option"""

    name: str
    raw: str
    values: List[MLOptionValue] = field(default_factory=list)


@dataclass
class MLOptionValue:
    """Dataclass representing a value in a multi-line option"""

    raw: str
    indent: int
    value: str


@dataclass
class Gcode:
    """Dataclass representing a gcode block"""

    name: str
    raw: str
    gcode: List[str] = field(default_factory=list)


@dataclass
class BlankLine:
    """Dataclass representing a blank line"""

    raw: str = "\n"


@dataclass
class CommentLine:
    """Dataclass representing a comment line"""

    raw: str


SectionItem = Union[Option, MultiLineOption, Gcode, BlankLine, CommentLine]


@dataclass
class Section:
    """Dataclass representing a config section"""

    name: str
    raw: str
    items: List[SectionItem] = field(default_factory=list)


# noinspection PyMethodMayBeStatic
class SimpleConfigParser:
    """A customized config parser targeted at handling Klipper style config files"""

    def __init__(self) -> None:
        self.config: Dict = {}

        self._header: List[str] = []
        self._save_config_block: List[str] = []
        self._config: List[Section] = []
        self._curr_sect: Union[Section, None] = None
        self._curr_ml_opt: Union[MultiLineOption, None] = None
        self._curr_gcode: Union[Gcode, None] = None

    def _match_section(self, line: str) -> bool:
        """Whether the given line matches the definition of a section"""
        return SECTION_RE.match(line) is not None

    def _match_option(self, line: str) -> bool:
        """Whether the given line matches the definition of an option"""
        return OPTION_RE.match(line) is not None

    def _match_options_block_start(self, line: str) -> bool:
        """Whether the given line matches the definition of a multiline option"""
        return OPTIONS_BLOCK_START_RE.match(line) is not None

    def _match_gcode_block_start(self, line: str) -> bool:
        """Whether the given line matches the definition of a gcode block start"""
        return GCODE_BLOCK_START_RE.match(line) is not None

    def _match_save_config_start(self, line: str) -> bool:
        """Whether the given line matches the definition of a save config start"""
        return SAVE_CONFIG_START_RE.match(line) is not None

    def _match_save_config_content(self, line: str) -> bool:
        """Whether the given line matches the definition of a save config content"""
        return SAVE_CONFIG_CONTENT_RE.match(line) is not None

    def _match_line_comment(self, line: str) -> bool:
        """Whether the given line matches the definition of a comment"""
        return LINE_COMMENT_RE.match(line) is not None

    def _match_empty_line(self, line: str) -> bool:
        """Wheter or not the given line matches the definition of an empty line"""
        return EMPTY_LINE_RE.match(line) is not None

    def _parse_line(self, line: str) -> None:
        """Parses a line and determines its type"""
        if self._curr_sect is None and not self._match_section(line):
            # we are at the beginning of the file, so we consider the part
            # up to the first section as the file header and store it separately
            self._header.append(line)
            return

        if self._match_section(line):
            self._reset_special_items()

            sect_name: str = SECTION_RE.match(line).group(1)
            sect = Section(name=sect_name, raw=line)
            self._curr_sect = sect
            self._config.append(sect)
            return

        if self._match_option(line):
            self._reset_special_items()

            name: str = OPTION_RE.match(line).group(1)
            val: str = OPTION_RE.match(line).group(2)
            opt = Option(
                name=name,
                raw=line,
                value=val,
            )
            self._curr_sect.items.append(opt)
            return

        if self._match_options_block_start(line):
            self._reset_special_items()

            name: str = OPTIONS_BLOCK_START_RE.match(line).group(1)
            ml_opt = MultiLineOption(
                name=name,
                raw=line,
            )
            self._curr_ml_opt = ml_opt
            self._curr_sect.items.append(ml_opt)
            return

        if self._curr_ml_opt is not None:
            # we are in an option block, so we consecutively add values
            # to the current multiline option until we hit a different line type

            if "#" in line:
                value = line.split("#", 1)[0].strip()
            elif ";" in line:
                value = line.split(";", 1)[0].strip()
            else:
                value = line.strip()

            ml_value = MLOptionValue(
                raw=line,
                indent=self._get_indent(line),
                value=value,
            )
            self._curr_ml_opt.values.append(ml_value)
            return

        if self._match_gcode_block_start(line):
            self._curr_gcode = Gcode(
                name="gcode",
                raw=line,
            )
            self._curr_sect.items.append(self._curr_gcode)
            return

        if self._curr_gcode is not None:
            # we are in a gcode block, so we add any following line
            # without further checks to the gcode block
            self._curr_gcode.gcode.append(line)
            return

        if self._match_save_config_start(line):
            self._reset_special_items()
            self._save_config_block.append(line)
            return

        if self._match_save_config_content(line):
            self._reset_special_items()
            self._save_config_block.append(line)
            return

        if self._match_empty_line(line):
            self._reset_special_items()
            self._curr_sect.items.append(BlankLine(raw=line))
            return

        if self._match_line_comment(line):
            self._reset_special_items()
            self._curr_sect.items.append(CommentLine(raw=line))
            return

    def _reset_special_items(self) -> None:
        """Reset special items like current multine option and gcode block"""
        self._curr_ml_opt = None
        self._curr_gcode = None

    def _get_indent(self, line: str) -> int:
        """Return the indentation level of a line"""
        return len(line) - len(line.lstrip())

    def read_file(self, file: Path) -> None:
        """Read and parse a config file"""
        self._config = []
        with open(file, "r", encoding="utf-8") as file:
            for line in file:
                self._parse_line(line)

    def write_file(self, path: str | Path) -> None:
        """Write the config to a file"""
        if path is None:
            raise ValueError("File path cannot be None")

        # first write the header
        content: List[str] = list(self._header)

        # then write all sections
        for i in self._config:
            content.append(i.raw)
            for item in i.items:
                content.append(item.raw)
                if isinstance(item, MultiLineOption):
                    content.extend(val.raw for val in item.values)
                elif isinstance(item, Gcode):
                    content.extend(item.gcode)

        # then write the save config block
        content.extend(self._save_config_block)

        # ensure file ends with a newline
        if content and not content[-1].endswith("\n"):
            content.append("\n")

        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(content)

    def get_sections(self) -> Set[str]:
        """Return a set of all section names"""
        return {s.name for s in self._config} if self._config else set()

    def has_section(self, section: str) -> bool:
        """Check if a section exists"""
        return section in self.get_sections()

    def add_section(self, section: str) -> Section:
        """Add a new section to the config"""
        if section in self.get_sections():
            raise DuplicateSectionError(section)

        if not self._config:
            new_sect = Section(name=section, raw=f"[{section}]\n")
            self._config.append(new_sect)
            return new_sect

        last_sect: Section = self._config[-1]
        if not last_sect.items or (
            last_sect.items and not isinstance(last_sect.items[-1], BlankLine)
        ):
            last_sect.items.append(BlankLine())

        new_sect = Section(name=section, raw=f"[{section}]\n")
        self._config.append(new_sect)
        return new_sect

    def remove_section(self, section: str) -> None:
        """Remove a section from the config

        This will remove ALL occurences of sections with the given name.
        """
        self._config = [s for s in self._config if s.name != section]

    def get_options(self, section: str) -> Set[str]:
        """Return a set of all option names for a given section"""
        sections: List[Section] = [s for s in self._config if s.name == section]
        all_items: List[SectionItem] = [
            item for section in sections for item in section.items
        ]

        return {o.name for o in all_items if isinstance(o, (Option, MultiLineOption))}

    def has_option(self, section: str, option: str) -> bool:
        """Check if an option exists in a section"""
        return self.has_section(section) and option in self.get_options(section)

    def set_option(self, section: str, option: str, value: str | List[str]) -> None:
        """
        Set the value of an option in a section. If the section does not exist,
        it is created. If the option does not exist, it is created.
        """

        # when adding options, we add them to the first matching section
        # if the section does not exist, we create it
        section: Section = (
            self.add_section(section)
            if not self.has_section(section)
            else next(s for s in self._config if s.name == section)
        )

        opt = self._find_option_by_name(option, section=section)
        if opt is None:
            if isinstance(value, list):
                indent = 4
                _opt = MultiLineOption(
                    name=option,
                    raw=f"{option}:\n",
                    values=[
                        MLOptionValue(
                            raw=f"{' ' * indent}{val}\n",
                            indent=indent,
                            value=val,
                        )
                        for val in value
                    ],
                )
            else:
                _opt = Option(
                    name=option,
                    raw=f"{option}: {value}\n",
                    value=value,
                )

            last_opt_idx: int = 0
            for idx, item in enumerate(section.items):
                if isinstance(item, (Option, MultiLineOption)):
                    last_opt_idx = idx
            # insert the new option after the last existing option
            section.items.insert(last_opt_idx + 1, _opt)

        elif opt and isinstance(opt, Option) and isinstance(value, str):
            curr_val = opt.value
            new_val = value
            opt.value = value
            opt.raw.replace(curr_val, new_val)

        elif opt and isinstance(opt, MultiLineOption) and isinstance(value, list):
            # note: we completely replace the existing values
            # so any existing indentation, comments, etc. will be lost
            indent = 4
            opt.values = [
                MLOptionValue(
                    raw=f"{' ' * indent}{val}\n",
                    indent=indent,
                    value=val,
                )
                for val in value
            ]

    def _find_section_by_name(
        self, sect_name: str
    ) -> Union[None, Section, List[Section]]:
        """Find a section by name"""
        _sects = [s for s in self._config if s.name == sect_name]
        if len(_sects) > 1:
            return _sects
        elif len(_sects) == 1:
            return _sects[0]
        else:
            return None

    def _find_option_by_name(
        self,
        opt_name: str,
        section: Union[Section, None] = None,
        sections: Union[List[Section], None] = None,
    ) -> Union[None, Option, MultiLineOption]:
        """Find an option or multi-line option by name in a section"""

        # if a single section is provided, search its items for the option
        if section is not None:
            for item in section.items:
                if (
                    isinstance(item, (Option, MultiLineOption))
                    and item.name == opt_name
                ):
                    return item

        # if multiple sections with the same name are provided, merge their
        # items and search for the option
        if sections is not None:
            all_items: List[SectionItem] = [
                item for sect in sections for item in sect.items
            ]
            for item in all_items:
                if (
                    isinstance(item, (Option, MultiLineOption))
                    and item.name == opt_name
                ):
                    return item

        return None

    def remove_option(self, section: str, option: str) -> None:
        """Remove an option from a section

        This will remove the option from ALL occurences of sections with the given name.
        Other non-option items (comments, blank lines, etc.) are preserved.
        """
        sections: List[Section] = [s for s in self._config if s.name == section]
        if not sections:
            return

        for sect in sections:
            sect.items = [
                item
                for item in sect.items
                if not (
                    isinstance(item, (Option, MultiLineOption)) and item.name == option
                )
            ]

    def _get_option(
        self, section: str, option: str
    ) -> Union[Option, MultiLineOption, None]:
        """Internal helper to resolve an option or multi-line option."""
        if section not in self.get_sections():
            raise NoSectionError(section)
        if option not in self.get_options(section):
            raise NoOptionError(option, section)
        sects: List[Section] = [s for s in self._config if s.name == section]
        return (
            self._find_option_by_name(option, sections=sects)
            if len(sects) > 1
            else self._find_option_by_name(option, section=sects[0])
        )

    def getval(self, section: str, option: str, fallback: str | _UNSET = _UNSET) -> str:
        """
        Return the value of the given option in the given section

        If the key is not found and 'fallback' is provided, it is used as
        a fallback value.
        """
        try:
            opt = self._get_option(section, option)
            if not isinstance(opt, Option):
                raise NoOptionError(option, section)

            return opt.value if opt else ""

        except (NoSectionError, NoOptionError):
            if fallback is _UNSET:
                raise
            return fallback

    def getvals(
        self, section: str, option: str, fallback: List[str] | _UNSET = _UNSET
    ) -> List[str]:
        """
        Return the values of the given multi-line option in the given section

        If the key is not found and 'fallback' is provided, it is used as
        a fallback value.
        """
        try:
            opt = self._get_option(section, option)
            if not isinstance(opt, MultiLineOption):
                raise NoOptionError(option, section)

            return [v.value for v in opt.values] if opt else []

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
        fallback: Any = _UNSET,
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
