testcases = [
    ("# an arbitrary comment", True),
    ("; another arbitrary comment", True),
    ("  ; indented comment", True),
    ("  # indented comment", True),
    ("not_a: comment", False),
    ("also_not_a= comment", False),
    ("[definitely_not_a_comment]", False),
]
