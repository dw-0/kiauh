#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import json
import os.path
import shutil
from pathlib import Path
from typing import List

from kiauh import KIAUH_CFG
from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.mainsail import (
    MAINSAIL_URL,
    MAINSAIL_DIR,
    MAINSAIL_CONFIG_DIR,
    MAINSAIL_CONFIG_REPO_URL,
    MAINSAIL_CONFIG_JSON,
    MODULE_PATH,
)
from kiauh.modules.mainsail.mainsail_dialogs import (
    print_moonraker_not_found_dialog,
    print_mainsail_already_installed_dialog,
    print_install_mainsail_config_dialog,
    print_mainsail_port_select_dialog,
)
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils.common import check_install_dependencies
from kiauh.utils.input_utils import get_confirm, get_number_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    download_file,
    unzip,
    create_upstream_nginx_cfg,
    create_nginx_cfg,
    delete_default_nginx_cfg,
    enable_nginx_cfg,
    set_nginx_permissions,
    get_ipv4_addr,
    control_systemd_service,
    create_common_vars_nginx_cfg,
)


def run_mainsail_setup(install: bool) -> None:
    im_mr = InstanceManager(Moonraker)
    is_moonraker_installed = len(im_mr.instances) > 0

    enable_remotemode = False
    if not is_moonraker_installed:
        print_moonraker_not_found_dialog()
        do_continue = get_confirm("Continue Mainsail installation?", allow_go_back=True)
        if do_continue:
            enable_remotemode = True
        else:
            return

    is_mainsail_installed = Path(f"{Path.home()}/mainsail").exists()
    do_reinstall = False
    if is_mainsail_installed:
        print_mainsail_already_installed_dialog()
        do_reinstall = get_confirm("Re-install Mainsail?", allow_go_back=True)
        if do_reinstall:
            backup_config_json()
        else:
            return

    im_kl = InstanceManager(Klipper)
    is_klipper_installed = len(im_kl.instances) > 0
    install_ms_config = False
    if is_klipper_installed:
        print_install_mainsail_config_dialog()
        question = "Download the recommended macros?"
        install_ms_config = get_confirm(question, allow_go_back=False)

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    cm.read_config()
    default_port = cm.get_value("mainsail", "default_port")
    mainsail_port = default_port if default_port else 80
    if not default_port:
        print_mainsail_port_select_dialog(f"{mainsail_port}")
        mainsail_port = get_number_input(
            "Configure Mainsail for port",
            min_count=mainsail_port,
            default=mainsail_port,
        )

    check_install_dependencies(["nginx"])

    try:
        download_mainsail()
        if do_reinstall:
            restore_config_json()
        if enable_remotemode:
            enable_mainsail_remotemode()
        if is_moonraker_installed:
            patch_moonraker_conf(
                im_mr.instances,
                "Mainsail",
                "update_manager mainsail",
                "mainsail-updater.conf",
            )
            im_mr.restart_all_instance()
        if is_klipper_installed and install_ms_config:
            download_mainsail_config()
            patch_moonraker_conf(
                im_mr.instances,
                "mainsail-config",
                "update_manager mainsail-config",
                "mainsail-config-updater.conf",
            )
            patch_printer_config(im_kl.instances)
            im_kl.restart_all_instance()

        create_upstream_nginx_cfg()
        create_common_vars_nginx_cfg()
        create_mainsail_nginx_cfg(mainsail_port)
        if is_klipper_installed:
            symlink_webui_nginx_log(im_kl.instances)
        control_systemd_service("nginx", "restart")

    except Exception as e:
        Logger.print_error(f"Mainsail installation failed!\n{e}")
        return

    log = f"Open Mainsail now on: http://{get_ipv4_addr()}:{mainsail_port}"
    Logger.print_ok("Mainsail installation complete!", start="\n")
    Logger.print_ok(log, prefix=False, end="\n\n")


def download_mainsail() -> None:
    try:
        Logger.print_status("Downloading Mainsail ...")
        download_file(MAINSAIL_URL, f"{Path.home()}", "mainsail.zip")
        Logger.print_ok("Download complete!")

        Logger.print_status("Extracting mainsail.zip ...")
        unzip(f"{Path.home()}/mainsail.zip", MAINSAIL_DIR)
        Logger.print_ok("OK!")

    except Exception:
        Logger.print_error("Downloading Mainsail failed!")
        raise


def download_mainsail_config() -> None:
    try:
        Logger.print_status("Downloading mainsail-config ...")
        rm = RepoManager(MAINSAIL_CONFIG_REPO_URL, target_dir=MAINSAIL_CONFIG_DIR)
        rm.clone_repo()
    except Exception:
        Logger.print_error("Downloading mainsail-config failed!")
        raise


def create_mainsail_nginx_cfg(port: int) -> None:
    try:
        Logger.print_status("Creating NGINX config for Mainsail ...")
        root_dir = MAINSAIL_DIR
        delete_default_nginx_cfg()
        create_nginx_cfg("mainsail", port, root_dir)
        enable_nginx_cfg("mainsail")
        set_nginx_permissions()
        Logger.print_ok("NGINX config for Mainsail successfully created.")
    except Exception:
        Logger.print_error("Creating NGINX config for Mainsail failed!")
        raise


def symlink_webui_nginx_log(klipper_instances: List[Klipper]) -> None:
    Logger.print_status("Link NGINX logs into log directory ...")
    access_log = Path("/var/log/nginx/mainsail-access.log")
    error_log = Path("/var/log/nginx/mainsail-error.log")

    for instance in klipper_instances:
        desti_access = Path(instance.log_dir).joinpath("mainsail-access.log")
        if not desti_access.exists():
            desti_access.symlink_to(access_log)

        desti_error = Path(instance.log_dir).joinpath("mainsail-error.log")
        if not desti_error.exists():
            desti_error.symlink_to(error_log)


def patch_moonraker_conf(
    moonraker_instances: List[Moonraker],
    name: str,
    section_name: str,
    template_file: str,
) -> None:
    for instance in moonraker_instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Add {name} update section to '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            return

        cm = ConfigManager(cfg_file)
        cm.read_config()
        if cm.config.has_section(section_name):
            Logger.print_info("Section already exist. Skipped ...")
            return

        template = os.path.join(MODULE_PATH, "res", template_file)
        with open(template, "r") as t:
            template_content = "\n"
            template_content += t.read()

        with open(cfg_file, "a") as f:
            f.write(template_content)


def patch_printer_config(klipper_instances: List[Klipper]) -> None:
    for instance in klipper_instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Including mainsail-config in '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            return

        cm = ConfigManager(cfg_file)
        cm.read_config()
        if cm.config.has_section("include mainsail.cfg"):
            Logger.print_info("Section already exist. Skipped ...")
            return

        with open(cfg_file, "a") as f:
            f.write("\n[include mainsail.cfg]")


def backup_config_json() -> None:
    try:
        Logger.print_status(f"Backup '{MAINSAIL_CONFIG_JSON}' ...")
        target = os.path.join(Path.home(), "config.json.kiauh.bak")
        shutil.copy(MAINSAIL_CONFIG_JSON, target)
    except OSError:
        Logger.print_info(f"Unable to backup config.json. Skipped ...")


def restore_config_json() -> None:
    try:
        Logger.print_status(f"Restore '{MAINSAIL_CONFIG_JSON}' ...")
        source = os.path.join(Path.home(), "config.json.kiauh.bak")
        shutil.copy(source, MAINSAIL_CONFIG_JSON)
    except OSError:
        Logger.print_info(f"Unable to restore config.json. Skipped ...")


def enable_mainsail_remotemode() -> None:
    with open(MAINSAIL_CONFIG_JSON, "r") as f:
        config_data = json.load(f)

    if config_data["instancesDB"] == "browser":
        return

    Logger.print_status("Setting instance storage location to 'browser' ...")
    config_data["instancesDB"] = "browser"

    with open(MAINSAIL_CONFIG_JSON, "w") as f:
        json.dump(config_data, f, indent=4)
