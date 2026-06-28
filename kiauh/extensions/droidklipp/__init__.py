# ======================================================================= #
#  Copyright (C) 2026 Cody Dixon                                         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path

# repo
DROIDKLIPP_REPO = "https://github.com/CodeMasterCody3D/DroidKlipp"
DROIDKLIPP_APK_URL = "https://github.com/CodeMasterCody3D/DroidKlipp-Android-APK/releases/latest/download/DroidKlipp.apk"

# directories
DROIDKLIPP_DIR = Path.home().joinpath("DroidKlipp")

# files
DROIDKLIPP_INSTALL_SCRIPT = DROIDKLIPP_DIR.joinpath("install_droidklipp.sh")
DROIDKLIPP_UNINSTALL_SCRIPT = DROIDKLIPP_DIR.joinpath("uninstall_droidklipp.sh")
DROIDKLIPP_MONITOR_FILE = DROIDKLIPP_DIR.joinpath("droidklipp_monitor.py")
DROIDKLIPP_DEPLOYED_MONITOR = Path.home().joinpath("droidklipp_monitor.py")

# service
DROIDKLIPP_SERVICE_NAME = "adb_monitor"

# packages
DROIDKLIPP_REQUIRED_PACKAGES = {"adb", "tmux", "x11-utils"}
