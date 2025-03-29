# Simple Config Parser

A custom config parser inspired by Python's configparser module.
Specialized for handling Klipper style config files.

---

### When parsing a config file, it will be split into the following elements:
- Header: All lines before the first section
- Section: A section is defined by a line starting with a `[` and ending with a `]`
- Option: A line starting with a word, followed by a `:` or `=` and a value
- Option Block: A line starting with a word, followed by a `:` or `=` and a newline
- Comment: A line starting with a `#` or `;`
- Blank: A line containing only whitespace characters

---

### Internally, the config is stored as a dictionary of sections, each containing a header and a list of elements:
```python
config = {
    "section_name": {
        "header": "[section_name]\n",
        "elements": [
                {
                    "type": "comment",
                    "content": "# This is a comment\n"
                },
                {
                    "type": "option",
                    "name": "option1",
                    "value": "value1",
                    "raw": "option1: value1\n"
                },
                {
                    "type": "blank",
                    "content": "\n"
                },
                {
                    "type": "option_block",
                    "name": "option2",
                    "value": [
                        "value2",
                        "value3"
                        ],
                    "raw": "option2:"
                }
            ]
        }
    }
```
