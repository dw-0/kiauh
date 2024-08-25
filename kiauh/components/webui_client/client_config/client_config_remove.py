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
from utils.config_utils import remove_config_section
from utils.fs_utils import run_remove_routines
from utils.instance_utils import get_instances


def run_client_config_removal(
    client_config: BaseWebClientConfig,
    kl_instances: List[Klipper],
    mr_instances: List[Moonraker],
) -> None:
    remove_client_config_dir(client_config)
    remove_client_config_symlink(client_config)
    remove_config_section(f"update_manager {client_config.name}", mr_instances)
    remove_config_section(client_config.config_section, kl_instances)


def remove_client_config_dir(client_config: BaseWebClientConfig) -> None:
    Logger.print_status(f"Removing {client_config.display_name} ...")
    run_remove_routines(client_config.config_dir)


def remove_client_config_symlink(client_config: BaseWebClientConfig) -> None:
    instances: List[Klipper] = get_instances(Klipper)
    for instance in instances:
        run_remove_routines(
            instance.base.cfg_dir.joinpath(client_config.config_filename)
        )
