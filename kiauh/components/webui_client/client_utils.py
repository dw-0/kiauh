# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run
from typing import List, get_args

from components.klipper.klipper import Klipper
from components.webui_client import MODULE_PATH
from components.webui_client.base_data import (
    BaseWebClient,
    WebClientType,
)
from components.webui_client.client_dialogs import print_client_port_select_dialog
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.backup_manager.backup_manager import BackupManager
from core.constants import (
    NGINX_CONFD,
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
)
from core.logger import Logger
from core.settings.kiauh_settings import KiauhSettings, WebUiSettings
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from core.types.color import Color
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.fs_utils import create_symlink, remove_file
from utils.git_utils import (
    get_latest_remote_tag,
    get_latest_unstable_tag,
)
from utils.input_utils import get_number_input
from utils.instance_utils import get_instances


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


def get_current_client_config() -> str:
    mainsail, fluidd = MainsailData(), FluiddData()
    clients: List[BaseWebClient] = [mainsail, fluidd]
    installed = [c for c in clients if c.client_config.config_dir.exists()]

    if not installed:
        return Color.apply("-", Color.CYAN)
    elif len(installed) == 1:
        cfg = installed[0].client_config
        return Color.apply(cfg.display_name, Color.CYAN)

    # at this point, both client config folders exists, so we need to check
    # which are actually included in the printer.cfg of all klipper instances
    mainsail_includes, fluidd_includes = [], []
    klipper_instances: List[Klipper] = get_instances(Klipper)
    for instance in klipper_instances:
        scp = SimpleConfigParser()
        scp.read_file(instance.cfg_file)
        includes_mainsail = scp.has_section(mainsail.client_config.config_section)
        includes_fluidd = scp.has_section(fluidd.client_config.config_section)

        if includes_mainsail:
            mainsail_includes.append(instance)
        if includes_fluidd:
            fluidd_includes.append(instance)

        # if both are included in the same file, we have a potential conflict
        if includes_mainsail and includes_fluidd:
            return Color.apply("Conflict", Color.YELLOW)

    if not mainsail_includes and not fluidd_includes:
        # there are no includes at all, even though the client config folders exist
        return Color.apply("-", Color.CYAN)
    elif len(fluidd_includes) > len(mainsail_includes):
        # there are more instances that include fluidd than mainsail
        return Color.apply(fluidd.client_config.display_name, Color.CYAN)
    else:
        # there are the same amount of non-conflicting includes for each config
        # or more instances include mainsail than fluidd
        return Color.apply(mainsail.client_config.display_name, Color.CYAN)


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


def symlink_webui_nginx_log(
    client: BaseWebClient, klipper_instances: List[Klipper]
) -> None:
    Logger.print_status("Link NGINX logs into log directory ...")
    access_log = client.nginx_access_log
    error_log = client.nginx_error_log

    for instance in klipper_instances:
        desti_access = instance.base.log_dir.joinpath(access_log.name)
        if not desti_access.exists():
            desti_access.symlink_to(access_log)

        desti_error = instance.base.log_dir.joinpath(error_log.name)
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
            return str(json.load(f)["version"])
    else:
        with open(version_file, "r") as f:
            return f.readlines()[0]


def get_remote_client_version(client: BaseWebClient) -> str | None:
    try:
        if (tag := get_latest_remote_tag(client.repo_path)) != "":
            return str(tag)
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
    bm.backup_file(client.config_file, dest)
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


def detect_client_cfg_conflict(curr_client: BaseWebClient) -> bool:
    """
    Check if any other client configs are present on the system.
    It is usually not harmful, but chances are they can conflict each other.
    Multiple client configs are, at least, redundant to have them installed
    :param curr_client: The client name to check for the conflict
    :return: True, if other client configs were found, else False
    """

    mainsail_cfg_status: ComponentStatus = get_client_config_status(MainsailData())
    fluidd_cfg_status: ComponentStatus = get_client_config_status(FluiddData())

    if curr_client.client == WebClientType.MAINSAIL and fluidd_cfg_status.status == 2:
        return True
    if curr_client.client == WebClientType.FLUIDD and mainsail_cfg_status.status == 2:
        return True

    return False


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


#################################################
## NGINX RELATED FUNCTIONS
#################################################


def copy_upstream_nginx_cfg() -> None:
    """
    Creates an upstream.conf in /etc/nginx/conf.d
    :return: None
    """
    source = MODULE_PATH.joinpath("assets/upstreams.conf")
    target = NGINX_CONFD.joinpath("upstreams.conf")
    try:
        command = ["sudo", "cp", source, target]
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def copy_common_vars_nginx_cfg() -> None:
    """
    Creates a common_vars.conf in /etc/nginx/conf.d
    :return: None
    """
    source = MODULE_PATH.joinpath("assets/common_vars.conf")
    target = NGINX_CONFD.joinpath("common_vars.conf")
    try:
        command = ["sudo", "cp", source, target]
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def generate_nginx_cfg_from_template(name: str, template_src: Path, **kwargs) -> None:
    """
    Creates an NGINX config from a template file and
    replaces all placeholders passed as kwargs. A placeholder must be defined
    in the template file as %{placeholder}%.
    :param name: name of the config to create
    :param template_src: the path to the template file
    :return: None
    """
    tmp = Path.home().joinpath(f"{name}.tmp")
    shutil.copy(template_src, tmp)
    with open(tmp, "r+") as f:
        content = f.read()

        for key, value in kwargs.items():
            content = content.replace(f"%{key}%", str(value))

        f.seek(0)
        f.write(content)
        f.truncate()

    target = NGINX_SITES_AVAILABLE.joinpath(name)
    try:
        command = ["sudo", "mv", tmp, target]
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Unable to create '{target}': {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def create_nginx_cfg(
    display_name: str,
    cfg_name: str,
    template_src: Path,
    **kwargs,
) -> None:
    from utils.sys_utils import set_nginx_permissions

    try:
        Logger.print_status(f"Creating NGINX config for {display_name} ...")

        source = NGINX_SITES_AVAILABLE.joinpath(cfg_name)
        target = NGINX_SITES_ENABLED.joinpath(cfg_name)
        remove_file(Path("/etc/nginx/sites-enabled/default"), True)
        generate_nginx_cfg_from_template(cfg_name, template_src=template_src, **kwargs)
        create_symlink(source, target, True)
        set_nginx_permissions()

        Logger.print_ok(f"NGINX config for {display_name} successfully created.")
    except Exception:
        Logger.print_error(f"Creating NGINX config for {display_name} failed!")
        raise


def get_nginx_config_list() -> List[Path]:
    """
    Get a list of all NGINX config files in /etc/nginx/sites-enabled
    :return: List of NGINX config files
    """
    configs: List[Path] = []
    for config in NGINX_SITES_ENABLED.iterdir():
        if not config.is_file():
            continue
        configs.append(config)
    return configs


def get_nginx_listen_port(config: Path) -> int | None:
    """
    Get the listen port from an NGINX config file
    :param config: The NGINX config file to read the port from
    :return: The listen port as int or None if not found/parsable
    """

    # noinspection HttpUrlsUsage
    pattern = r"default_server|http://|https://|[;\[\]]"
    port = ""
    with open(config, "r") as cfg:
        for line in cfg.readlines():
            line = re.sub(pattern, "", line.strip())
            if line.startswith("listen"):
                if ":" not in line:
                    port = line.split()[-1]
                else:
                    port = line.split(":")[-1]
        try:
            return int(port)
        except ValueError:
            Logger.print_error(
                f"Unable to parse listen port {port} from {config.name}!"
            )
            return None


def read_ports_from_nginx_configs() -> List[int]:
    """
    Helper function to iterate over all NGINX configs
    and read all ports defined for listen
    :return: A sorted list of listen ports
    """
    if not NGINX_SITES_ENABLED.exists():
        return []

    port_list: List[int] = []
    for config in get_nginx_config_list():
        port = get_nginx_listen_port(config)
        if port is not None:
            port_list.append(port)

    return sorted(port_list, key=lambda x: int(x))


def get_client_port_selection(
    client: BaseWebClient,
    settings: KiauhSettings,
    reconfigure=False,
) -> int:
    default_port: int = int(settings.get(client.name, "port"))
    ports_in_use: List[int] = read_ports_from_nginx_configs()
    next_free_port: int = get_next_free_port(ports_in_use)

    port: int = (
        next_free_port
        if not reconfigure and default_port in ports_in_use
        else default_port
    )

    print_client_port_select_dialog(client.display_name, port, ports_in_use)

    while True:
        _type = "Reconfigure" if reconfigure else "Configure"
        question = f"{_type} {client.display_name} for port"
        port_input = get_number_input(question, min_value=80, default=port)

        if port_input not in ports_in_use:
            client_settings: WebUiSettings = settings[client.name]
            client_settings.port = port_input
            settings.save()

            return port_input

        Logger.print_error("This port is already in use. Please select another one.")


def get_next_free_port(ports_in_use: List[int]) -> int:
    valid_ports = set(range(80, 7125))
    used_ports = set(map(int, ports_in_use))

    return min(valid_ports - used_ports)


def set_listen_port(client: BaseWebClient, curr_port: int, new_port: int) -> None:
    """
    Set the port the client should listen on in the NGINX config
    :param curr_port: The current port the client listens on
    :param new_port: The new port to set
    :param client: The client to set the port for
    :return: None
    """
    config = NGINX_SITES_AVAILABLE.joinpath(client.name)
    with open(config, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "listen" in line:
            lines[i] = line.replace(str(curr_port), str(new_port))

    with open(config, "w") as f:
        f.writelines(lines)
