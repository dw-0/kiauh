import pytest

from src.simple_config_parser.simple_config_parser import (
    DuplicateOptionError,
    DuplicateSectionError,
    SimpleConfigParser,
)


@pytest.fixture
def parser():
    return SimpleConfigParser()


class TestInternalStateChanges:
    @pytest.mark.parametrize(
        "given", ["dummy_section", "dummy_section 2", "another_section"]
    )
    def test_ensure_section_body_exists(self, parser, given):
        parser._config = {}
        parser.section_name = given
        parser._ensure_section_body_exists()

        assert parser._config[given] is not None
        assert parser._config[given]["body"] == []

    def test_add_option_to_section_body(self):
        pass

    @pytest.mark.parametrize(
        "given", ["dummy_section", "dummy_section 2", "another_section\n"]
    )
    def test_store_internal_state_section(self, parser, given):
        parser._store_internal_state_section(given, given)

        assert parser._all_sections == [given]
        assert parser._config[given]["body"] == []
        assert parser._config[given]["_raw"] == given

    def test_duplicate_section_error(self, parser):
        section_name = "dummy_section"
        parser._all_sections = [section_name]

        with pytest.raises(DuplicateSectionError) as excinfo:
            parser._store_internal_state_section(section_name, section_name)
            message = f"Section '{section_name}' is defined more than once"
            assert message in str(excinfo.value)

        # Check that the internal state of the parser is correct
        assert parser.in_option_block is False
        assert parser.section_name == ""
        assert parser._all_sections == [section_name]

    @pytest.mark.parametrize(
        "given_name, given_value, given_raw_value",
        [("dummyoption", "dummyvalue", "dummyvalue\n")],
    )
    def test_store_internal_state_option(
        self, parser, given_name, given_value, given_raw_value
    ):
        parser.section_name = "dummy_section"
        parser._store_internal_state_option(given_name, given_value, given_raw_value)

        assert parser._all_options[parser.section_name] == {given_name: given_value}

        new_option = {
            "is_multiline": False,
            "option": given_name,
            "value": given_value,
            "_raw": given_raw_value,
        }
        assert parser._config[parser.section_name]["body"] == [new_option]

    def test_duplicate_option_error(self, parser):
        option_name = "dummyoption"
        value = "dummyvalue"
        parser.section_name = "dummy_section"
        parser._all_options = {parser.section_name: {option_name: value}}

        with pytest.raises(DuplicateOptionError) as excinfo:
            parser._store_internal_state_option(option_name, value, value)
            message = f"Option '{option_name}' in section '{parser.section_name}' is defined more than once"
            assert message in str(excinfo.value)
