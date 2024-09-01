import pytest
from data.case_parse_comment import testcases as case_parse_comment
from data.case_parse_option import testcases as case_parse_option
from data.case_parse_section import testcases as case_parse_section

from src.simple_config_parser.simple_config_parser import (
    Option,
    SimpleConfigParser,
)


@pytest.fixture
def parser():
    return SimpleConfigParser()


class TestSingleLineParsing:
    @pytest.mark.parametrize("given, expected", [*case_parse_section])
    def test_parse_section(self, parser, given, expected):
        parser._parse_section(given)

        # Check that the internal state of the parser is correct
        assert parser.section_name == expected
        assert parser.in_option_block is False
        assert parser._all_sections == [expected]
        assert parser._config[expected]["_raw"] == given
        assert parser._config[expected]["body"] == []

    @pytest.mark.parametrize(
        "given, expected_option, expected_value", [*case_parse_option]
    )
    def test_parse_option(self, parser, given, expected_option, expected_value):
        section_name = "test_section"
        parser.section_name = section_name
        parser._parse_option(given)

        # Check that the internal state of the parser is correct
        assert parser.section_name == section_name
        assert parser.in_option_block is False
        assert parser._all_options[section_name][expected_option] == expected_value

        section_option = parser._config[section_name]["body"][0]
        assert section_option["option"] == expected_option
        assert section_option["value"] == expected_value
        assert section_option["_raw"] == given

    @pytest.mark.parametrize(
        "option, next_line",
        [("gcode", "next line"), ("gcode", "    {{% some jinja template %}}")],
    )
    def test_parse_multiline_option(self, parser, option, next_line):
        parser.section_name = "dummy_section"
        parser.in_option_block = True
        parser._add_option_to_section_body(option, "", option)
        parser._parse_multiline_option(option, next_line)
        cleaned_next_line = next_line.strip().strip("\n")

        assert parser._all_options[parser.section_name] is not None
        assert parser._all_options[parser.section_name][option] == [cleaned_next_line]

        expected_option: Option = {
            "is_multiline": True,
            "option": option,
            "value": [cleaned_next_line],
            "_raw": option,
            "_raw_value": [next_line],
        }
        assert parser._config[parser.section_name]["body"] == [expected_option]

    @pytest.mark.parametrize("given", [*case_parse_comment])
    def test_parse_comment(self, parser, given):
        parser.section_name = "dummy_section"
        parser._parse_comment(given)

        # internal state checks after parsing
        assert parser.in_option_block is False

        expected_option = {
            "is_multiline": False,
            "_raw": given,
            "option": "",
            "value": "",
        }
        assert parser._config[parser.section_name]["body"] == [expected_option]

    @pytest.mark.parametrize("given", ["# header line", "; another header line"])
    def test_parse_header_comment(self, parser, given):
        parser.section_name = ""
        parser._parse_comment(given)

        assert parser.in_option_block is False
        assert parser._header == [given]
