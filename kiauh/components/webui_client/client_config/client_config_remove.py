# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #


from typing import List, Optional

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import BaseWebClientConfig
from core.logger import Logger
from core.services.backup_service import BackupService
from core.services.message_service import Message
from core.types.color import Color
from utils.config_utils import remove_config_section
from utils.fs_utils import run_remove_routines
from utils.instance_type import InstanceType
from utils.instance_utils import get_instances


def run_client_config_removal(
    client_config: BaseWebClientConfig,
    kl_instances: List[Klipper],
    mr_instances: List[Moonraker],
    svc: Optional[BackupService] = None,
) -> Message:
    completion_msg = Message(
        title=f"{client_config.display_name} Removal Process completed",
        color=Color.GREEN,
    )
    Logger.print_status(f"Removing {client_config.display_name} ...")
    if run_remove_routines(client_config.config_dir):
        completion_msg.text.append(f"● {client_config.display_name} removed")

    if svc is None:
        svc = BackupService()

    svc.backup_moonraker_conf()
    completion_msg = remove_moonraker_config_section(
        completion_msg, client_config, mr_instances
    )

    svc.backup_printer_cfg()
    completion_msg = remove_printer_config_section(
        completion_msg, client_config, kl_instances
    )

    if completion_msg.text:
        completion_msg.text.insert(0, "The following actions were performed:")
    else:
        completion_msg.color = Color.YELLOW
        completion_msg.centered = True
        completion_msg.text = ["Nothing to remove."]

    return completion_msg


def remove_cfg_symlink(client_config: BaseWebClientConfig, message: Message) -> Message:
    instances: List[Klipper] = get_instances(Klipper)
    kl_instances = []
    for instance in instances:
        cfg = instance.base.cfg_dir.joinpath(client_config.config_filename)
        if run_remove_routines(cfg):
            kl_instances.append(instance)
    text = f"{client_config.display_name} removed from instance"
    return update_msg(kl_instances, message, text)


def remove_printer_config_section(
    message: Message, client_config: BaseWebClientConfig, kl_instances: List[Klipper]
) -> Message:
    kl_section = client_config.config_section
    kl_instances = remove_config_section(kl_section, kl_instances)
    text = f"Klipper config section '{kl_section}' removed for instance"
    return update_msg(kl_instances, message, text)


def remove_moonraker_config_section(
    message: Message, client_config: BaseWebClientConfig, mr_instances: List[Moonraker]
) -> Message:
    mr_section = f"update_manager {client_config.name}"
    mr_instances = remove_config_section(mr_section, mr_instances)
    text = f"Moonraker config section '{mr_section}' removed for instance"
    return update_msg(mr_instances, message, text)


def update_msg(instances: List[InstanceType], message: Message, text: str) -> Message:
    if not instances:
        return message

    instance_names = [i.service_file_path.stem for i in instances]
    message.text.append(f"● {text}: {', '.join(instance_names)}")
    return message
