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
from components.webui_client.base_data import BaseWebClientConfig
from core.logger import Logger
from core.services.message_service import Message
from core.types.color import Color
from utils.config_utils import remove_config_section
from utils.fs_utils import run_remove_routines
from utils.instance_utils import get_instances


def run_client_config_removal(
    client_config: BaseWebClientConfig,
    kl_instances: List[Klipper],
    mr_instances: List[Moonraker],
) -> Message:
    completion_msg = Message(
        title=f"{client_config.display_name} Removal Process completed",
        color=Color.GREEN,
    )
    Logger.print_status(f"Removing {client_config.display_name} ...")
    if run_remove_routines(client_config.config_dir):
        completion_msg.text.append(f"● {client_config.display_name} removed")

    instances: List[Klipper] = get_instances(Klipper)
    handled_configs = []
    for instance in instances:
        if run_remove_routines(
            instance.base.cfg_dir.joinpath(client_config.config_filename)
        ):
            handled_configs.append(instance)
    if handled_configs:
        instance_names = [i.service_file_path.stem for i in handled_configs]
        completion_msg.text.append(
            f"● {client_config.display_name} removed from instances: {', '.join(instance_names)}"
        )

    mr_section = f"update_manager {client_config.name}"
    handled_mr_instances = remove_config_section(mr_section, mr_instances)
    if handled_mr_instances:
        instance_names = [i.service_file_path.stem for i in handled_mr_instances]
        completion_msg.text.append(
            f"● Moonraker config section '{mr_section}' removed for instance: {', '.join(instance_names)}"
        )

    kl_section = client_config.config_section
    handled_kl_instances = remove_config_section(kl_section, kl_instances)
    if handled_kl_instances:
        instance_names = [i.service_file_path.stem for i in handled_kl_instances]
        completion_msg.text.append(
            f"● Klipper config section '{mr_section}' removed for instance: {', '.join(instance_names)}"
        )

    if not completion_msg.text:
        completion_msg.color = Color.YELLOW
        completion_msg.centered = True
        completion_msg.text.append("Nothing to remove.")
    else:
        completion_msg.text.insert(0, "The following actions were performed:")

    return completion_msg
