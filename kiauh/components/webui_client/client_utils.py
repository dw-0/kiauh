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
from json import JSONDecodeError
from pathlib import Path
from typing import List, Optional, Dict, Literal, Union, get_args

import urllib.request

from components.klipper.klipper import Klipper
from components.webui_client import (
    MAINSAIL_CONFIG_JSON,
    MAINSAIL_DIR,
    MAINSAIL_BACKUP_DIR,
    FLUIDD_PRE_RLS_URL,
    FLUIDD_BACKUP_DIR,
    FLUIDD_URL,
    FLUIDD_DIR,
    ClientData,
    FLUIDD_CONFIG_REPO_URL,
    FLUIDD_CONFIG_DIR,
    ClientConfigData,
    MAINSAIL_PRE_RLS_URL,
    MAINSAIL_URL,
    MAINSAIL_CONFIG_REPO_URL,
    MAINSAIL_CONFIG_DIR,
    ClientName,
    MAINSAIL_TAGS_URL,
    FLUIDD_TAGS_URL,
    FLUIDD_CONFIG_BACKUP_DIR,
    MAINSAIL_CONFIG_BACKUP_DIR,
)
from core.backup_manager.backup_manager import BackupManager
from core.repo_manager.repo_manager import RepoManager
from utils import NGINX_SITES_AVAILABLE, NGINX_CONFD
from utils.common import get_install_status_webui
from utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_YELLOW
from utils.logger import Logger


def load_client_data(client_name: ClientName) -> Optional[ClientData]:
    client_data = None

    if client_name == "mainsail":
        client_config_data = ClientConfigData(
            name="mainsail-config",
            display_name="Mainsail-Config",
            cfg_filename="mainsail.cfg",
            dir=MAINSAIL_CONFIG_DIR,
            backup_dir=MAINSAIL_CONFIG_BACKUP_DIR,
            url=MAINSAIL_CONFIG_REPO_URL,
            printer_cfg_section="include mainsail.cfg",
            mr_conf_path="~/mainsail-config",
            mr_conf_origin=MAINSAIL_CONFIG_REPO_URL,
        )
        client_data = ClientData(
            name=client_name,
            display_name=client_name.capitalize(),
            dir=MAINSAIL_DIR,
            backup_dir=MAINSAIL_BACKUP_DIR,
            url=MAINSAIL_URL,
            pre_release_url=MAINSAIL_PRE_RLS_URL,
            tags_url=MAINSAIL_TAGS_URL,
            remote_mode=True,
            mr_conf_repo="mainsail-crew/mainsail",
            mr_conf_path="~/mainsail",
            client_config=client_config_data,
        )
    elif client_name == "fluidd":
        client_config_data = ClientConfigData(
            name="fluidd-config",
            display_name="Fluidd-Config",
            cfg_filename="fluidd.cfg",
            dir=FLUIDD_CONFIG_DIR,
            backup_dir=FLUIDD_CONFIG_BACKUP_DIR,
            url=FLUIDD_CONFIG_REPO_URL,
            printer_cfg_section="include fluidd.cfg",
            mr_conf_path="~/fluidd-config",
            mr_conf_origin=FLUIDD_CONFIG_REPO_URL,
        )
        client_data = ClientData(
            name=client_name,
            display_name=client_name.capitalize(),
            dir=FLUIDD_DIR,
            backup_dir=FLUIDD_BACKUP_DIR,
            url=FLUIDD_URL,
            pre_release_url=FLUIDD_PRE_RLS_URL,
            tags_url=FLUIDD_TAGS_URL,
            remote_mode=False,
            mr_conf_repo="fluidd-core/fluidd",
            mr_conf_path="~/fluidd",
            client_config=client_config_data,
        )

    return client_data


def get_client_status(client: ClientData) -> str:
    return get_install_status_webui(
        client.get("dir"),
        NGINX_SITES_AVAILABLE.joinpath(client.get("name")),
        NGINX_CONFD.joinpath("upstreams.conf"),
        NGINX_CONFD.joinpath("common_vars.conf"),
    )


def get_client_config_status(
    client: ClientData,
) -> Dict[
    Literal["repo", "local", "remote"],
    Union[str, int],
]:
    client_config = client.get("client_config")
    client_config = client_config.get("dir")

    return {
        "repo": RepoManager.get_repo_name(client_config),
        "local": RepoManager.get_local_commit(client_config),
        "remote": RepoManager.get_remote_commit(client_config),
    }


def get_current_client_config(clients: List[ClientData]) -> str:
    installed = []
    for client in clients:
        client_config = client.get("client_config")
        if client_config.get("dir").exists():
            installed.append(client)

    if len(installed) > 1:
        return f"{COLOR_YELLOW}Conflict!{RESET_FORMAT}"
    elif len(installed) == 1:
        cfg = installed[0].get("client_config")
        return f"{COLOR_CYAN}{cfg.get('display_name')}{RESET_FORMAT}"

    return f"{COLOR_CYAN}-{RESET_FORMAT}"


def backup_mainsail_config_json(is_temp=False) -> None:
    Logger.print_status(f"Backup '{MAINSAIL_CONFIG_JSON}' ...")
    bm = BackupManager()
    if is_temp:
        fn = Path.home().joinpath("config.json.kiauh.bak")
        bm.backup_file(MAINSAIL_CONFIG_JSON, custom_filename=fn)
    else:
        bm.backup_file(MAINSAIL_CONFIG_JSON)


def restore_mainsail_config_json() -> None:
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


def get_local_client_version(client: ClientData) -> str:
    relinfo_file = client.get("dir").joinpath("release_info.json")
    if not relinfo_file.is_file():
        return "-"

    with open(relinfo_file, "r") as f:
        return json.load(f)["version"]


def get_remote_client_version(client: ClientData) -> str:
    try:
        with urllib.request.urlopen(client.get("tags_url")) as response:
            data = json.loads(response.read())
        return data[0]["name"]
    except (JSONDecodeError, TypeError):
        return "ERROR"


def backup_client_data(client: ClientData) -> None:
    name = client.get("name")
    src = client.get("dir")
    dest = client.get("backup_dir")

    with open(src.joinpath(".version"), "r") as v:
        version = v.readlines()[0]

    bm = BackupManager()
    bm.backup_directory(f"{name}-{version}", src, dest)
    if name == "mainsail":
        bm.backup_file(MAINSAIL_CONFIG_JSON, dest)
    bm.backup_file(NGINX_SITES_AVAILABLE.joinpath(name), dest)


def backup_client_config_data(client: ClientData) -> None:
    client_config = client.get("client_config")
    name = client_config.get("name")
    source = client_config.get("dir")
    target = client_config.get("backup_dir")
    bm = BackupManager()
    bm.backup_directory(name, source, target)


def get_existing_clients() -> List[ClientData]:
    clients = list(get_args(ClientName))
    installed_clients: List[ClientData] = []
    for c in clients:
        c_data: ClientData = load_client_data(c)
        if c_data.get("dir").exists():
            installed_clients.append(c_data)

    return installed_clients


def get_existing_client_config() -> List[ClientData]:
    clients = list(get_args(ClientName))
    installed_client_configs: List[ClientData] = []
    for c in clients:
        c_data: ClientData = load_client_data(c)
        c_config_data: ClientConfigData = c_data.get("client_config")
        if c_config_data.get("dir").exists():
            installed_client_configs.append(c_data)

    return installed_client_configs


def config_for_other_client_exist(client_to_ignore: ClientName) -> bool:
    """
    Check if any other client configs are present on the system.
    It is usually not harmful, but chances are they can conflict each other.
    Multiple client configs are, at least, redundant to have them installed
    :param client_to_ignore: The client name to ignore for the check
    :return: True, if other client configs were found, else False
    """

    clients = set([c["name"] for c in get_existing_client_config()])
    clients = clients - {client_to_ignore}

    return True if len(clients) > 0 else False
