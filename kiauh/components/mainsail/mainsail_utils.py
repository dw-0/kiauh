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
import shutil
from pathlib import Path
from typing import List

import requests

from kiauh.components.klipper.klipper import Klipper
from kiauh.components.mainsail import (
    MAINSAIL_CONFIG_JSON,
    MAINSAIL_DIR,
    MAINSAIL_BACKUP_DIR,
)
from kiauh.core.backup_manager.backup_manager import BackupManager
from kiauh.utils import NGINX_SITES_AVAILABLE, NGINX_CONFD
from kiauh.utils.common import get_install_status_webui
from kiauh.utils.logger import Logger


def get_mainsail_status() -> str:
    return get_install_status_webui(
        MAINSAIL_DIR,
        NGINX_SITES_AVAILABLE.joinpath("mainsail"),
        NGINX_CONFD.joinpath("upstreams.conf"),
        NGINX_CONFD.joinpath("common_vars.conf"),
    )


def backup_config_json(is_temp=False) -> None:
    Logger.print_status(f"Backup '{MAINSAIL_CONFIG_JSON}' ...")
    bm = BackupManager()
    if is_temp:
        fn = Path.home().joinpath("config.json.kiauh.bak")
        bm.backup_file(MAINSAIL_CONFIG_JSON, custom_filename=fn)
    else:
        bm.backup_file(MAINSAIL_CONFIG_JSON)


def restore_config_json() -> None:
    try:
        Logger.print_status(f"Restore '{MAINSAIL_CONFIG_JSON}' ...")
        source = Path.home().joinpath("config.json.kiauh.bak")
        shutil.copy(source, MAINSAIL_CONFIG_JSON)
    except OSError:
        Logger.print_info("Unable to restore config.json. Skipped ...")


def enable_mainsail_remotemode() -> None:
    Logger.print_status("Enable Mainsails remote mode ...")
    with open(MAINSAIL_CONFIG_JSON, "r") as f:
        config_data = json.load(f)

    if config_data["instancesDB"] == "browser":
        Logger.print_info("Remote mode already configured. Skipped ...")
        return

    Logger.print_status("Setting instance storage location to 'browser' ...")
    config_data["instancesDB"] = "browser"

    with open(MAINSAIL_CONFIG_JSON, "w") as f:
        json.dump(config_data, f, indent=4)
    Logger.print_ok("Mainsails remote mode enabled!")


def symlink_webui_nginx_log(klipper_instances: List[Klipper]) -> None:
    Logger.print_status("Link NGINX logs into log directory ...")
    access_log = Path("/var/log/nginx/mainsail-access.log")
    error_log = Path("/var/log/nginx/mainsail-error.log")

    for instance in klipper_instances:
        desti_access = instance.log_dir.joinpath("mainsail-access.log")
        if not desti_access.exists():
            desti_access.symlink_to(access_log)

        desti_error = instance.log_dir.joinpath("mainsail-error.log")
        if not desti_error.exists():
            desti_error.symlink_to(error_log)


def get_mainsail_local_version() -> str:
    relinfo_file = MAINSAIL_DIR.joinpath("release_info.json")
    if not relinfo_file.is_file():
        return "-"

    with open(relinfo_file, "r") as f:
        return json.load(f)["version"]


def get_mainsail_remote_version() -> str:
    url = "https://api.github.com/repos/mainsail-crew/mainsail/tags"
    response = requests.get(url)
    data = json.loads(response.text)
    return data[0]["name"]


def backup_mainsail_data() -> None:
    with open(MAINSAIL_DIR.joinpath(".version"), "r") as v:
        version = v.readlines()[0]
    bm = BackupManager()
    bm.backup_directory(f"mainsail-{version}", MAINSAIL_DIR, MAINSAIL_BACKUP_DIR)
    bm.backup_file(MAINSAIL_CONFIG_JSON, MAINSAIL_BACKUP_DIR)
    bm.backup_file(NGINX_SITES_AVAILABLE.joinpath("mainsail"), MAINSAIL_BACKUP_DIR)
