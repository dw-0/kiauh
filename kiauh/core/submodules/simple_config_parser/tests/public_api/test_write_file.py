# ======================================================================= #
#  Copyright (C) 2024 Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  https://github.com/dw-0/simple-config-parser                           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

import pytest

from src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)

BASE_DIR = Path(__file__).parent.parent.joinpath("assets")
TEST_DATA_PATH = BASE_DIR.joinpath("test_config_1.cfg")
# TEST_DATA_PATH_2 = BASE_DIR.joinpath("test_config_1_write.cfg")


def test_write_file_exception():
    parser = SimpleConfigParser()
    with pytest.raises(ValueError):
        parser.write_file(None)  # noqa


def test_write_to_file(tmp_path):
    tmp_file = Path(tmp_path).joinpath("tmp_config.cfg")
    parser1 = SimpleConfigParser()
    parser1.read_file(TEST_DATA_PATH)
    # parser1.write_file(TEST_DATA_PATH_2)
    parser1.write_file(tmp_file)

    parser2 = SimpleConfigParser()
    parser2.read_file(tmp_file)

    assert tmp_file.exists()
    assert parser2.config is not None

    with open(TEST_DATA_PATH, "r") as original, open(tmp_file, "r") as written:
        assert original.read() == written.read()

def test_remove_option_and_write(tmp_path):
    # Setup paths
    test_dir = BASE_DIR.joinpath("write_tests/remove_option")
    input_file = test_dir.joinpath("input.cfg")
    expected_file = test_dir.joinpath("expected.cfg")
    output_file = Path(tmp_path).joinpath("output.cfg")

    # Read input file and remove option
    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.remove_option("section_1", "option_to_remove")

    # Write modified config
    parser.write_file(output_file)
    # parser.write_file(test_dir.joinpath("output.cfg"))

    # Compare with expected output
    with open(expected_file, "r") as expected, open(output_file, "r") as actual:
        assert expected.read() == actual.read()

    # Additional verification
    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert not parser2.has_option("section_1", "option_to_remove")

def test_remove_section_and_write(tmp_path):
    # Setup paths
    test_dir = BASE_DIR.joinpath("write_tests/remove_section")
    input_file = test_dir.joinpath("input.cfg")
    expected_file = test_dir.joinpath("expected.cfg")
    output_file = Path(tmp_path).joinpath("output.cfg")

    # Read input file and remove section
    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.remove_section("section_to_remove")

    # Write modified config
    parser.write_file(output_file)
    # parser.write_file(test_dir.joinpath("output.cfg"))

    # Compare with expected output
    with open(expected_file, "r") as expected, open(output_file, "r") as actual:
        assert expected.read() == actual.read()

    # Additional verification
    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert not parser2.has_section("section_to_remove")
    assert "section_1" in parser2.get_sections()
    assert "section_2" in parser2.get_sections()

def test_add_option_and_write(tmp_path):
    # Setup paths
    test_dir = BASE_DIR.joinpath("write_tests/add_option")
    input_file = test_dir.joinpath("input.cfg")
    expected_file = test_dir.joinpath("expected.cfg")
    output_file = Path(tmp_path).joinpath("output.cfg")

    # Read input file and add option
    parser = SimpleConfigParser()
    parser.read_file(input_file)
    parser.set_option("section_1", "new_option", "new_value")

    # Write modified config
    parser.write_file(output_file)
    # parser.write_file(test_dir.joinpath("output.cfg"))

    # Compare with expected output
    with open(expected_file, "r") as expected, open(output_file, "r") as actual:
        assert expected.read() == actual.read()

    # Additional verification
    parser2 = SimpleConfigParser()
    parser2.read_file(output_file)
    assert parser2.has_option("section_1", "new_option")
    assert parser2.getval("section_1", "new_option") == "new_value"
