testcases = [
    ("", True),
    (" ", True),
    ("not empty", False),
    ("  # indented comment", False),
    ("not: empty", False),
    ("also_not= empty", False),
    ("[definitely_not_empty]", False),
]
