# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.i18n import N_, _tr

# global dependencies
GLOBAL_DEPS = ["git", "wget", "curl", "unzip", "dfu-util", "python3-virtualenv"]

# strings
INVALID_CHOICE_MSG = N_("Invalid choice. Please select a valid value.")


def INVALID_CHOICE() -> str:
    return _tr(INVALID_CHOICE_MSG)

# dirs
SYSTEMD = Path("/etc/systemd/system")
NGINX_SITES_AVAILABLE = Path("/etc/nginx/sites-available")
NGINX_SITES_ENABLED = Path("/etc/nginx/sites-enabled")
NGINX_CONFD = Path("/etc/nginx/conf.d")
