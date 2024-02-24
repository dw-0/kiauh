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
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from components.fluidd import FLUIDD_DIR, FLUIDD_CONFIG_DIR
from components.moonraker.moonraker import Moonraker
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from utils.filesystem_utils import remove_file
from utils.logger import Logger


def run_fluidd_removal(
    remove_fluidd: bool,
    remove_fl_config: bool,
    remove_mr_updater_section: bool,
    remove_flc_printer_cfg_include: bool,
) -> None:
    if remove_fluidd:
        remove_fluidd_dir()
        remove_nginx_config()
        remove_nginx_logs()
        if remove_mr_updater_section:
            remove_updater_section("update_manager fluidd")
    if remove_fl_config:
        remove_fluidd_cfg_dir()
        remove_fluidd_cfg_symlink()
        if remove_mr_updater_section:
            remove_updater_section("update_manager fluidd-config")
        if remove_flc_printer_cfg_include:
            remove_printer_cfg_include()


def remove_fluidd_dir() -> None:
    Logger.print_status("Removing Fluidd ...")
    if not FLUIDD_DIR.exists():
        Logger.print_info(f"'{FLUIDD_DIR}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(FLUIDD_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{FLUIDD_DIR}':\n{e}")


def remove_nginx_config() -> None:
    Logger.print_status("Removing Fluidd NGINX config ...")
    try:
        remove_file(NGINX_SITES_AVAILABLE.joinpath("fluidd"), True)
        remove_file(NGINX_SITES_ENABLED.joinpath("fluidd"), True)

    except subprocess.CalledProcessError as e:
        log = f"Unable to remove Fluidd NGINX config:\n{e.stderr.decode()}"
        Logger.print_error(log)


def remove_nginx_logs() -> None:
    Logger.print_status("Removing Fluidd NGINX logs ...")
    try:
        remove_file(Path("/var/log/nginx/fluidd-access.log"), True)
        remove_file(Path("/var/log/nginx/fluidd-error.log"), True)

        im = InstanceManager(Klipper)
        instances: List[Klipper] = im.instances
        if not instances:
            return

        for instance in instances:
            remove_file(instance.log_dir.joinpath("fluidd-access.log"))
            remove_file(instance.log_dir.joinpath("fluidd-error.log"))

    except (OSError, subprocess.CalledProcessError) as e:
        Logger.print_error(f"Unable to NGINX logs:\n{e}")


def remove_updater_section(name: str) -> None:
    Logger.print_status("Remove updater section from moonraker.conf ...")
    im = InstanceManager(Moonraker)
    instances: List[Moonraker] = im.instances
    if not instances:
        Logger.print_info("Moonraker not installed. Skipped ...")
        return

    for instance in instances:
        Logger.print_status(f"Remove section '{name}' in '{instance.cfg_file}' ...")

        if not instance.cfg_file.is_file():
            Logger.print_info(f"'{instance.cfg_file}' does not exist. Skipped ...")
            continue

        cm = ConfigManager(instance.cfg_file)
        if not cm.config.has_section(name):
            Logger.print_info("Section not present. Skipped ...")
            continue

        cm.config.remove_section(name)
        cm.write_config()


def remove_fluidd_cfg_dir() -> None:
    Logger.print_status("Removing fluidd-config ...")
    if not FLUIDD_CONFIG_DIR.exists():
        Logger.print_info(f"'{FLUIDD_CONFIG_DIR}' does not exist. Skipping ...")
        return

    try:
        shutil.rmtree(FLUIDD_CONFIG_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{FLUIDD_CONFIG_DIR}':\n{e}")


def remove_fluidd_cfg_symlink() -> None:
    Logger.print_status("Removing fluidd.cfg symlinks ...")
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    for instance in instances:
        Logger.print_status(f"Removing symlink from '{instance.cfg_file}' ...")
        try:
            remove_file(instance.cfg_dir.joinpath("fluidd.cfg"))
        except subprocess.CalledProcessError:
            Logger.print_error("Failed to remove symlink!")


def remove_printer_cfg_include() -> None:
    Logger.print_status("Remove fluidd-config include from printer.cfg ...")
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    if not instances:
        Logger.print_info("Klipper not installed. Skipping ...")
        return

    for instance in instances:
        log = f"Removing include from '{instance.cfg_file}' ..."
        Logger.print_status(log)

        if not instance.cfg_file.is_file():
            continue

        cm = ConfigManager(instance.cfg_file)
        if not cm.config.has_section("include fluidd.cfg"):
            Logger.print_info("Section not present. Skipped ...")
            continue

        cm.config.remove_section("include fluidd.cfg")
        cm.write_config()
