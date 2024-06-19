import pytest

from src.simple_config_parser.simple_config_parser import (
    DuplicateSectionError,
    NoOptionError,
    NoSectionError,
    SimpleConfigParser,
)


@pytest.fixture
def parser():
    return SimpleConfigParser()


class TestPublicAPI:
    def test_has_section(self, parser):
        parser._all_sections = ["section1"]
        assert parser.has_section("section1") is True

    @pytest.mark.parametrize("section", ["section1", "section2", "section three"])
    def test_add_section(self, parser, section):
        parser.add_section(section)

        assert section in parser._all_sections
        assert parser._all_options[section] == {}

        cfg_section = {"_raw": f"\n[{section}]\n", "body": []}
        assert parser._config[section] == cfg_section

    @pytest.mark.parametrize("section", ["section1", "section2", "section three"])
    def test_add_existing_section(self, parser, section):
        parser._all_sections = [section]

        with pytest.raises(DuplicateSectionError):
            parser.add_section(section)

        assert parser._all_sections == [section]

    @pytest.mark.parametrize("section", ["section1", "section2", "section three"])
    def test_remove_section(self, parser, section):
        parser.add_section(section)
        parser.remove_section(section)

        assert section not in parser._all_sections
        assert section not in parser._all_options
        assert section not in parser._config

    @pytest.mark.parametrize("section", ["section1", "section2", "section three"])
    def test_remove_non_existing_section(self, parser, section):
        with pytest.raises(NoSectionError):
            parser.remove_section(section)

    def test_get_all_sections(self, parser):
        parser.add_section("section1")
        parser.add_section("section2")
        parser.add_section("section three")

        assert parser.sections() == ["section1", "section2", "section three"]

    def test_has_option(self, parser):
        parser.add_section("section1")
        parser.set("section1", "option1", "value1")

        assert parser.has_option("section1", "option1") is True

    @pytest.mark.parametrize(
        "section, option, value",
        [
            ("section1", "option1", "value1"),
            ("section2", "option2", "value2"),
            ("section three", "option3", "value three"),
        ],
    )
    def test_set_new_option(self, parser, section, option, value):
        parser.add_section(section)
        parser.set(section, option, value)

        assert section in parser._all_sections
        assert option in parser._all_options[section]
        assert parser._all_options[section][option] == value

        assert parser._config[section]["body"][0]["is_multiline"] is False
        assert parser._config[section]["body"][0]["option"] == option
        assert parser._config[section]["body"][0]["value"] == value
        assert parser._config[section]["body"][0]["_raw"] == f"{option}: {value}\n"

    def test_set_existing_option(self, parser):
        section, option, value1, value2 = "section1", "option1", "value1", "value2"

        parser.add_section(section)
        parser.set(section, option, value1)
        parser.set(section, option, value2)

        assert parser._all_options[section][option] == value2
        assert parser._config[section]["body"][0]["is_multiline"] is False
        assert parser._config[section]["body"][0]["option"] == option
        assert parser._config[section]["body"][0]["value"] == value2
        assert parser._config[section]["body"][0]["_raw"] == f"{option}: {value2}\n"

    def test_set_new_multiline_option(self, parser):
        section, option, value = "section1", "option1", "value1\nvalue2\nvalue3"

        parser.add_section(section)
        parser.set(section, option, value)

        assert parser._config[section]["body"][0]["is_multiline"] is True
        assert parser._config[section]["body"][0]["option"] == option

        values = ["value1", "value2", "value3"]
        raw_values = ["  value1\n", "  value2\n", "  value3\n"]
        assert parser._config[section]["body"][0]["value"] == values
        assert parser._config[section]["body"][0]["_raw"] == f"{option}:\n"
        assert parser._config[section]["body"][0]["_raw_value"] == raw_values
        assert parser._all_options[section][option] == values

    def test_set_option_of_non_existing_section(self, parser):
        with pytest.raises(NoSectionError):
            parser.set("section1", "option1", "value1")

    def test_remove_option(self, parser):
        section, option, value = "section1", "option1", "value1"

        parser.add_section(section)
        parser.set(section, option, value)
        parser.remove_option(section, option)

        assert option not in parser._all_options[section]
        assert option not in parser._config[section]["body"]

    def test_remove_non_existing_option(self, parser):
        parser.add_section("section1")
        with pytest.raises(NoOptionError):
            parser.remove_option("section1", "option1")

    def test_remove_option_of_non_existing_section(self, parser):
        with pytest.raises(NoSectionError):
            parser.remove_option("section1", "option1")

    def test_get_option(self, parser):
        parser.add_section("section1")
        parser.add_section("section2")
        parser.set("section1", "option1", "value1")
        parser.set("section2", "option2", "value2")
        parser.set("section2", "option3", "value two")

        assert parser.get("section1", "option1") == "value1"
        assert parser.get("section2", "option2") == "value2"
        assert parser.get("section2", "option3") == "value two"

    def test_get_option_of_non_existing_section(self, parser):
        with pytest.raises(NoSectionError):
            parser.get("section1", "option1")

    def test_get_option_of_non_existing_option(self, parser):
        parser.add_section("section1")
        with pytest.raises(NoOptionError):
            parser.get("section1", "option1")

    def test_get_option_fallback(self, parser):
        parser.add_section("section1")
        assert parser.get("section1", "option1", "fallback_value") == "fallback_value"

    def test_get_options(self, parser):
        parser.add_section("section1")
        parser.set("section1", "option1", "value1")
        parser.set("section1", "option2", "value2")
        parser.set("section1", "option3", "value3")

        options = {"option1": "value1", "option2": "value2", "option3": "value3"}
        assert parser.options("section1") == options

    def test_get_option_as_int(self, parser):
        parser.add_section("section1")
        parser.set("section1", "option1", "1")

        option = parser.getint("section1", "option1")
        assert isinstance(option, int) is True

    def test_get_option_as_float(self, parser):
        parser.add_section("section1")
        parser.set("section1", "option1", "1.234")

        option = parser.getfloat("section1", "option1")
        assert isinstance(option, float) is True

    @pytest.mark.parametrize(
        "value",
        ["True", "true", "on", "1", "yes", "False", "false", "off", "0", "no"],
    )
    def test_get_option_as_boolean(self, parser, value):
        parser.add_section("section1")
        parser.set("section1", "option1", value)

        option = parser.getboolean("section1", "option1")
        assert isinstance(option, bool) is True
