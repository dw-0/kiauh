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

from kiauh import KIAUH_CFG
from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.components.klipper.klipper import Klipper
from kiauh.components.mainsail import (
    MAINSAIL_URL,
    MAINSAIL_DIR,
    MAINSAIL_CONFIG_DIR,
    MAINSAIL_CONFIG_REPO_URL,
    MODULE_PATH,
)
from kiauh.components.mainsail.mainsail_dialogs import (
    print_moonraker_not_found_dialog,
    print_mainsail_already_installed_dialog,
    print_install_mainsail_config_dialog,
    print_mainsail_port_select_dialog,
)
from kiauh.components.mainsail.mainsail_utils import (
    restore_config_json,
    enable_mainsail_remotemode,
    backup_config_json,
    symlink_webui_nginx_log,
)
from kiauh.components.moonraker.moonraker import Moonraker
from kiauh.utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from kiauh.utils.common import check_install_dependencies
from kiauh.utils.filesystem_utils import (
    unzip,
    copy_upstream_nginx_cfg,
    copy_common_vars_nginx_cfg,
    create_nginx_cfg,
    create_symlink,
    remove_file,
)
from kiauh.utils.input_utils import get_confirm, get_number_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    download_file,
    set_nginx_permissions,
    get_ipv4_addr,
    control_systemd_service,
)


def install_mainsail() -> None:
    mr_im = InstanceManager(Moonraker)
    mr_instances: List[Moonraker] = mr_im.instances

    enable_remotemode = False
    if not mr_instances:
        print_moonraker_not_found_dialog()
        if not get_confirm("Continue Mainsail installation?", allow_go_back=True):
            return

    # if moonraker is not installed or multiple instances
    # are installed we enable mainsails remote mode
    if not mr_instances or len(mr_instances) > 1:
        enable_remotemode = True

    do_reinstall = False
    if Path.home().joinpath("mainsail").exists():
        print_mainsail_already_installed_dialog()
        do_reinstall = get_confirm("Re-install Mainsail?", allow_go_back=True)
        if do_reinstall:
            backup_config_json(is_temp=True)
        else:
            return

    kl_im = InstanceManager(Klipper)
    kl_instances = kl_im.instances
    install_ms_config = False
    if kl_instances:
        print_install_mainsail_config_dialog()
        question = "Download the recommended macros?"
        install_ms_config = get_confirm(question, allow_go_back=False)

    # if a default port is configured in the kiauh.cfg, we use that for the port
    # otherwise we default to port 80, but show the user a dialog to confirm/change that port
    cm = ConfigManager(cfg_file=KIAUH_CFG)
    default_port = cm.get_value("mainsail", "default_port")
    is_valid_port = default_port and default_port.isdigit()
    mainsail_port = default_port if is_valid_port else "80"
    if not is_valid_port:
        print_mainsail_port_select_dialog(mainsail_port)
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
        if mr_instances:
            patch_moonraker_conf(
                mr_instances,
                "Mainsail",
                "update_manager mainsail",
                "mainsail-updater.conf",
            )
            mr_im.restart_all_instance()
        if install_ms_config and kl_instances:
            download_mainsail_cfg()
            create_mainsail_cfg_symlink(kl_instances)
            patch_moonraker_conf(
                mr_instances,
                "mainsail-config",
                "update_manager mainsail-config",
                "mainsail-config-updater.conf",
            )
            patch_printer_config(kl_instances)
            kl_im.restart_all_instance()

        copy_upstream_nginx_cfg()
        copy_common_vars_nginx_cfg()
        create_mainsail_nginx_cfg(mainsail_port)
        if kl_instances:
            symlink_webui_nginx_log(kl_instances)
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
        target = Path.home().joinpath("mainsail.zip")
        download_file(MAINSAIL_URL, target, True)
        Logger.print_ok("Download complete!")

        Logger.print_status("Extracting mainsail.zip ...")
        unzip(Path.home().joinpath("mainsail.zip"), MAINSAIL_DIR)
        target.unlink(missing_ok=True)
        Logger.print_ok("OK!")

    except Exception:
        Logger.print_error("Downloading Mainsail failed!")
        raise


def update_mainsail() -> None:
    Logger.print_status("Updating Mainsail ...")
    backup_config_json(is_temp=True)
    download_mainsail()
    restore_config_json()


def download_mainsail_cfg() -> None:
    try:
        Logger.print_status("Downloading mainsail-config ...")
        rm = RepoManager(MAINSAIL_CONFIG_REPO_URL, target_dir=MAINSAIL_CONFIG_DIR)
        rm.clone_repo()
    except Exception:
        Logger.print_error("Downloading mainsail-config failed!")
        raise


def create_mainsail_cfg_symlink(klipper_instances: List[Klipper]) -> None:
    Logger.print_status("Create symlink of mainsail.cfg ...")
    source = Path(MAINSAIL_CONFIG_DIR, "mainsail.cfg")
    for instance in klipper_instances:
        target = instance.cfg_dir
        Logger.print_status(f"Linking {source} to {target}")
        try:
            create_symlink(source, target)
        except subprocess.CalledProcessError:
            Logger.print_error("Creating symlink failed!")


def create_mainsail_nginx_cfg(port: int) -> None:
    root_dir = MAINSAIL_DIR
    source = NGINX_SITES_AVAILABLE.joinpath("mainsail")
    target = NGINX_SITES_ENABLED.joinpath("mainsail")
    try:
        Logger.print_status("Creating NGINX config for Mainsail ...")
        remove_file(Path("/etc/nginx/sites-enabled/default"), True)
        create_nginx_cfg("mainsail", port, root_dir)
        create_symlink(source, target, True)
        set_nginx_permissions()
        Logger.print_ok("NGINX config for Mainsail successfully created.")
    except Exception:
        Logger.print_error("Creating NGINX config for Mainsail failed!")
        raise


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


def patch_printer_config(klipper_instances: List[Klipper]) -> None:
    for instance in klipper_instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Including mainsail-config in '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            return

        cm = ConfigManager(cfg_file)
        if cm.config.has_section("include mainsail.cfg"):
            Logger.print_info("Section already exist. Skipped ...")
            return

        with open(cfg_file, "a") as f:
            f.write("\n[include mainsail.cfg]")
