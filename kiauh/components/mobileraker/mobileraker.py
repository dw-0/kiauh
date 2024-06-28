# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from components.mobileraker import (
    MOBILERAKER_BACKUP_DIR,
    MOBILERAKER_DIR,
    MOBILERAKER_ENV,
    MOBILERAKER_REPO,
)
from components.moonraker.moonraker import Moonraker
from core.backup_manager.backup_manager import BackupManager
from core.instance_manager.instance_manager import InstanceManager
from core.settings.kiauh_settings import KiauhSettings
from utils.common import check_install_dependencies, get_install_status
from utils.config_utils import add_config_section, remove_config_section
from utils.constants import SYSTEMD
from utils.fs_utils import remove_with_sudo
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.logger import DialogType, Logger
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_manage,
    cmd_sysctl_service,
    install_python_requirements,
)
from utils.types import ComponentStatus


def install_mobileraker() -> None:
    Logger.print_status("Installing Mobileraker's companion ...")

    if not check_python_version(3, 7):
        return

    mr_im = InstanceManager(Moonraker)
    mr_instances = mr_im.instances
    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Moonraker not found! Mobileraker's companion will not properly work "
                "without a working Moonraker installation.",
                "Mobileraker's companion's update manager configuration for Moonraker "
                "will not be added to any moonraker.conf.",
            ],
        )
        if not get_confirm(
            "Continue Mobileraker's companion installation?",
            default_choice=False,
            allow_go_back=True,
        ):
            return

    package_list = ["git", "wget", "curl", "unzip", "dfu-util"]
    check_install_dependencies(package_list)

    git_clone_wrapper(MOBILERAKER_REPO, MOBILERAKER_DIR)

    try:
        script = f"{MOBILERAKER_DIR}/scripts/install.sh"
        run(script, shell=True, check=True)
        if mr_instances:
            patch_mobileraker_update_manager(mr_instances)
            mr_im.restart_all_instance()
        else:
            Logger.print_info(
                "Moonraker is not installed! Cannot add Mobileraker's "
                "companion to update manager!"
            )
        Logger.print_ok("Mobileraker's companion successfully installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing Mobileraker's companion:\n{e}")
        return


def patch_mobileraker_update_manager(instances: List[Moonraker]) -> None:
    env_py = f"{MOBILERAKER_ENV}/bin/python"
    add_config_section(
        section="update_manager mobileraker",
        instances=instances,
        options=[
            ("type", "git_repo"),
            ("path", "mobileraker_companion"),
            ("orgin", MOBILERAKER_REPO),
            ("primary_branch", "main"),
            ("managed_services", "mobileraker"),
            ("env", env_py),
            ("requirements", "scripts/mobileraker-requirements.txt"),
            ("install_script", "scripts/install.sh"),
        ],
    )


def update_mobileraker() -> None:
    try:
        if not MOBILERAKER_DIR.exists():
            Logger.print_info(
                "Mobileraker's companion does not seem to be installed! Skipping ..."
            )
            return

        Logger.print_status("Updating Mobileraker's companion ...")

        cmd_sysctl_service("mobileraker", "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            backup_mobileraker_dir()

        git_pull_wrapper(MOBILERAKER_REPO, MOBILERAKER_DIR)

        requirements = MOBILERAKER_DIR.joinpath("/scripts/mobileraker-requirements.txt")
        install_python_requirements(MOBILERAKER_ENV, requirements)

        cmd_sysctl_service("mobileraker", "start")

        Logger.print_ok("Mobileraker's companion updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating Mobileraker's companion:\n{e}")
        return


def get_mobileraker_status() -> ComponentStatus:
    return get_install_status(
        MOBILERAKER_DIR,
        MOBILERAKER_ENV,
        files=[SYSTEMD.joinpath("mobileraker.service")],
    )


def remove_mobileraker() -> None:
    Logger.print_status("Removing Mobileraker's companion ...")
    try:
        if MOBILERAKER_DIR.exists():
            Logger.print_status("Removing Mobileraker's companion directory ...")
            shutil.rmtree(MOBILERAKER_DIR)
            Logger.print_ok("Mobileraker's companion directory successfully removed!")
        else:
            Logger.print_warn("Mobileraker's companion directory not found!")

        if MOBILERAKER_ENV.exists():
            Logger.print_status("Removing Mobileraker's companion environment ...")
            shutil.rmtree(MOBILERAKER_ENV)
            Logger.print_ok("Mobileraker's companion environment successfully removed!")
        else:
            Logger.print_warn("Mobileraker's companion environment not found!")

        service = SYSTEMD.joinpath("mobileraker.service")
        if service.exists():
            Logger.print_status("Removing mobileraker service ...")
            cmd_sysctl_service(service, "stop")
            cmd_sysctl_service(service, "disable")
            remove_with_sudo(service)
            cmd_sysctl_manage("daemon-reload")
            cmd_sysctl_manage("reset-failed")
            Logger.print_ok("Mobileraker's companion service successfully removed!")

        kl_im = InstanceManager(Klipper)
        kl_instances: List[Klipper] = kl_im.instances
        for instance in kl_instances:
            logfile = instance.log_dir.joinpath("mobileraker.log")
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_im = InstanceManager(Moonraker)
        mr_instances: List[Moonraker] = mr_im.instances
        if mr_instances:
            Logger.print_status(
                "Removing Mobileraker's companion from update manager ..."
            )
            remove_config_section("update_manager mobileraker", mr_instances)
            Logger.print_ok(
                "Mobileraker's companion successfully removed from update manager!"
            )

        Logger.print_ok("Mobileraker's companion successfully removed!")

    except Exception as e:
        Logger.print_error(f"Error removing Mobileraker's companion:\n{e}")


def backup_mobileraker_dir() -> None:
    bm = BackupManager()
    bm.backup_directory(
        "mobileraker_companion",
        source=MOBILERAKER_DIR,
        target=MOBILERAKER_BACKUP_DIR,
    )
    bm.backup_directory(
        "mobileraker-env",
        source=MOBILERAKER_ENV,
        target=MOBILERAKER_BACKUP_DIR,
    )
