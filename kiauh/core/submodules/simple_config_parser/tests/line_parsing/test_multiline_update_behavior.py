# ======================================================================= #
#  Tests: Verhalten beim Aktualisieren von Multiline-Optionen            #
# ======================================================================= #
from pathlib import Path

from src.simple_config_parser.simple_config_parser import (
    BlankLine,
    MultiLineOption,
    SimpleConfigParser,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEST_CFG = ASSETS_DIR / "test_config_1.cfg"


def test_update_existing_multiline_option_replaces_values_and_drops_comments(tmp_path):
    parser = SimpleConfigParser()
    parser.read_file(TEST_CFG)

    assert parser.getvals("section number 5", "multi_option")
    orig_values = parser.getvals("section number 5", "multi_option")
    assert "value_5_2" in orig_values

    new_values = ["alpha", "beta", "gamma"]
    parser.set_option("section number 5", "multi_option", new_values)

    updated = parser.getvals("section number 5", "multi_option")
    assert updated == new_values

    sect = [s for s in parser._config if s.name == "section number 5"][0]
    ml = [
        i
        for i in sect.items
        if isinstance(i, MultiLineOption) and i.name == "multi_option"
    ][0]
    assert all("value_5_2" not in v.value for v in ml.values)
    # Nach komplettem Replace keine alten Inline-Kommentare mehr
    assert all("; here is a comment" not in v.raw for v in ml.values)

    out_file = tmp_path / "updated_multiline.cfg"
    parser.write_file(out_file)
    assert out_file.read_text(encoding="utf-8").endswith("\n")


def test_add_section_inserts_blank_line_if_needed():
    parser = SimpleConfigParser()
    parser.read_file(TEST_CFG)

    last_before = parser._config[-1]
    had_blank_before = bool(last_before.items) and isinstance(
        last_before.items[-1], BlankLine
    )

    parser.add_section("new_last_section")
    assert parser.has_section("new_last_section")

    # Vorherige letzte Section wurde ggf. um eine BlankLine erweitert
    prev_last = [s for s in parser._config if s.name == last_before.name][0]
    if not had_blank_before:
        assert isinstance(prev_last.items[-2], BlankLine) or isinstance(
            prev_last.items[-1], BlankLine
        )
    else:
        # Falls bereits BlankLine vorhanden war, bleibt sie bestehen
        assert isinstance(prev_last.items[-1], BlankLine)
