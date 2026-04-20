# AGENTS.md - KIAUH Development Guide

## Project Overview

KIAUH (Klipper Installation And Update Helper) is a Python-based installation script for Klipper 3D printer firmware and related components written in Python 3.8+.

## Running KIAUH

```bash
./kiauh.sh
```

**Important:** Must NOT run as root. The script will exit if EUID is 0.

## Development Commands

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Lint (ruff)
ruff check .

# Format
ruff format .

# Typecheck
mypy kiauh

# Run tests
pytest

# Run specific test file
pytest kiauh/core/simple_config_parser/tests/public_api/test_options_api.py
```

## Testing

- New tests should be placed near their corresponding components/modules (e.g., `kiauh/components/klipper/*/test_*.py`)
- Always use a `tests/` subdirectory
- Existing pytest setup in `kiauh/core/simple_config_parser/tests/` serves as reference

## Project Structure

- `kiauh.sh` - Bash entry point, sets PYTHONPATH and calls main.py
- `kiauh/main.py` - Python entry point
- `kiauh/core/` - Core functionality (menus, services, settings, types)
- `kiauh/components/` - Klipper components (klipper, moonraker, webui_client, etc.)
- `kiauh/extensions/` - Extension system for optional addons (obico, octoprint, spoolman, etc.)
- `kiauh/core/simple_config_parser/` - Custom INI-style config parser for Klipper configs
- `kiauh/core/simple_config_parser/src/simple_config_parser/` - Submodule (git subtree)

## Key Quirks

1. **Python version:** Requires Python 3.8+ (checked in kiauh.sh)
2. **Config files:** KIAUH uses `kiauh.cfg` in project root (not .ini format - it's parsed by simple_config_parser)
3. **Submodule:** `kiauh/core/simple_config_parser/` is a git subtree, not a submodule
4. **Branch check:** KIAUH only checks for updates on master branch (not develop)
5. **Target:** Designed to run on Raspberry Pi OS / Debian-based distros

## Code Style

- 4-space indentation
- 88 character line length
- Double quotes
- LF line endings
- Type hints required (mypy checks)
- Ruff with I (isort) enabled
