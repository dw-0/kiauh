# ======================================================================= #
#  Copyright (C) 2026 umeiko                                               #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

KLIPPERSCREEN_ESP_REPO = "https://github.com/umeiko/KlipperScreen-esp"
KLIPPERSCREEN_ESP_RELEASE_BASE = (
    "https://github.com/umeiko/KlipperScreen-esp/releases/latest/download"
)
KLIPPERSCREEN_ESP_UNINSTALL_SCRIPT = (
    "https://raw.githubusercontent.com/umeiko/KlipperScreen-esp/main/"
    "scripts/linux/uninstall.sh"
)
KLIPPERSCREEN_ESP_MIRRORS = ("https://ghproxy.net/", "https://gh-proxy.com/")
KLIPPERSCREEN_ESP_SERVICE_NAME = "KlipperScreen-esp.service"
KLIPPERSCREEN_ESP_BACKEND_DROP_IN = (
    "/etc/systemd/system/KlipperScreen-esp.service.d/backend.conf"
)
KLIPPERSCREEN_ESP_PACKAGE_ARCHES = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "aarch64": "arm64",
    "arm64": "arm64",
    "armv7l": "armhf",
    "armv6l": "armhf",
    "armhf": "armhf",
}
KLIPPERSCREEN_ESP_INSTALL_DIR = Path.home().joinpath(
    ".local", "share", "KlipperScreen-esp"
)
