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
    MOBILERAKER_ENV_DIR,
    MOBILERAKER_INSTALL_SCRIPT,
    MOBILERAKER_LOG_NAME,
    MOBILERAKER_REPO,
    MOBILERAKER_REQ_FILE,
    MOBILERAKER_SERVICE_FILE,
    MOBILERAKER_SERVICE_NAME,
    MOBILERAKER_UPDATER_SECTION_NAME,
)
from components.moonraker.moonraker import Moonraker
from core.backup_manager.backup_manager import BackupManager
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from core.types import ComponentStatus
from utils.common import check_install_dependencies, get_install_status
from utils.config_utils import add_config_section, remove_config_section
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_service,
    install_python_requirements,
    remove_system_service,
)


def install_mobileraker() -> None:
    Logger.print_status("Installing Mobileraker's companion ...")

    if not check_python_version(3, 7):
        return

    mr_instances = get_instances(Moonraker)
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

    check_install_dependencies()

    git_clone_wrapper(MOBILERAKER_REPO, MOBILERAKER_DIR)

    try:
        run(MOBILERAKER_INSTALL_SCRIPT.as_posix(), shell=True, check=True)
        if mr_instances:
            patch_mobileraker_update_manager(mr_instances)
            InstanceManager.restart_all(mr_instances)
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
    add_config_section(
        section=MOBILERAKER_UPDATER_SECTION_NAME,
        instances=instances,
        options=[
            ("type", "git_repo"),
            ("path", MOBILERAKER_DIR.as_posix()),
            ("origin", MOBILERAKER_REPO),
            ("primary_branch", "main"),
            ("managed_services", "mobileraker"),
            ("env", f"{MOBILERAKER_ENV_DIR}/bin/python"),
            ("requirements", MOBILERAKER_REQ_FILE.as_posix()),
            ("install_script", MOBILERAKER_INSTALL_SCRIPT.as_posix()),
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

        cmd_sysctl_service(MOBILERAKER_SERVICE_NAME, "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            backup_mobileraker_dir()

        git_pull_wrapper(MOBILERAKER_REPO, MOBILERAKER_DIR)

        install_python_requirements(MOBILERAKER_ENV_DIR, MOBILERAKER_REQ_FILE)

        cmd_sysctl_service(MOBILERAKER_SERVICE_NAME, "start")

        Logger.print_ok("Mobileraker's companion updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating Mobileraker's companion:\n{e}")
        return


def get_mobileraker_status() -> ComponentStatus:
    return get_install_status(
        MOBILERAKER_DIR,
        MOBILERAKER_ENV_DIR,
        files=[MOBILERAKER_SERVICE_FILE],
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

        if MOBILERAKER_ENV_DIR.exists():
            Logger.print_status("Removing Mobileraker's companion environment ...")
            shutil.rmtree(MOBILERAKER_ENV_DIR)
            Logger.print_ok("Mobileraker's companion environment successfully removed!")
        else:
            Logger.print_warn("Mobileraker's companion environment not found!")

        if MOBILERAKER_SERVICE_FILE.exists():
            remove_system_service(MOBILERAKER_SERVICE_NAME)

        kl_instances: List[Klipper] = get_instances(Klipper)
        for instance in kl_instances:
            logfile = instance.base.log_dir.joinpath(MOBILERAKER_LOG_NAME)
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if mr_instances:
            Logger.print_status(
                "Removing Mobileraker's companion from update manager ..."
            )
            remove_config_section(MOBILERAKER_UPDATER_SECTION_NAME, mr_instances)
            Logger.print_ok(
                "Mobileraker's companion successfully removed from update manager!"
            )

        Logger.print_ok("Mobileraker's companion successfully removed!")

    except Exception as e:
        Logger.print_error(f"Error removing Mobileraker's companion:\n{e}")


def backup_mobileraker_dir() -> None:
    bm = BackupManager()
    bm.backup_directory(
        MOBILERAKER_DIR.name,
        source=MOBILERAKER_DIR,
        target=MOBILERAKER_BACKUP_DIR,
    )
    bm.backup_directory(
        MOBILERAKER_ENV_DIR.name,
        source=MOBILERAKER_ENV_DIR,
        target=MOBILERAKER_BACKUP_DIR,
    )
