import pytest
from data.case_line_is_comment import testcases as case_line_is_comment
from data.case_line_is_empty import testcases as case_line_is_empty
from data.case_line_is_multiline_option import (
    testcases as case_line_is_multiline_option,
)
from data.case_line_is_option import testcases as case_line_is_option
from data.case_line_is_section import testcases as case_line_is_section

from src.simple_config_parser.simple_config_parser import SimpleConfigParser


@pytest.fixture
def parser():
    return SimpleConfigParser()


class TestLineTypeDetection:
    @pytest.mark.parametrize("given, expected", [*case_line_is_section])
    def test_line_is_section(self, parser, given, expected):
        assert parser._is_section(given) is expected

    @pytest.mark.parametrize("given, expected", [*case_line_is_option])
    def test_line_is_option(self, parser, given, expected):
        assert parser._is_option(given) is expected

    @pytest.mark.parametrize("given, expected", [*case_line_is_multiline_option])
    def test_line_is_multiline_option(self, parser, given, expected):
        assert parser._is_multiline_option(given) is expected

    @pytest.mark.parametrize("given, expected", [*case_line_is_comment])
    def test_line_is_comment(self, parser, given, expected):
        assert parser._is_comment(given) is expected

    @pytest.mark.parametrize("given, expected", [*case_line_is_empty])
    def test_line_is_empty(self, parser, given, expected):
        assert parser._is_empty_line(given) is expected
