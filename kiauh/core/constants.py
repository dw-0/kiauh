# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import pwd
from pathlib import Path

# global dependencies
GLOBAL_DEPS = ["git", "wget", "curl", "unzip", "dfu-util", "python3-virtualenv"]

# strings
INVALID_CHOICE = "Invalid choice. Please select a valid value."

# current user
CURRENT_USER = pwd.getpwuid(os.getuid())[0]


def _resolve_base_dir() -> Path:
    """Resolve the base directory for all component and extension installs.

    Resolution order (first non-empty absolute path wins):
      1. KIAUH_BASE_DIR environment variable
      2. ``base_dir`` option in ``[kiauh]`` section of ``kiauh.cfg``
      3. ``Path.home()`` (default — preserves upstream behaviour)

    The settings file is read directly here (not via KiauhSettings) to
    avoid circular imports — component ``__init__`` modules depend on
    ``BASE_DIR`` and are imported before KiauhSettings is constructed.
    """

    # 1. env var — highest priority
    env = os.environ.get("KIAUH_BASE_DIR", "").strip()
    if env and Path(env).is_absolute():
        return Path(env)

    # 2. settings file — read only the raw value to stay import-safe
    try:
        # PROJECT_ROOT is two levels up from this file (kiauh/core/constants.py)
        project_root = Path(__file__).resolve().parent.parent.parent
        # sanity check that we found the right directory
        if not (project_root / "kiauh.sh").exists():
            raise FileNotFoundError
        cfg_path = project_root / "kiauh.cfg"
        if not cfg_path.exists():
            cfg_path = project_root / "default.kiauh.cfg"
        if cfg_path.exists():
            with open(cfg_path, "r") as fh:
                in_kiauh_section = False
                for line in fh:
                    stripped = line.strip()
                    if stripped.startswith("["):
                        in_kiauh_section = stripped == "[kiauh]"
                        continue
                    if in_kiauh_section and stripped.startswith("base_dir"):
                        # handle both "key: value" and "key = value" formats
                        for sep in (":", "="):
                            if sep in stripped:
                                parts = stripped.split(sep, 1)
                                if len(parts) == 2:
                                    val = parts[1].strip()
                                    if val and Path(val).is_absolute():
                                        return Path(val)
                                break
    except Exception:
        pass  # any I/O or parse error → fall through to default

    # 3. default — identical to upstream behaviour
    return Path.home()


# base directory for all component and extension installations
# Defaults to the current user's home directory. Override with the
# KIAUH_BASE_DIR environment variable **or** the ``base_dir`` option in
# kiauh.cfg to support system-wide installs (e.g. /opt/kiauh, /srv/kiauh).
BASE_DIR: Path = _resolve_base_dir()

# dirs
SYSTEMD = Path("/etc/systemd/system")
NGINX_SITES_AVAILABLE = Path("/etc/nginx/sites-available")
NGINX_SITES_ENABLED = Path("/etc/nginx/sites-enabled")
NGINX_CONFD = Path("/etc/nginx/conf.d")
