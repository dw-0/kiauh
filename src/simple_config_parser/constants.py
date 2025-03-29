# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import re
from enum import Enum

# definition of section line:
#  - then line MUST start with an opening square bracket - it is the first section marker
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
#  - the option name MUST be followed by a colon or an equal sign - it is the separator
#  - the separator MUST NOT be followed by a value
#    - the separator MAY have any amount of leading or trailing whitespaces
#    - the separator MUST NOT be directly followed by a colon or equal sign
#    - the separator MAY be followed by a # or ; - it is the comment marker
#  - the inline comment MAY be of any length and character
OPTIONS_BLOCK_START_RE = re.compile(r"^([^;#:=\s]+)\s*[:=]\s*([#;].*)?$")

# definition of comment line:
#  - the line MAY start with any amount of whitespace characters
#  - the line MUST contain a # or ; - it is the comment marker
#  - the comment marker MAY be followed by any amount of whitespace characters
#  - the comment MAY be of any length and character
LINE_COMMENT_RE = re.compile(r"^\s*[#;].*")

# definition of empty line:
#  - the line MUST contain only whitespace characters
EMPTY_LINE_RE = re.compile(r"^\s*$")

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

HEADER_IDENT = "#_header"

INDENT = " " * 4

class LineType(Enum):
    OPTION = "option"
    OPTION_BLOCK = "option_block"
    COMMENT = "comment"
    BLANK = "blank"
