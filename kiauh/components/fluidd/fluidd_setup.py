#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import subprocess
from pathlib import Path
from typing import List

from components.fluidd import (
    FLUIDD_URL,
    FLUIDD_CONFIG_REPO_URL,
    FLUIDD_CONFIG_DIR,
    FLUIDD_DIR,
    MODULE_PATH,
)
from components.fluidd.fluidd_dialogs import (
    print_fluidd_already_installed_dialog,
    print_install_fluidd_config_dialog,
    print_fluidd_port_select_dialog,
    print_moonraker_not_found_dialog,
)
from components.fluidd.fluidd_utils import symlink_webui_nginx_log
from kiauh import KIAUH_CFG
from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from core.repo_manager.repo_manager import RepoManager
from utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from utils.common import check_install_dependencies
from utils.filesystem_utils import (
    unzip,
    copy_upstream_nginx_cfg,
    copy_common_vars_nginx_cfg,
    create_nginx_cfg,
    create_symlink,
    remove_file,
    read_ports_from_nginx_configs,
    get_next_free_port, is_valid_port,
    )
from utils.input_utils import get_confirm, get_number_input
from utils.logger import Logger
from utils.system_utils import (
    download_file,
    set_nginx_permissions,
    get_ipv4_addr,
    control_systemd_service,
)


def install_fluidd() -> None:
    mr_im = InstanceManager(Moonraker)
    mr_instances: List[Moonraker] = mr_im.instances

    if not mr_instances:
        print_moonraker_not_found_dialog()
        if not get_confirm("Continue Fluidd installation?", allow_go_back=True):
            return

    if Path.home().joinpath("fluidd").exists():
        print_fluidd_already_installed_dialog()
        do_reinstall = get_confirm("Re-install Fluidd?", allow_go_back=True)
        if not do_reinstall:
            return

    kl_im = InstanceManager(Klipper)
    kl_instances = kl_im.instances
    install_fl_config = False
    if kl_instances:
        print_install_fluidd_config_dialog()
        question = "Download the recommended macros?"
        install_fl_config = get_confirm(question, allow_go_back=False)

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    fluidd_port = cm.get_value("fluidd", "port")
    ports_in_use = read_ports_from_nginx_configs()

    # check if configured port is a valid number and not in use already
    valid_port = is_valid_port(fluidd_port, ports_in_use)
    while not valid_port:
        next_port = get_next_free_port(ports_in_use)
        print_fluidd_port_select_dialog(next_port, ports_in_use)
        fluidd_port = str(get_number_input(
            "Configure Fluidd for port",
            min_count=int(next_port),
            default=next_port,
        ))
        valid_port = is_valid_port(fluidd_port, ports_in_use)

    check_install_dependencies(["nginx"])

    try:
        download_fluidd()
        if mr_instances:
            patch_moonraker_conf(
                mr_instances,
                "Fluidd",
                "update_manager fluidd",
                "fluidd-updater.conf",
            )
            mr_im.restart_all_instance()
        if install_fl_config and kl_instances:
            download_fluidd_cfg()
            create_fluidd_cfg_symlink(kl_instances)
            patch_moonraker_conf(
                mr_instances,
                "fluidd-config",
                "update_manager fluidd-config",
                "fluidd-config-updater.conf",
            )
            patch_printer_config(kl_instances)
            kl_im.restart_all_instance()

        copy_upstream_nginx_cfg()
        copy_common_vars_nginx_cfg()
        create_fluidd_nginx_cfg(fluidd_port)
        if kl_instances:
            symlink_webui_nginx_log(kl_instances)
        control_systemd_service("nginx", "restart")

    except Exception as e:
        Logger.print_error(f"Fluidd installation failed!\n{e}")
        return

    log = f"Open Fluidd now on: http://{get_ipv4_addr()}:{fluidd_port}"
    Logger.print_ok("Fluidd installation complete!", start="\n")
    Logger.print_ok(log, prefix=False, end="\n\n")


def download_fluidd() -> None:
    try:
        Logger.print_status("Downloading Fluidd ...")
        target = Path.home().joinpath("fluidd.zip")
        download_file(FLUIDD_URL, target, True)
        Logger.print_ok("Download complete!")

        Logger.print_status("Extracting fluidd.zip ...")
        unzip(Path.home().joinpath("fluidd.zip"), FLUIDD_DIR)
        target.unlink(missing_ok=True)
        Logger.print_ok("OK!")

    except Exception:
        Logger.print_error("Downloading Fluidd failed!")
        raise


def update_fluidd() -> None:
    Logger.print_status("Updating Fluidd ...")
    download_fluidd()


def download_fluidd_cfg() -> None:
    try:
        Logger.print_status("Downloading fluidd-config ...")
        rm = RepoManager(FLUIDD_CONFIG_REPO_URL, target_dir=FLUIDD_CONFIG_DIR)
        rm.clone_repo()
    except Exception:
        Logger.print_error("Downloading fluidd-config failed!")
        raise


def create_fluidd_cfg_symlink(klipper_instances: List[Klipper]) -> None:
    Logger.print_status("Create symlink of fluidd.cfg ...")
    source = Path(FLUIDD_CONFIG_DIR, "fluidd.cfg")
    for instance in klipper_instances:
        target = instance.cfg_dir
        Logger.print_status(f"Linking {source} to {target}")
        try:
            create_symlink(source, target)
        except subprocess.CalledProcessError:
            Logger.print_error("Creating symlink failed!")


def create_fluidd_nginx_cfg(port: int) -> None:
    root_dir = FLUIDD_DIR
    source = NGINX_SITES_AVAILABLE.joinpath("fluidd")
    target = NGINX_SITES_ENABLED.joinpath("fluidd")
    try:
        Logger.print_status("Creating NGINX config for Fluidd ...")
        remove_file(Path("/etc/nginx/sites-enabled/default"), True)
        create_nginx_cfg("fluidd", port, root_dir)
        create_symlink(source, target, True)
        set_nginx_permissions()
        Logger.print_ok("NGINX config for Fluidd successfully created.")
    except Exception:
        Logger.print_error("Creating NGINX config for Fluidd failed!")
        raise


# TODO: could be fully extracted, its webui agnostic, and used for mainsail and fluidd
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
        if cm.config.has_section(section_name):
            Logger.print_info("Section already exist. Skipped ...")
            return

        template = MODULE_PATH.joinpath("assets", template_file)
        with open(template, "r") as t:
            template_content = "\n"
            template_content += t.read()

        with open(cfg_file, "a") as f:
            f.write(template_content)


# TODO: could be made fully webui agnostic and extracted, and used for mainsail and fluidd
def patch_printer_config(klipper_instances: List[Klipper]) -> None:
    for instance in klipper_instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Including fluidd-config in '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            return

        cm = ConfigManager(cfg_file)
        if cm.config.has_section("include fluidd.cfg"):
            Logger.print_info("Section already exist. Skipped ...")
            return

        with open(cfg_file, "a") as f:
            f.write("\n[include fluidd.cfg]")
