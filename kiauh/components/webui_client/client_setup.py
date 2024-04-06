# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper

from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import (
    WebClientType,
    BaseWebClient,
    BaseWebClientConfig,
)
from components.webui_client.client_config.client_config_setup import (
    install_client_config,
)
from components.webui_client.client_dialogs import (
    print_moonraker_not_found_dialog,
    print_client_port_select_dialog,
    print_install_client_config_dialog,
)
from components.webui_client.client_utils import (
    backup_mainsail_config_json,
    restore_mainsail_config_json,
    enable_mainsail_remotemode,
    symlink_webui_nginx_log,
    config_for_other_client_exist,
)
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from kiauh import KIAUH_CFG
from utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from utils.common import check_install_dependencies
from utils.filesystem_utils import (
    unzip,
    copy_upstream_nginx_cfg,
    copy_common_vars_nginx_cfg,
    create_nginx_cfg,
    create_symlink,
    remove_file,
    add_config_section,
    read_ports_from_nginx_configs,
    is_valid_port,
    get_next_free_port,
)
from utils.input_utils import get_confirm, get_number_input
from utils.logger import Logger
from utils.system_utils import (
    download_file,
    set_nginx_permissions,
    get_ipv4_addr,
    control_systemd_service,
)


def install_client(client: BaseWebClient) -> None:
    if client is None:
        raise ValueError("Missing parameter client_data!")

    if client.client_dir.exists():
        Logger.print_info(
            f"{client.display_name} seems to be already installed! Skipped ..."
        )
        return

    mr_im = InstanceManager(Moonraker)
    mr_instances: List[Moonraker] = mr_im.instances

    enable_remotemode = False
    if not mr_instances:
        print_moonraker_not_found_dialog()
        if not get_confirm(
            f"Continue {client.display_name} installation?",
            allow_go_back=True,
        ):
            return

    # if moonraker is not installed or multiple instances
    # are installed we enable mainsails remote mode
    if (
        client.client == WebClientType.MAINSAIL
        and not mr_instances
        or len(mr_instances) > 1
    ):
        enable_remotemode = True

    kl_im = InstanceManager(Klipper)
    kl_instances = kl_im.instances
    install_client_cfg = False
    client_config: BaseWebClientConfig = client.client_config
    if (
        kl_instances
        and not client_config.config_dir.exists()
        and not config_for_other_client_exist(client_to_ignore=client.client)
    ):
        print_install_client_config_dialog(client)
        question = f"Download the recommended {client_config.display_name}?"
        install_client_cfg = get_confirm(question, allow_go_back=False)

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    default_port = cm.get_value(client.name, "port")
    client_port = default_port if default_port and default_port.isdigit() else "80"
    ports_in_use = read_ports_from_nginx_configs()

    # check if configured port is a valid number and not in use already
    valid_port = is_valid_port(client_port, ports_in_use)
    while not valid_port:
        next_port = get_next_free_port(ports_in_use)
        print_client_port_select_dialog(client.display_name, next_port, ports_in_use)
        client_port = str(
            get_number_input(
                f"Configure {client.display_name} for port",
                min_count=int(next_port),
                default=next_port,
            )
        )
        valid_port = is_valid_port(client_port, ports_in_use)

    check_install_dependencies(["nginx"])

    try:
        download_client(client)
        if enable_remotemode and client.client == WebClientType.MAINSAIL:
            enable_mainsail_remotemode()
        if mr_instances:
            add_config_section(
                section=f"update_manager {client.name}",
                instances=mr_instances,
                options=[
                    ("type", "web"),
                    ("channel", "stable"),
                    ("repo", str(client.repo_path)),
                    ("path", str(client.client_dir)),
                ],
            )
            mr_im.restart_all_instance()
        if install_client_cfg and kl_instances:
            install_client_config(client)

        copy_upstream_nginx_cfg()
        copy_common_vars_nginx_cfg()
        create_client_nginx_cfg(client, client_port)
        if kl_instances:
            symlink_webui_nginx_log(kl_instances)
        control_systemd_service("nginx", "restart")

    except Exception as e:
        Logger.print_error(f"{client.display_name} installation failed!\n{e}")
        return

    log = f"Open {client.display_name} now on: http://{get_ipv4_addr()}:{client_port}"
    Logger.print_ok(f"{client.display_name} installation complete!", start="\n")
    Logger.print_ok(log, prefix=False, end="\n\n")


def download_client(client: BaseWebClient) -> None:
    zipfile = f"{client.name.lower()}.zip"
    target = Path().home().joinpath(zipfile)
    try:
        Logger.print_status(f"Downloading {zipfile} ...")
        download_file(client.stable_url, target, True)
        Logger.print_ok("Download complete!")

        Logger.print_status(f"Extracting {zipfile} ...")
        unzip(target, client.client_dir)
        target.unlink(missing_ok=True)
        Logger.print_ok("OK!")

    except Exception:
        Logger.print_error(f"Downloading {zipfile} failed!")
        raise


def update_client(client: BaseWebClient) -> None:
    Logger.print_status(f"Updating {client.display_name} ...")
    if not client.client_dir.exists():
        Logger.print_info(
            f"Unable to update {client.display_name}. Directory does not exist! Skipping ..."
        )
        return

    if client.client == WebClientType.MAINSAIL:
        backup_mainsail_config_json(is_temp=True)

    download_client(client)

    if client.client == WebClientType.MAINSAIL:
        restore_mainsail_config_json()


def create_client_nginx_cfg(client: BaseWebClient, port: int) -> None:
    display_name = client.display_name
    root_dir = client.client_dir
    source = NGINX_SITES_AVAILABLE.joinpath(client.name)
    target = NGINX_SITES_ENABLED.joinpath(client.name)
    try:
        Logger.print_status(f"Creating NGINX config for {display_name} ...")
        remove_file(Path("/etc/nginx/sites-enabled/default"), True)
        create_nginx_cfg(client.name, port, root_dir)
        create_symlink(source, target, True)
        set_nginx_permissions()
        Logger.print_ok(f"NGINX config for {display_name} successfully created.")
    except Exception:
        Logger.print_error(f"Creating NGINX config for {display_name} failed!")
        raise
