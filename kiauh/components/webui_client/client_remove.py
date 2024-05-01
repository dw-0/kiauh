# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #


import shutil
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import (
    BaseWebClient,
    WebClientType,
)
from components.webui_client.client_config.client_config_remove import (
    run_client_config_removal,
)
from components.webui_client.client_utils import backup_mainsail_config_json

from core.instance_manager.instance_manager import InstanceManager
from utils.config_utils import remove_config_section
from utils.filesystem_utils import (
    remove_nginx_config,
    remove_nginx_logs,
)
from utils.logger import Logger


def run_client_removal(
    client: BaseWebClient,
    rm_client: bool,
    rm_client_config: bool,
    backup_ms_config_json: bool,
) -> None:
    mr_im = InstanceManager(Moonraker)
    mr_instances: List[Moonraker] = mr_im.instances
    kl_im = InstanceManager(Klipper)
    kl_instances: List[Klipper] = kl_im.instances

    if backup_ms_config_json and client.client == WebClientType.MAINSAIL:
        backup_mainsail_config_json()

    if rm_client:
        client_name = client.name
        remove_client_dir(client)
        remove_nginx_config(client_name)
        remove_nginx_logs(client_name, kl_instances)

        section = f"update_manager {client_name}"
        remove_config_section(section, mr_instances)

    if rm_client_config:
        run_client_config_removal(
            client.client_config,
            kl_instances,
            mr_instances,
        )


def remove_client_dir(client: BaseWebClient) -> None:
    Logger.print_status(f"Removing {client.display_name} ...")
    client_dir = client.client_dir
    if not client.client_dir.exists():
        Logger.print_info(f"'{client_dir}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(client_dir)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{client_dir}':\n{e}")
