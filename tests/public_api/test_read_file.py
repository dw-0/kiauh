# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

from src.simple_config_parser.simple_config_parser import Section, SimpleConfigParser

BASE_DIR = Path(__file__).parent.parent / "assets"
TEST_DATA_PATH = BASE_DIR / "test_config_1.cfg"


def test_read_file_sections_and_header():
    parser = SimpleConfigParser()
    parser.read_file(TEST_DATA_PATH)

    # Header erhalten
    assert parser._header, "Header darf nicht leer sein"
    assert any("a comment at the very top" in ln for ln in parser._header)

    # Sektionen korrekt eingelesen
    expected = {"section_1", "section_2", "section_3", "section_4", "section number 5"}
    assert parser.get_sections() == expected

    # Reihenfolge bleibt erhalten
    assert [s.name for s in parser._config] == [
        "section_1",
        "section_2",
        "section_3",
        "section_4",
        "section number 5",
    ]

    # Jede Section ist ein Section-Dataclass
    assert all(isinstance(s, Section) for s in parser._config)
