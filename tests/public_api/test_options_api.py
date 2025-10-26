# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import pytest

from src.simple_config_parser.simple_config_parser import (
    MultiLineOption,
    NoOptionError,
    NoSectionError,
    SimpleConfigParser,
)


def test_get_options(parser: SimpleConfigParser):
    expected_options = {
        "section_1": {"option_1", "option_1_1", "option_1_2", "option_1_3"},
        "section_2": {"option_2"},
        "section_3": {"option_3"},
        "section_4": {"option_4"},
        "section number 5": {"option_5", "multi_option", "option_5_1"},
    }
    for sect, opts in expected_options.items():
        assert opts.issubset(parser.get_options(sect))


def test_has_option(parser):
    assert parser.has_option("section_1", "option_1") is True
    assert parser.has_option("section_1", "option_128") is False
    assert parser.has_option("section_128", "option_1") is False


def test_getval(parser):
    assert parser.getval("section_1", "option_1") == "value_1"
    assert parser.getval("section_3", "option_3") == "value_3"
    assert parser.getval("section_4", "option_4") == "value_4"
    assert parser.getval("section number 5", "option_5") == "this.is.value-5"
    assert parser.getval("section number 5", "option_5_1") == "value_5_1"
    assert parser.getval("section_2", "option_2") == "value_2"


def test_getvals_multiline(parser):
    vals = parser.getvals("section number 5", "multi_option")
    assert isinstance(vals, list) and len(vals) >= 3
    assert "value_5_2" in vals


def test_getval_fallback(parser):
    assert parser.getval("section_1", "option_128", fallback="fallback") == "fallback"
    with pytest.raises(NoOptionError):
        parser.getval("section_1", "option_128")


def test_getval_exceptions(parser):
    with pytest.raises(NoSectionError):
        parser.getval("section_128", "option_1")
    with pytest.raises(NoOptionError):
        parser.getval("section_1", "option_128")


def test_type_conversions(parser):
    assert parser.getint("section_1", "option_1_2") == 5
    assert pytest.approx(parser.getfloat("section_1", "option_1_3"), rel=1e-9) == 1.123
    assert parser.getboolean("section_1", "option_1_1") is True


def test_type_conversion_errors(parser):
    with pytest.raises(ValueError):
        parser.getint("section_1", "option_1")
    with pytest.raises(ValueError):
        parser.getboolean("section_1", "option_1")
    with pytest.raises(ValueError):
        parser.getfloat("section_1", "option_1")


def test_type_conversion_fallbacks(parser):
    assert parser.getint("section_1", "missing", fallback=99) == 99
    assert parser.getfloat("section_1", "missing", fallback=3.14) == 3.14
    assert parser.getboolean("section_1", "missing", fallback=False) is False


def test_set_option_creates_and_updates(parser):
    parser.set_option("section_1", "new_option", "nv")
    assert parser.getval("section_1", "new_option") == "nv"
    parser.set_option("section_1", "new_option", "nv2")
    assert parser.getval("section_1", "new_option") == "nv2"


def test_set_multiline_option(parser):
    parser.set_option("section_2", "array_option", ["value_1", "value_2", "value_3"])
    vals = parser.getvals("section_2", "array_option")
    assert vals == ["value_1", "value_2", "value_3"]
    # Prüfe Typ
    sect = [s for s in parser._config if s.name == "section_2"][0]
    ml = [
        i
        for i in sect.items
        if isinstance(i, MultiLineOption) and i.name == "array_option"
    ][0]
    assert isinstance(ml, MultiLineOption)
    assert ml.raw == "array_option:\n"


def test_remove_option(parser):
    parser.remove_option("section_1", "option_1")
    assert not parser.has_option("section_1", "option_1")
