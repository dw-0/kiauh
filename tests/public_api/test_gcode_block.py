from pathlib import Path

from src.simple_config_parser.simple_config_parser import Gcode, SimpleConfigParser

ASSETS = Path(__file__).parent.parent / "assets"
GCODE_FILE = ASSETS / "test_gcode.cfg"


def test_gcode_block_parsing():
    parser = SimpleConfigParser()
    parser.read_file(GCODE_FILE)

    assert "gcode_macro test" in parser.get_sections()
    sect = [s for s in parser._config if s.name == "gcode_macro test"][0]
    gcode_items = [i for i in sect.items if isinstance(i, Gcode)]
    assert gcode_items, "No Gcode block found in section"

    gc = gcode_items[0]
    assert gc.raw.strip().startswith("gcode:")
    assert any("G28" in ln for ln in gc.gcode)
    assert any("M118" in ln for ln in gc.gcode)
    assert all(ln.startswith("    ") or ln == "\n" for ln in gc.gcode if ln.strip())

    tmp_out = GCODE_FILE.parent / "tmp_gcode_roundtrip.cfg"
    parser.write_file(tmp_out)
    assert tmp_out.read_text(encoding="utf-8") == GCODE_FILE.read_text(encoding="utf-8")
    tmp_out.unlink()
