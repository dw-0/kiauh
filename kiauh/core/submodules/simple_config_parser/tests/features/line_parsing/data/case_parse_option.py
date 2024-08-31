testcases = [
    ("option: value", "option", "value"),
    ("option : value", "option", "value"),
    ("option :value", "option", "value"),
    ("option= value", "option", "value"),
    ("option = value", "option", "value"),
    ("option =value", "option", "value"),
    ("option: value\n", "option", "value"),
    ("option: value # inline comment", "option", "value"),
    ("option: value # inline comment\n", "option", "value"),
    (
        "description: Helper: park toolhead used in PAUSE and CANCEL_PRINT",
        "description",
        "Helper: park toolhead used in PAUSE and CANCEL_PRINT",
    ),
    ("description: homing!", "description", "homing!"),
    ("description: inline macro :-)", "description", "inline macro :-)"),
    ("path: %GCODES_DIR%", "path", "%GCODES_DIR%"),
    (
        "serial = /dev/serial/by-id/<your-mcu-id>",
        "serial",
        "/dev/serial/by-id/<your-mcu-id>",
    ),
]
