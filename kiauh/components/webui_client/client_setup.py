# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
import tempfile
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client import MODULE_PATH
from components.webui_client.base_data import (
    BaseWebClient,
    BaseWebClientConfig,
    WebClientType,
)
from components.webui_client.client_config.client_config_setup import (
    install_client_config,
)
from components.webui_client.client_dialogs import (
    print_install_client_config_dialog,
    print_moonraker_not_found_dialog,
)
from components.webui_client.client_utils import (
    copy_common_vars_nginx_cfg,
    copy_upstream_nginx_cfg,
    create_nginx_cfg,
    detect_client_cfg_conflict,
    enable_mainsail_remotemode,
    get_client_port_selection,
    symlink_webui_nginx_log,
)
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.common import backup_printer_config_dir, check_install_dependencies
from utils.config_utils import add_config_section
from utils.fs_utils import unzip
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_service,
    download_file,
    get_ipv4_addr,
)


def install_client(
    client: BaseWebClient,
    settings: KiauhSettings,
    reinstall: bool = False,
) -> None:
    mr_instances: List[Moonraker] = get_instances(Moonraker)

    enable_remotemode = False
    if not mr_instances:
        print_moonraker_not_found_dialog(client.display_name)
        if not get_confirm(f"Continue {client.display_name} installation?"):
            return

    # if moonraker is not installed or multiple instances
    # are installed we enable mainsails remote mode
    if (
        client.client == WebClientType.MAINSAIL
        and not mr_instances
        or len(mr_instances) > 1
    ):
        enable_remotemode = True

    kl_instances = get_instances(Klipper)
    install_client_cfg = False
    client_config: BaseWebClientConfig = client.client_config
    if (
        kl_instances
        and not client_config.config_dir.exists()
        and not detect_client_cfg_conflict(client)
    ):
        print_install_client_config_dialog(client)
        question = f"Download the recommended {client_config.display_name}?"
        install_client_cfg = get_confirm(question, allow_go_back=False)

    default_port: int = int(settings.get(client.name, "port"))
    port: int = (
        default_port if reinstall else get_client_port_selection(client, settings)
    )

    check_install_dependencies({"nginx"})

    try:
        download_client(client)
        if enable_remotemode and client.client == WebClientType.MAINSAIL:
            enable_mainsail_remotemode()

        backup_printer_config_dir()
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
        InstanceManager.restart_all(mr_instances)

        if install_client_cfg and kl_instances:
            install_client_config(client, False)

        copy_upstream_nginx_cfg()
        copy_common_vars_nginx_cfg()
        create_nginx_cfg(
            display_name=client.display_name,
            cfg_name=client.name,
            template_src=MODULE_PATH.joinpath("assets/nginx_cfg"),
            PORT=port,
            ROOT_DIR=client.client_dir,
            NAME=client.name,
        )

        if kl_instances:
            symlink_webui_nginx_log(client, kl_instances)
        cmd_sysctl_service("nginx", "restart")

    except Exception as e:
        Logger.print_error(e)
        Logger.print_dialog(
            DialogType.ERROR,
            center_content=True,
            content=[f"{client.display_name} installation failed!"],
        )
        return

    # noinspection HttpUrlsUsage
    Logger.print_dialog(
        DialogType.CUSTOM,
        custom_title=f"{client.display_name} installation complete!",
        custom_color=Color.GREEN,
        center_content=True,
        content=[
            f"Open {client.display_name} now on: http://{get_ipv4_addr()}{'' if port == 80 else f':{port}'}",
        ],
    )


def download_client(client: BaseWebClient) -> None:
    zipfile = f"{client.name.lower()}.zip"
    target = Path().home().joinpath(zipfile)
    try:
        Logger.print_status(
            f"Downloading {client.display_name} from {client.download_url} ..."
        )
        download_file(client.download_url, target, True)
        Logger.print_ok("Download complete!")

        Logger.print_status(f"Extracting {zipfile} ...")
        unzip(target, client.client_dir)
        target.unlink(missing_ok=True)
        Logger.print_ok("OK!")

    except Exception:
        Logger.print_error(f"Downloading {client.display_name} failed!")
        raise


def update_client(client: BaseWebClient) -> None:
    Logger.print_status(f"Updating {client.display_name} ...")
    if not client.client_dir.exists():
        Logger.print_info(
            f"Unable to update {client.display_name}. Directory does not exist! Skipping ..."
        )
        return

    with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
        Logger.print_status(
            f"Creating temporary backup of {client.config_file} as {tmp_file.name} ..."
        )
        shutil.copy(client.config_file, tmp_file.name)
        download_client(client)
        shutil.copy(tmp_file.name, client.config_file)
