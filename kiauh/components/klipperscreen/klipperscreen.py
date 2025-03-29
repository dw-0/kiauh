# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
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
from components.klipperscreen import (
    KLIPPERSCREEN_BACKUP_DIR,
    KLIPPERSCREEN_DIR,
    KLIPPERSCREEN_ENV_DIR,
    KLIPPERSCREEN_INSTALL_SCRIPT,
    KLIPPERSCREEN_LOG_NAME,
    KLIPPERSCREEN_REPO,
    KLIPPERSCREEN_REQ_FILE,
    KLIPPERSCREEN_SERVICE_FILE,
    KLIPPERSCREEN_SERVICE_NAME,
    KLIPPERSCREEN_UPDATER_SECTION_NAME,
)
from components.moonraker.moonraker import Moonraker
from core.backup_manager.backup_manager import BackupManager
from core.constants import SYSTEMD
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from core.types.component_status import ComponentStatus
from utils.common import (
    check_install_dependencies,
    get_install_status,
)
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_with_sudo
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


def install_klipperscreen() -> None:
    Logger.print_status("Installing KlipperScreen ...")

    if not check_python_version(3, 7):
        return

    mr_instances = get_instances(Moonraker)
    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Moonraker not found! KlipperScreen will not properly work "
                "without a working Moonraker installation.",
                "\n\n",
                "KlipperScreens update manager configuration for Moonraker "
                "will not be added to any moonraker.conf.",
            ],
        )
        if not get_confirm(
            "Continue KlipperScreen installation?",
            default_choice=False,
            allow_go_back=True,
        ):
            return

    check_install_dependencies()

    git_clone_wrapper(KLIPPERSCREEN_REPO, KLIPPERSCREEN_DIR)

    try:
        run(KLIPPERSCREEN_INSTALL_SCRIPT.as_posix(), shell=True, check=True)
        if mr_instances:
            patch_klipperscreen_update_manager(mr_instances)
            InstanceManager.restart_all(mr_instances)
        else:
            Logger.print_info(
                "Moonraker is not installed! Cannot add "
                "KlipperScreen to update manager!"
            )
        Logger.print_ok("KlipperScreen successfully installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing KlipperScreen:\n{e}")
        return


def patch_klipperscreen_update_manager(instances: List[Moonraker]) -> None:
    add_config_section(
        section=KLIPPERSCREEN_UPDATER_SECTION_NAME,
        instances=instances,
        options=[
            ("type", "git_repo"),
            ("path", KLIPPERSCREEN_DIR.as_posix()),
            ("origin", KLIPPERSCREEN_REPO),
            ("managed_services", "KlipperScreen"),
            ("env", f"{KLIPPERSCREEN_ENV_DIR}/bin/python"),
            ("requirements", KLIPPERSCREEN_REQ_FILE.as_posix()),
            ("install_script", KLIPPERSCREEN_INSTALL_SCRIPT.as_posix()),
        ],
    )


def update_klipperscreen() -> None:
    if not KLIPPERSCREEN_DIR.exists():
        Logger.print_info("KlipperScreen does not seem to be installed! Skipping ...")
        return

    try:
        Logger.print_status("Updating KlipperScreen ...")

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "stop")

        settings = KiauhSettings()
        if settings.kiauh.backup_before_update:
            backup_klipperscreen_dir()

        git_pull_wrapper(KLIPPERSCREEN_DIR)

        install_python_requirements(KLIPPERSCREEN_ENV_DIR, KLIPPERSCREEN_REQ_FILE)

        cmd_sysctl_service(KLIPPERSCREEN_SERVICE_NAME, "start")

        Logger.print_ok("KlipperScreen updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating KlipperScreen:\n{e}")
        return


def get_klipperscreen_status() -> ComponentStatus:
    return get_install_status(
        KLIPPERSCREEN_DIR,
        KLIPPERSCREEN_ENV_DIR,
        files=[SYSTEMD.joinpath(KLIPPERSCREEN_SERVICE_NAME)],
    )


def remove_klipperscreen() -> None:
    Logger.print_status("Removing KlipperScreen ...")
    try:
        if KLIPPERSCREEN_DIR.exists():
            Logger.print_status("Removing KlipperScreen directory ...")
            shutil.rmtree(KLIPPERSCREEN_DIR)
            Logger.print_ok("KlipperScreen directory successfully removed!")
        else:
            Logger.print_warn("KlipperScreen directory not found!")

        if KLIPPERSCREEN_ENV_DIR.exists():
            Logger.print_status("Removing KlipperScreen environment ...")
            shutil.rmtree(KLIPPERSCREEN_ENV_DIR)
            Logger.print_ok("KlipperScreen environment successfully removed!")
        else:
            Logger.print_warn("KlipperScreen environment not found!")

        if KLIPPERSCREEN_SERVICE_FILE.exists():
            remove_system_service(KLIPPERSCREEN_SERVICE_NAME)

        logfile = Path(f"/tmp/{KLIPPERSCREEN_LOG_NAME}")
        if logfile.exists():
            Logger.print_status("Removing KlipperScreen log file ...")
            remove_with_sudo(logfile)
            Logger.print_ok("KlipperScreen log file successfully removed!")

        kl_instances: List[Klipper] = get_instances(Klipper)
        for instance in kl_instances:
            logfile = instance.base.log_dir.joinpath(KLIPPERSCREEN_LOG_NAME)
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if mr_instances:
            Logger.print_status("Removing KlipperScreen from update manager ...")
            remove_config_section("update_manager KlipperScreen", mr_instances)
            Logger.print_ok("KlipperScreen successfully removed from update manager!")

        Logger.print_ok("KlipperScreen successfully removed!")

    except Exception as e:
        Logger.print_error(f"Error removing KlipperScreen:\n{e}")


def backup_klipperscreen_dir() -> None:
    bm = BackupManager()
    bm.backup_directory(
        KLIPPERSCREEN_DIR.name,
        source=KLIPPERSCREEN_DIR,
        target=KLIPPERSCREEN_BACKUP_DIR,
    )
    bm.backup_directory(
        KLIPPERSCREEN_ENV_DIR.name,
        source=KLIPPERSCREEN_ENV_DIR,
        target=KLIPPERSCREEN_BACKUP_DIR,
    )
