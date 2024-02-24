#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import json
import urllib.request
from json import JSONDecodeError
from pathlib import Path
from typing import List

from components.fluidd import FLUIDD_DIR, FLUIDD_BACKUP_DIR
from components.klipper.klipper import Klipper
from core.backup_manager.backup_manager import BackupManager
from utils import NGINX_SITES_AVAILABLE, NGINX_CONFD
from utils.common import get_install_status_webui
from utils.logger import Logger


# TODO: could be extracted and made generic
def get_fluidd_status() -> str:
    return get_install_status_webui(
        FLUIDD_DIR,
        NGINX_SITES_AVAILABLE.joinpath("fluidd"),
        NGINX_CONFD.joinpath("upstreams.conf"),
        NGINX_CONFD.joinpath("common_vars.conf"),
    )


# TODO: could be extracted and made generic
def symlink_webui_nginx_log(klipper_instances: List[Klipper]) -> None:
    Logger.print_status("Link NGINX logs into log directory ...")
    access_log = Path("/var/log/nginx/fluidd-access.log")
    error_log = Path("/var/log/nginx/fluidd-error.log")

    for instance in klipper_instances:
        desti_access = instance.log_dir.joinpath("fluidd-access.log")
        if not desti_access.exists():
            desti_access.symlink_to(access_log)

        desti_error = instance.log_dir.joinpath("fluidd-error.log")
        if not desti_error.exists():
            desti_error.symlink_to(error_log)


# TODO: could be extracted and made generic
def get_fluidd_local_version() -> str:
    relinfo_file = FLUIDD_DIR.joinpath("release_info.json")
    if not relinfo_file.is_file():
        return "-"

    with open(relinfo_file, "r") as f:
        return json.load(f)["version"]


# TODO: could be extracted and made generic
def get_fluidd_remote_version() -> str:
    url = "https://api.github.com/repos/fluidd-core/fluidd/tags"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        return data[0]["name"]
    except (JSONDecodeError, TypeError):
        return "ERROR"


# TODO: could be extracted and made generic
def backup_fluidd_data() -> None:
    with open(FLUIDD_DIR.joinpath(".version"), "r") as v:
        version = v.readlines()[0]
    bm = BackupManager()
    bm.backup_directory(f"fluidd-{version}", FLUIDD_DIR, FLUIDD_BACKUP_DIR)
    bm.backup_file(NGINX_SITES_AVAILABLE.joinpath("fluidd"), FLUIDD_BACKUP_DIR)
