# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import BaseWebClient, BaseWebClientConfig
from components.webui_client.client_dialogs import (
    print_client_already_installed_dialog,
)
from components.webui_client.client_utils import (
    backup_client_config_data,
    detect_client_cfg_conflict,
)
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from core.settings.kiauh_settings import KiauhSettings
from utils.common import backup_printer_config_dir
from utils.config_utils import add_config_section, add_config_section_at_top
from utils.fs_utils import create_symlink
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances


def install_client_config(client_data: BaseWebClient, cfg_backup=True) -> None:
    client_config: BaseWebClientConfig = client_data.client_config
    display_name = client_config.display_name

    if detect_client_cfg_conflict(client_data):
        Logger.print_info("Another Client-Config is already installed! Skipped ...")
        return

    if client_config.config_dir.exists():
        print_client_already_installed_dialog(display_name)
        if get_confirm(f"Re-install {display_name}?", allow_go_back=True):
            shutil.rmtree(client_config.config_dir)
        else:
            return

    mr_instances: List[Moonraker] = get_instances(Moonraker)
    kl_instances = get_instances(Klipper)

    try:
        download_client_config(client_config)
        create_client_config_symlink(client_config, kl_instances)

        if cfg_backup:
            backup_printer_config_dir()

        add_config_section(
            section=f"update_manager {client_config.name}",
            instances=mr_instances,
            options=[
                ("type", "git_repo"),
                ("primary_branch", "master"),
                ("path", str(client_config.config_dir)),
                ("origin", str(client_config.repo_url)),
                ("managed_services", "klipper"),
            ],
        )
        add_config_section_at_top(client_config.config_section, kl_instances)
        InstanceManager.restart_all(kl_instances)

    except Exception as e:
        Logger.print_error(f"{display_name} installation failed!\n{e}")
        return

    Logger.print_ok(f"{display_name} installation complete!", start="\n")


def download_client_config(client_config: BaseWebClientConfig) -> None:
    try:
        Logger.print_status(f"Downloading {client_config.display_name} ...")
        repo = client_config.repo_url
        target_dir = client_config.config_dir
        git_clone_wrapper(repo, target_dir)
    except Exception:
        Logger.print_error(f"Downloading {client_config.display_name} failed!")
        raise


def update_client_config(client: BaseWebClient) -> None:
    client_config: BaseWebClientConfig = client.client_config

    Logger.print_status(f"Updating {client_config.display_name} ...")

    if not client_config.config_dir.exists():
        Logger.print_info(
            f"Unable to update {client_config.display_name}. Directory does not exist! Skipping ..."
        )
        return

    settings = KiauhSettings()
    if settings.kiauh.backup_before_update:
        backup_client_config_data(client)

    git_pull_wrapper(client_config.config_dir)

    Logger.print_ok(f"Successfully updated {client_config.display_name}.")
    Logger.print_info("Restart Klipper to reload the configuration!")


def create_client_config_symlink(
    client_config: BaseWebClientConfig, klipper_instances: List[Klipper]
) -> None:
    for instance in klipper_instances:
        Logger.print_status(f"Create symlink for {client_config.config_filename} ...")
        source = Path(client_config.config_dir, client_config.config_filename)
        target = instance.base.cfg_dir
        Logger.print_status(f"Linking {source} to {target}")
        try:
            create_symlink(source, target)
        except subprocess.CalledProcessError:
            Logger.print_error("Creating symlink failed!")
