# ======================================================================= #
#  Copyright (C) 2026 Ahmed Bebars                                        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from core.constants import SYSTEMD

# repo
AE_REPO = "https://github.com/ahmedbebars/klipper-auto-eject.git"

# names
AE_SERVICE_NAME = "klipper-auto-eject.service"

# directories
AE_DIR = Path.home().joinpath("klipper-auto-eject")

# files
AE_INSTALL_SCRIPT = AE_DIR.joinpath("install.sh")
AE_SERVICE_FILE = SYSTEMD.joinpath(AE_SERVICE_NAME)
