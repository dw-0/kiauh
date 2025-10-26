# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path
from typing import List

import pytest

from src.simple_config_parser.simple_config_parser import (
    BlankLine,
    CommentLine,
    MLOptionValue,
    MultiLineOption,
    Option,
    Section,
    SimpleConfigParser,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEST_CFG = ASSETS_DIR / "test_config_1.cfg"


@pytest.fixture()
def parser() -> SimpleConfigParser:
    p = SimpleConfigParser()
    p.read_file(TEST_CFG)
    return p


# ----------------------------- Helper utils ----------------------------- #


def _get_section(p: SimpleConfigParser, name: str) -> Section:
    sect = [s for s in p._config if s.name == name]
    assert sect, f"Section '{name}' not found"
    return sect[0]


def _get_option(sect: Section, name: str):
    for item in sect.items:
        if isinstance(item, (Option, MultiLineOption)) and item.name == name:
            return item
    return None


# ------------------------------ Basic parsing --------------------------- #


def test_header_lines_preserved(parser: SimpleConfigParser):
    # Lines before first section become header; ensure we captured them
    assert parser._header, "Header should not be empty"
    # The first section name should not appear inside header lines
    assert all("[section_1]" not in ln for ln in parser._header)
    # Ensure comments retained verbatim
    assert any("a comment at the very top" in ln for ln in parser._header)


def test_section_names(parser: SimpleConfigParser):
    expected = {"section_1", "section_2", "section_3", "section_4", "section number 5"}
    assert parser.get_sections() == expected


def test_section_raw_line(parser: SimpleConfigParser):
    s2 = _get_section(parser, "section_2")
    assert s2.raw.startswith("[section_2]")
    assert "; comment" in s2.raw


def test_single_line_option_parsing(parser: SimpleConfigParser):
    s1 = _get_section(parser, "section_1")
    opt = _get_option(s1, "option_1")
    assert isinstance(opt, Option)
    assert opt.name == "option_1"
    assert opt.value == "value_1"
    assert opt.raw.strip() == "option_1: value_1"


def test_other_single_line_option_values(parser: SimpleConfigParser):
    s1 = _get_section(parser, "section_1")
    bool_opt = _get_option(s1, "option_1_1")
    int_opt = _get_option(s1, "option_1_2")
    float_opt = _get_option(s1, "option_1_3")
    assert isinstance(bool_opt, Option) and bool_opt.value == "True"
    assert isinstance(int_opt, Option) and int_opt.value.startswith("5")
    assert isinstance(float_opt, Option) and float_opt.value.startswith("1.123")


def test_comment_and_blank_lines_preserved(parser: SimpleConfigParser):
    s4 = _get_section(parser, "section_4")
    # Expect first item is a comment line, followed by an option
    assert any(isinstance(i, CommentLine) for i in s4.items), "Comment line missing"
    # Ensure at least one blank line exists in some section
    assert any(isinstance(i, BlankLine) for s in parser._config for i in s.items), (
        "No blank lines parsed"
    )


def test_multiline_option_parsing(parser: SimpleConfigParser):
    s5 = _get_section(parser, "section number 5")
    ml = _get_option(s5, "multi_option")
    assert isinstance(ml, MultiLineOption), "multi_option should be a MultiLineOption"
    # Raw line ends with ':'
    assert ml.raw.strip().startswith("multi_option:")
    values: List[MLOptionValue] = ml.values
    # Ensure values captured (includes comment lines inside block)
    assert len(values) >= 4
    trimmed_values = [v.value for v in values]
    # Comments are stripped from value field; original raw retains them
    assert trimmed_values[0] == "" or "multi-line" not in trimmed_values[0], (
        "First value should be empty or comment stripped"
    )
    assert "value_5_1" in trimmed_values
    assert any("value_5_2" == v for v in trimmed_values)
    assert any("value_5_3" == v for v in trimmed_values)
    # Indentation should be consistent (4 spaces in test data)
    assert all(v.indent == 4 for v in values), "Indentation should be 4 spaces"


def test_option_after_multiline_block(parser: SimpleConfigParser):
    s5 = _get_section(parser, "section number 5")
    opt = _get_option(s5, "option_5_1")
    assert isinstance(opt, Option)
    assert opt.value == "value_5_1"


def test_getval_and_conversions(parser: SimpleConfigParser):
    assert parser.getval("section_1", "option_1") == "value_1"
    assert parser.getboolean("section_1", "option_1_1") is True
    assert parser.getint("section_1", "option_1_2") == 5
    assert abs(parser.getfloat("section_1", "option_1_3") - 1.123) < 1e-9


def test_getval_fallback(parser: SimpleConfigParser):
    assert parser.getval("missing_section", "missing", fallback="fb") == "fb"
    assert parser.getint("missing_section", "missing", fallback=42) == 42


def test_getvals_on_multiline_option(parser: SimpleConfigParser):
    vals = parser.getvals("section number 5", "multi_option")
    # Should not include inline comments, should capture cleaned values
    assert any(v == "value_5_2" for v in vals)


def test_round_trip_write(tmp_path: Path, parser: SimpleConfigParser):
    out_file = tmp_path / "round_trip.cfg"
    parser.write_file(out_file)
    original = TEST_CFG.read_text(encoding="utf-8")
    written = out_file.read_text(encoding="utf-8")
    # Files should match exactly (parser aims for perfect reproduction)
    assert original == written, "Round-trip file content mismatch"


def test_set_option_adds_and_updates(parser: SimpleConfigParser):
    # Add new option
    parser.set_option("section_3", "new_opt", "some_value")
    s3 = _get_section(parser, "section_3")
    new_opt = _get_option(s3, "new_opt")
    assert isinstance(new_opt, Option) and new_opt.value == "some_value"
    # Update existing option value
    parser.set_option("section_3", "new_opt", "other")
    new_opt_after = _get_option(s3, "new_opt")
    assert new_opt_after.value == "other"


def test_set_option_multiline(parser: SimpleConfigParser):
    parser.set_option("section_2", "multi_new", ["a", "b", "c"])
    s2 = _get_section(parser, "section_2")
    ml = _get_option(s2, "multi_new")
    assert isinstance(ml, MultiLineOption)
    assert [v.value for v in ml.values] == ["a", "b", "c"]


def test_remove_section(parser: SimpleConfigParser):
    parser.remove_section("section_4")
    assert "section_4" not in parser.get_sections()


def test_remove_option(parser: SimpleConfigParser):
    parser.remove_option("section_1", "option_1")
    s1 = _get_section(parser, "section_1")
    assert _get_option(s1, "option_1") is None


def test_multiline_option_comment_stripping(parser: SimpleConfigParser):
    # Ensure inline comments removed from value attribute but remain in raw
    s5 = _get_section(parser, "section number 5")
    ml = _get_option(s5, "multi_option")
    assert isinstance(ml, MultiLineOption)
    raw_with_comment = [v.raw for v in ml.values if "; here is a comment" in v.raw]
    assert raw_with_comment, "Expected raw line with inline comment"
    # Corresponding cleaned value should not contain the comment part
    cleaned_match = [v.value for v in ml.values if v.value == "value_5_2"]
    assert cleaned_match, "Expected cleaned value 'value_5_2' without comment"


def test_blank_lines_between_sections(parser: SimpleConfigParser):
    # Ensure at least one blank line exists before section_2 (from original file structure)
    idx_section_1 = [i for i, s in enumerate(parser._config) if s.name == "section_1"][
        0
    ]
    idx_section_2 = [i for i, s in enumerate(parser._config) if s.name == "section_2"][
        0
    ]
    # Collect lines after section_1 items end until next section raw
    assert idx_section_2 == idx_section_1 + 1, "Sections not consecutive as expected"
    # Validate section_2 has a preceding blank line inside previous section or header logic
    s1 = _get_section(parser, "section_1")
    assert any(isinstance(i, BlankLine) for i in s1.items), (
        "Expected blank line at end of section_1"
    )


def test_write_preserves_trailing_newline(tmp_path: Path, parser: SimpleConfigParser):
    out_file = tmp_path / "ensure_newline.cfg"
    parser.write_file(out_file)
    content = out_file.read_bytes()
    assert content.endswith(b"\n"), "Written file must end with newline"
