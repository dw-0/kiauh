testcases = [
    ("[example_section]", True),
    ("[gcode_macro CANCEL_PRINT]", True),
    ("[gcode_macro SET_PAUSE_NEXT_LAYER]", True),
    ("[gcode_macro _TOOLHEAD_PARK_PAUSE_CANCEL]", True),
    ("[update_manager moonraker-obico]", True),
    ("[include moonraker_obico_macros.cfg]", True),
    ("[include moonraker-obico-update.cfg]", True),
    ("[example_section two]", True),
    ("not_a_valid_section", False),
    ("section: invalid", False),
]
