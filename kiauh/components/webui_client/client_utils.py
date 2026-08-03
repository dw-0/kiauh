# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from json import JSONDecodeError
from pathlib import Path
from subprocess import PIPE, CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from components.webui_client import CLIENTS, MODULE_PATH
from components.webui_client.base_data import (
    BaseWebClient,
    BaseWebClientConfig,
    WebClientType,
)
from components.webui_client.client_dialogs import print_client_port_select_dialog
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.constants import (
    NGINX_CONFD,
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
)
from core.i18n import _tr
from core.logger import Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings, WebUiSettings
from core.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from core.types.color import Color
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.fs_utils import create_symlink, remove_with_sudo
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
        return str(Color.apply("-", Color.CYAN))
    elif len(installed) == 1:
        cfg = installed[0].client_config
        return str(Color.apply(cfg.display_name, Color.CYAN))

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

        if includes_mainsail and includes_fluidd:
            return str(Color.apply("Conflict", Color.YELLOW))

    if not mainsail_includes and not fluidd_includes:
        return str(Color.apply("-", Color.CYAN))
    elif len(fluidd_includes) > len(mainsail_includes):
        return str(Color.apply(fluidd.client_config.display_name, Color.CYAN))
    else:
        return str(Color.apply(mainsail.client_config.display_name, Color.CYAN))


def enable_mainsail_remotemode() -> None:
    Logger.print_status(_tr("Enable Mainsails remote mode ..."))
    c_json = MainsailData().client_dir.joinpath("config.json")
    with open(c_json, "r") as f:
        config_data = json.load(f)

    if config_data["instancesDB"] == "browser" or config_data["instancesDB"] == "json":
        Logger.print_info(_tr("Remote mode already configured. Skipped ..."))
        return

    Logger.print_status(_tr("Setting instance storage location to 'browser' ..."))
    config_data["instancesDB"] = "browser"

    with open(c_json, "w") as f:
        json.dump(config_data, f, indent=4)
    Logger.print_ok(_tr("Mainsails remote mode enabled!"))


def symlink_webui_nginx_log(
    client: BaseWebClient, klipper_instances: List[Klipper]
) -> None:
    Logger.print_status(_tr("Link NGINX logs into log directory ..."))
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

    if relinfo_file.is_file():
        try:
            if relinfo_file.stat().st_size == 0:
                raise JSONDecodeError("Empty file", "", 0)
            with open(relinfo_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_version = data.get("version")
            if raw_version is not None:
                parsed = str(raw_version).strip()
                if parsed:
                    return parsed
        except (JSONDecodeError, OSError):
            Logger.print_error(_tr("Invalid 'release_info.json'"))

    if version_file.is_file():
        try:
            with open(version_file, "r") as f:
                line = f.readline().strip()
            return line or None
        except OSError:
            Logger.print_error(_tr("Unable to read '.version'"))

    return None


def get_remote_client_version(client: BaseWebClient) -> str | None:
    try:
        if (tag := get_latest_remote_tag(client.repo_path)) != "":
            return str(tag)
        return None
    except Exception:
        return None


def backup_client_data(client: BaseWebClient) -> None:
    version = ""
    src = client.client_dir
    if src.joinpath(".version").exists():
        with open(src.joinpath(".version"), "r") as v:
            version = v.readlines()[0]

    svc = BackupService()
    target_path = svc.backup_root.joinpath(f"{client.client_dir.name}_{version}")
    svc.backup_directory(
        source_path=client.client_dir,
        target_path=target_path,
        backup_name=client.name,
    )
    svc.backup_file(
        source_path=client.config_file,
        target_path=target_path,
    )


def backup_client_config_data(client: BaseWebClient) -> None:
    version = ""
    src = client.client_dir
    if src.joinpath(".version").exists():
        with open(src.joinpath(".version"), "r") as v:
            version = v.readlines()[0]

    svc = BackupService()
    target_path = svc.backup_root.joinpath(f"{client.client_dir.name}_{version}")
    svc.backup_directory(
        source_path=client.client_config.config_dir,
        target_path=target_path,
        backup_name=client.client_config.name,
    )


def get_existing_clients() -> List[BaseWebClient]:
    clients: List[BaseWebClient] = [bwc() for bwc in CLIENTS.values()]
    return [client for client in clients if client.client_dir.exists()]


def detect_client_cfg_conflict(curr_client: BaseWebClient) -> bool:
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


def copy_upstream_nginx_cfg() -> None:
    source = MODULE_PATH.joinpath("assets/upstreams.conf")
    target = NGINX_CONFD.joinpath("upstreams.conf")
    try:
        command = ["sudo", "cp", source, target]
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = _tr("Unable to create upstreams.conf: {}").format(e.stderr.decode())
        Logger.print_error(log)
        raise


def copy_common_vars_nginx_cfg() -> None:
    source = MODULE_PATH.joinpath("assets/common_vars.conf")
    target = NGINX_CONFD.joinpath("common_vars.conf")
    try:
        command = ["sudo", "cp", source, target]
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = _tr("Unable to create upstreams.conf: {}").format(e.stderr.decode())
        Logger.print_error(log)
        raise


def generate_nginx_cfg_from_template(name: str, template_src: Path, **kwargs) -> None:
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
        log = _tr("Unable to create '{}': {}").format(target, e.stderr.decode())
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
        Logger.print_status(_tr("Creating NGINX config for {} ...").format(display_name))

        source = NGINX_SITES_AVAILABLE.joinpath(cfg_name)
        target = NGINX_SITES_ENABLED.joinpath(cfg_name)
        remove_with_sudo(Path("/etc/nginx/sites-enabled/default"))
        generate_nginx_cfg_from_template(cfg_name, template_src=template_src, **kwargs)
        create_symlink(source, target, True)
        set_nginx_permissions()

        Logger.print_ok(_tr("NGINX config for {} successfully created.").format(display_name))
    except Exception:
        Logger.print_error(_tr("Creating NGINX config for {} failed!").format(display_name))
        raise


def get_nginx_config_list() -> List[Path]:
    configs: List[Path] = []
    for config in NGINX_SITES_ENABLED.iterdir():
        if not config.is_file():
            continue
        configs.append(config)
    return configs


def get_nginx_listen_port(config: Path) -> int | None:
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
                _tr("Unable to parse listen port {} from {}!").format(port, config.name)
            )
            return None


def read_ports_from_nginx_configs() -> List[int]:
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
        _type = _tr("Reconfigure") if reconfigure else _tr("Configure")
        question = _tr("{} {} for port").format(_type, client.display_name)
        port_input: int | None = get_number_input(question, min_value=80, default=port)

        if port_input and port_input not in ports_in_use:
            client_settings: WebUiSettings = settings[client.name]
            client_settings.port = port_input
            settings.save()

            return port_input

        Logger.print_error(_tr("This port is already in use. Please select another one."))


def get_next_free_port(ports_in_use: List[int]) -> int:
    valid_ports = set(range(80, 7125))
    used_ports = set(map(int, ports_in_use))

    return min(valid_ports - used_ports)


def set_listen_port(client: BaseWebClient, curr_port: int, new_port: int) -> None:
    config = NGINX_SITES_AVAILABLE.joinpath(client.name)
    with open(config, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if "listen" in line:
            lines[i] = line.replace(str(curr_port), str(new_port))

    with open(config, "w") as f:
        f.writelines(lines)


def create_client_config_symlink(
    client_config: BaseWebClientConfig, klipper_instances: List[Klipper]
) -> None:
    for instance in klipper_instances:
        Logger.print_status(_tr("Create symlink for {} ...").format(client_config.config_filename))
        source = Path(client_config.config_dir, client_config.config_filename)
        target = instance.base.cfg_dir
        Logger.print_status(_tr("Linking {} to {}").format(source, target))
        try:
            create_symlink(source, target)
        except Exception:
            Logger.print_error(_tr("Creating symlink failed!"))
