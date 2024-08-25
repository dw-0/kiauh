# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import (
    BaseWebClient,
)
from components.webui_client.client_config.client_config_remove import (
    run_client_config_removal,
)
from core.backup_manager.backup_manager import BackupManager
from core.constants import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from core.logger import Logger
from utils.config_utils import remove_config_section
from utils.fs_utils import (
    remove_with_sudo,
    run_remove_routines,
)
from utils.instance_utils import get_instances


def run_client_removal(
    client: BaseWebClient,
    remove_client: bool,
    remove_client_cfg: bool,
    backup_config: bool,
) -> None:
    mr_instances: List[Moonraker] = get_instances(Moonraker)
    kl_instances: List[Klipper] = get_instances(Klipper)

    if backup_config:
        bm = BackupManager()
        bm.backup_file(client.config_file)

    if remove_client:
        client_name = client.name
        remove_client_dir(client)
        remove_client_nginx_config(client_name)
        remove_client_nginx_logs(client, kl_instances)

        section = f"update_manager {client_name}"
        remove_config_section(section, mr_instances)

    if remove_client_cfg:
        run_client_config_removal(
            client.client_config,
            kl_instances,
            mr_instances,
        )


def remove_client_dir(client: BaseWebClient) -> None:
    Logger.print_status(f"Removing {client.display_name} ...")
    run_remove_routines(client.client_dir)


def remove_client_nginx_config(name: str) -> None:
    Logger.print_status(f"Removing NGINX config for {name.capitalize()} ...")

    remove_with_sudo(NGINX_SITES_AVAILABLE.joinpath(name))
    remove_with_sudo(NGINX_SITES_ENABLED.joinpath(name))


def remove_client_nginx_logs(client: BaseWebClient, instances: List[Klipper]) -> None:
    Logger.print_status(f"Removing NGINX logs for {client.display_name} ...")

    remove_with_sudo(client.nginx_access_log)
    remove_with_sudo(client.nginx_error_log)

    if not instances:
        return

    for instance in instances:
        run_remove_routines(
            instance.base.log_dir.joinpath(client.nginx_access_log.name)
        )
        run_remove_routines(instance.base.log_dir.joinpath(client.nginx_error_log.name))
