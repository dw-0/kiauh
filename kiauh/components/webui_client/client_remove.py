# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
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
from core.constants import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from core.logger import Logger
from core.services.backup_service import BackupService
from core.services.message_service import Message
from core.types.color import Color
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
) -> Message:
    completion_msg = Message(
        title=f"{client.display_name} Removal Process completed",
        color=Color.GREEN,
    )
    mr_instances: List[Moonraker] = get_instances(Moonraker)
    kl_instances: List[Klipper] = get_instances(Klipper)
    svc = BackupService()

    if backup_config:
        version = ""
        src = client.client_dir
        if src.joinpath(".version").exists():
            with open(src.joinpath(".version"), "r") as v:
                version = v.readlines()[0]

        target_path = svc.backup_root.joinpath(f"{client.client_dir.name}_{version}")
        success = svc.backup_file(
            source_path=client.config_file,
            target_path=target_path,
        )
        if success:
            completion_msg.text.append(f"● {client.config_file.name} backup created")

    if remove_client:
        client_name = client.name
        if remove_client_dir(client):
            completion_msg.text.append(f"● {client.display_name} removed")
        if remove_client_nginx_config(client_name):
            completion_msg.text.append("● NGINX config removed")
        if remove_client_nginx_logs(client, kl_instances):
            completion_msg.text.append("● NGINX logs removed")

        svc.backup_moonraker_conf()
        section = f"update_manager {client_name}"
        handled_instances: List[Moonraker] = remove_config_section(
            section, mr_instances
        )
        if handled_instances:
            names = [i.service_file_path.stem for i in handled_instances]
            completion_msg.text.append(
                f"● Moonraker config section '{section}' removed for instance: {', '.join(names)}"
            )

    if remove_client_cfg:
        cfg_completion_msg = run_client_config_removal(
            client.client_config,
            kl_instances,
            mr_instances,
            svc,
        )
        if cfg_completion_msg.color == Color.GREEN:
            completion_msg.text.extend(cfg_completion_msg.text[1:])

    if not completion_msg.text:
        completion_msg.color = Color.YELLOW
        completion_msg.centered = True
        completion_msg.text.append("Nothing to remove.")
    else:
        completion_msg.text.insert(0, "The following actions were performed:")

    return completion_msg


def remove_client_dir(client: BaseWebClient) -> bool:
    Logger.print_status(f"Removing {client.display_name} ...")
    return run_remove_routines(client.client_dir)


def remove_client_nginx_config(name: str) -> bool:
    Logger.print_status(f"Removing NGINX config for {name.capitalize()} ...")
    return remove_with_sudo(
        [
            NGINX_SITES_AVAILABLE.joinpath(name),
            NGINX_SITES_ENABLED.joinpath(name),
        ]
    )


def remove_client_nginx_logs(client: BaseWebClient, instances: List[Klipper]) -> bool:
    Logger.print_status(f"Removing NGINX logs for {client.display_name} ...")

    files = [client.nginx_access_log, client.nginx_error_log]
    if instances:
        for instance in instances:
            files.append(instance.base.log_dir.joinpath(client.nginx_access_log.name))
            files.append(instance.base.log_dir.joinpath(client.nginx_error_log.name))

    return remove_with_sudo(files)
