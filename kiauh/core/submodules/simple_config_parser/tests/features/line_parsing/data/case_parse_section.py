testcases = [
    ("[test_section]", "test_section"),
    ("[test_section two]", "test_section two"),
    ("[section1] # inline comment", "section1"),
    ("[section2] ; second comment", "section2"),
    ("[include moonraker-obico-update.cfg]", "include moonraker-obico-update.cfg"),
    ("[include moonraker_obico_macros.cfg]", "include moonraker_obico_macros.cfg"),
]
