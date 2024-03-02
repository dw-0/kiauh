#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #


import shutil
import subprocess
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client import ClientConfigData
from core.instance_manager.instance_manager import InstanceManager
from utils.filesystem_utils import remove_file, remove_config_section
from utils.logger import Logger


def run_client_config_removal(
    client_config: ClientConfigData,
    remove_moonraker_conf_section: bool,
    remove_printer_cfg_include: bool,
    kl_instances: List[Klipper],
    mr_instances: List[Moonraker],
) -> None:
    remove_client_config_dir(client_config)
    remove_client_config_symlink(client_config)
    if remove_moonraker_conf_section:
        remove_config_section(
            f"update_manager {client_config.get('name')}", mr_instances
        )
    if remove_printer_cfg_include:
        remove_config_section(client_config.get("printer_cfg_section"), kl_instances)


def remove_client_config_dir(client_config: ClientConfigData) -> None:
    Logger.print_status(f"Removing {client_config.get('name')} ...")
    client_config_dir = client_config.get("dir")
    if not client_config_dir.exists():
        Logger.print_info(f"'{client_config_dir}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(client_config_dir)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{client_config_dir}':\n{e}")


def remove_client_config_symlink(client_config: ClientConfigData) -> None:
    Logger.print_status(f"Removing {client_config.get('cfg_filename')} symlinks ...")
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    for instance in instances:
        Logger.print_status(f"Removing symlink from '{instance.cfg_file}' ...")
        try:
            remove_file(instance.cfg_dir.joinpath(client_config.get("cfg_filename")))
        except subprocess.CalledProcessError:
            Logger.print_error("Failed to remove symlink!")
