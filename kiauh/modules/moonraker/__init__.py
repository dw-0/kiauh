#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
from pathlib import Path

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))

MOONRAKER_DIR = f"{Path.home()}/moonraker"
MOONRAKER_ENV_DIR = f"{Path.home()}/moonraker-env"
MOONRAKER_REQUIREMENTS_TXT = f"{MOONRAKER_DIR}/scripts/moonraker-requirements.txt"
DEFAULT_MOONRAKER_REPO_URL = "https://github.com/Arksine/moonraker"
DEFAULT_MOONRAKER_PORT = 7125

# introduced due to
# https://github.com/Arksine/moonraker/issues/349
# https://github.com/Arksine/moonraker/pull/346
POLKIT_LEGACY_FILE = "/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla"
POLKIT_FILE = "/etc/polkit-1/rules.d/moonraker.rules"
POLKIT_USR_FILE = "/usr/share/polkit-1/rules.d/moonraker.rules"
POLKIT_SCRIPT = f"{Path.home()}/moonraker/scripts/set-policykit-rules.sh"

EXIT_MOONRAKER_SETUP = "Exiting Moonraker setup ..."
