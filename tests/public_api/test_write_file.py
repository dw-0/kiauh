# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

from src.simple_config_parser.simple_config_parser import SimpleConfigParser

BASE_DIR = Path(__file__).parent.parent / "assets"
TEST_DATA_PATH = BASE_DIR / "test_config_1.cfg"


def test_write_file_exception():
    parser = SimpleConfigParser()
    with pytest.raises(ValueError):
        parser.write_file(None)  # noqa: intentionally invalid


def test_write_to_file(tmp_path):
    tmp_file = Path(tmp_path) / "tmp_config.cfg"
    parser1 = SimpleConfigParser()
    parser1.read_file(TEST_DATA_PATH)
    parser1.write_file(tmp_file)

    parser2 = SimpleConfigParser()
    parser2.read_file(tmp_file)

    assert tmp_file.exists()
    # gleiche Sections & Round-Trip identisch
    assert parser2.get_sections() == parser1.get_sections()
    assert tmp_file.read_text(encoding="utf-8") == TEST_DATA_PATH.read_text(
        encoding="utf-8"
    )


def test_remove_option_and_write(tmp_path):
    test_dir = BASE_DIR / "write_tests" / "remove_option"
    input_file = test_dir / "input.cfg"
    expected_file = test_dir / "expected.cfg"
    output_file = Path(tmp_path) / "output.cfg"

    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.remove_option("section_1", "option_to_remove")
    parser.write_file(output_file)

    assert output_file.read_text(encoding="utf-8") == expected_file.read_text(
        encoding="utf-8"
    )

    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert not parser2.has_option("section_1", "option_to_remove")


def test_remove_section_and_write(tmp_path):
    test_dir = BASE_DIR / "write_tests" / "remove_section"
    input_file = test_dir / "input.cfg"
    expected_file = test_dir / "expected.cfg"
    output_file = Path(tmp_path) / "output.cfg"

    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.remove_section("section_to_remove")
    parser.write_file(output_file)

    assert output_file.read_text(encoding="utf-8") == expected_file.read_text(
        encoding="utf-8"
    )

    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert not parser2.has_section("section_to_remove")
    assert {"section_1", "section_2"}.issubset(parser2.get_sections())


def test_add_option_and_write(tmp_path):
    test_dir = BASE_DIR / "write_tests" / "add_option"
    input_file = test_dir / "input.cfg"
    expected_file = test_dir / "expected.cfg"
    output_file = Path(tmp_path) / "output.cfg"

    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.set_option("section_1", "new_option", "new_value")
    parser.write_file(output_file)

    assert output_file.read_text(encoding="utf-8") == expected_file.read_text(
        encoding="utf-8"
    )

    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert parser2.has_option("section_1", "new_option")
    assert parser2.getval("section_1", "new_option") == "new_value"
