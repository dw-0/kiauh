# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import json  # noqa: I001
import shutil
from pathlib import Path
from typing import List, get_args

from components.klipper.klipper import Klipper
from components.webui_client.base_data import (
    BaseWebClient,
    BaseWebClientConfig,
    WebClientType,
)
from components.webui_client.mainsail_data import MainsailData
from core.backup_manager.backup_manager import BackupManager
from core.settings.kiauh_settings import KiauhSettings
from utils import NGINX_CONFD, NGINX_SITES_AVAILABLE
from utils.common import get_install_status
from utils.constants import COLOR_CYAN, COLOR_YELLOW, RESET_FORMAT
from utils.git_utils import (
    get_latest_tag,
    get_latest_unstable_tag,
)
from utils.logger import Logger
from utils.types import ComponentStatus


def get_client_status(
    client: BaseWebClient, fetch_remote: bool = False
) -> ComponentStatus:
    files = [
        NGINX_SITES_AVAILABLE.joinpath(client.name),
        NGINX_CONFD.joinpath("upstreams.conf"),
        NGINX_CONFD.joinpath("common_vars.conf"),
    ]
    comp_status: ComponentStatus = get_install_status(client.client_dir, files=files)

    # if the client dir does not exist, set the status to not
    # installed even if the other files are present
    if not client.client_dir.exists():
        comp_status.status = 0

    comp_status.local = get_local_client_version(client)
    comp_status.remote = get_remote_client_version(client) if fetch_remote else None
    return comp_status


def get_client_config_status(client: BaseWebClient) -> ComponentStatus:
    return get_install_status(client.client_config.config_dir)


def get_current_client_config(clients: List[BaseWebClient]) -> str:
    installed = []
    for client in clients:
        client_config = client.client_config
        if client_config.config_dir.exists():
            installed.append(client)

    if len(installed) > 1:
        return f"{COLOR_YELLOW}Conflict!{RESET_FORMAT}"
    elif len(installed) == 1:
        cfg = installed[0].client_config
        return f"{COLOR_CYAN}{cfg.display_name}{RESET_FORMAT}"

    return f"{COLOR_CYAN}-{RESET_FORMAT}"


def backup_mainsail_config_json(is_temp=False) -> None:
    c_json = MainsailData().client_dir.joinpath("config.json")
    bm = BackupManager()
    if is_temp:
        fn = Path.home().joinpath("config.json.kiauh.bak")
        bm.backup_file(c_json, custom_filename=fn)
    else:
        bm.backup_file(c_json)


def restore_mainsail_config_json() -> None:
    try:
        c_json = MainsailData().client_dir.joinpath("config.json")
        Logger.print_status(f"Restore '{c_json}' ...")
        source = Path.home().joinpath("config.json.kiauh.bak")
        shutil.copy(source, c_json)
    except OSError:
        Logger.print_info("Unable to restore config.json. Skipped ...")


def enable_mainsail_remotemode() -> None:
    Logger.print_status("Enable Mainsails remote mode ...")
    c_json = MainsailData().client_dir.joinpath("config.json")
    with open(c_json, "r") as f:
        config_data = json.load(f)

    if config_data["instancesDB"] == "browser":
        Logger.print_info("Remote mode already configured. Skipped ...")
        return

    Logger.print_status("Setting instance storage location to 'browser' ...")
    config_data["instancesDB"] = "browser"

    with open(c_json, "w") as f:
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


def get_local_client_version(client: BaseWebClient) -> str | None:
    relinfo_file = client.client_dir.joinpath("release_info.json")
    version_file = client.client_dir.joinpath(".version")

    if not client.client_dir.exists():
        return None
    if not relinfo_file.is_file() and not version_file.is_file():
        return "n/a"

    if relinfo_file.is_file():
        with open(relinfo_file, "r") as f:
            return json.load(f)["version"]
    else:
        with open(version_file, "r") as f:
            return f.readlines()[0]


def get_remote_client_version(client: BaseWebClient) -> str | None:
    try:
        if (tag := get_latest_tag(client.repo_path)) != "":
            return tag
        return None
    except Exception:
        return None


def backup_client_data(client: BaseWebClient) -> None:
    name = client.name
    src = client.client_dir
    dest = client.backup_dir

    with open(src.joinpath(".version"), "r") as v:
        version = v.readlines()[0]

    bm = BackupManager()
    bm.backup_directory(f"{name}-{version}", src, dest)
    if name == "mainsail":
        c_json = MainsailData().client_dir.joinpath("config.json")
        bm.backup_file(c_json, dest)
    bm.backup_file(NGINX_SITES_AVAILABLE.joinpath(name), dest)


def backup_client_config_data(client: BaseWebClient) -> None:
    client_config = client.client_config
    name = client_config.name
    source = client_config.config_dir
    target = client_config.backup_dir
    bm = BackupManager()
    bm.backup_directory(name, source, target)


def get_existing_clients() -> List[BaseWebClient]:
    clients = list(get_args(WebClientType))
    installed_clients: List[BaseWebClient] = []
    for client in clients:
        if client.client_dir.exists():
            installed_clients.append(client)

    return installed_clients


def get_existing_client_config() -> List[BaseWebClient]:
    clients = list(get_args(WebClientType))
    installed_client_configs: List[BaseWebClient] = []
    for client in clients:
        c_config_data: BaseWebClientConfig = client.client_config
        if c_config_data.config_dir.exists():
            installed_client_configs.append(client)

    return installed_client_configs


def config_for_other_client_exist(client_to_ignore: WebClientType) -> bool:
    """
    Check if any other client configs are present on the system.
    It is usually not harmful, but chances are they can conflict each other.
    Multiple client configs are, at least, redundant to have them installed
    :param client_to_ignore: The client name to ignore for the check
    :return: True, if other client configs were found, else False
    """

    clients = set([c.name for c in get_existing_client_config()])
    clients = clients - {client_to_ignore.value}

    return True if len(clients) > 0 else False


def get_download_url(base_url: str, client: BaseWebClient) -> str:
    settings = KiauhSettings()
    use_unstable = settings.get(client.name, "unstable_releases")
    stable_url = f"{base_url}/latest/download/{client.name}.zip"

    if not use_unstable:
        return stable_url

    try:
        unstable_tag = get_latest_unstable_tag(client.repo_path)
        if unstable_tag == "":
            raise Exception
        return f"{base_url}/download/{unstable_tag}/{client.name}.zip"
    except Exception:
        return stable_url
