# Simple Config Parser

A custom config parser inspired by Python's configparser module.
Specialized for handling Klipper style config files.

---

### When parsing a config file, it will be split into the following elements:
- Header: All lines before the first section
- Section: A section is defined by a line starting with a `[` and ending with a `]`
- Option: A line starting with a word, followed by a `:` or `=` and a value
- Option Block: A line starting with a word, followed by a `:` or `=` and a newline
  - The word `gcode` is excluded from being treated as an option block
- Gcode Block: A line starting with the word `gcode`, followed by a `:` or `=` and a newline
  - All indented lines following the gcode line are considered part of the gcode block
- Comment: A line starting with a `#` or `;`
- Blank: A line containing only whitespace characters
- SaveConfig Block: Klippers auto-generated SAVE_CONFIG section that can be found at the very end of the config file

