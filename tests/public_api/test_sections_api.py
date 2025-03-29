# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import pytest

from src.simple_config_parser.simple_config_parser import (
    DuplicateSectionError,
)


def test_get_sections(parser):
    expected_keys = {
        "section_1",
        "section_2",
        "section_3",
        "section_4",
        "section number 5",
    }
    assert expected_keys.issubset(
        parser.get_sections()
    ), f"Expected keys: {expected_keys}, got: {parser.get_sections()}"


def test_has_section(parser):
    assert parser.has_section("section_1") is True
    assert parser.has_section("not_available") is False


def test_add_section(parser):
    pre_add_count = len(parser.get_sections())
    parser.add_section("new_section")
    parser.add_section("new_section2")
    assert parser.has_section("new_section") is True
    assert parser.has_section("new_section2") is True
    assert len(parser.get_sections()) == pre_add_count + 2

    new_section = parser.config["new_section"]
    assert isinstance(new_section, dict)
    assert new_section["header"] == "[new_section]\n"
    assert new_section["elements"] is not None
    assert new_section["elements"] == []

    new_section2 = parser.config["new_section2"]
    assert isinstance(new_section2, dict)
    assert new_section2["header"] == "[new_section2]\n"
    assert new_section2["elements"] is not None
    assert new_section2["elements"] == []


def test_add_section_duplicate(parser):
    with pytest.raises(DuplicateSectionError):
        parser.add_section("section_1")


def test_remove_section(parser):
    pre_remove_count = len(parser.get_sections())
    parser.remove_section("section_1")
    assert parser.has_section("section_1") is False
    assert len(parser.get_sections()) == pre_remove_count - 1
    assert "section_1" not in parser.config
