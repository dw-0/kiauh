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
from subprocess import run, CalledProcessError
from typing import List, Dict, Literal, Union

from components.klipper.klipper import Klipper
from components.klipperscreen import (
    KLIPPERSCREEN_DIR,
    KLIPPERSCREEN_REPO,
    KLIPPERSCREEN_ENV,
    KLIPPERSCREEN_BACKUP_DIR,
)
from components.moonraker.moonraker import Moonraker
from core.backup_manager.backup_manager import BackupManager
from core.instance_manager.instance_manager import InstanceManager
from core.settings.kiauh_settings import KiauhSettings
from utils.common import get_install_status, check_install_dependencies
from utils.config_utils import add_config_section, remove_config_section
from utils.constants import SYSTEMD
from utils.fs_utils import remove_with_sudo
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
    get_repo_name,
    get_local_commit,
    get_remote_commit,
)
from utils.input_utils import get_confirm
from utils.logger import Logger
from utils.sys_utils import (
    check_python_version,
    control_systemd_service,
    install_python_requirements,
)


def install_klipperscreen() -> None:
    Logger.print_status("Installing KlipperScreen ...")

    if not check_python_version(3, 7):
        return

    mr_im = InstanceManager(Moonraker)
    mr_instances = mr_im.instances
    if not mr_instances:
        # TODO: add moonraker not found dialog
        print("Moonraker not found!")
        if not get_confirm(
            "Continue KlipperScreen installation?",
            allow_go_back=True,
        ):
            return

    package_list = ["wget", "curl", "unzip", "dfu-util"]
    check_install_dependencies(package_list)

    git_clone_wrapper(KLIPPERSCREEN_REPO, KLIPPERSCREEN_DIR)

    try:
        script = f"{KLIPPERSCREEN_DIR}/scripts/KlipperScreen-install.sh"
        run(script, shell=True, check=True)
        if mr_instances:
            patch_klipperscreen_update_manager(mr_instances)
            mr_im.restart_all_instance()
        else:
            Logger.print_info(
                "Moonraker is not installed! Cannot add KlipperScreen to update manager!"
            )
        Logger.print_ok("KlipperScreen successfully installed!")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing KlipperScreen:\n{e}")
        return


def patch_klipperscreen_update_manager(instances: List[Moonraker]) -> None:
    env_py = f"{KLIPPERSCREEN_ENV}/bin/python"
    add_config_section(
        section="update_manager KlipperScreen",
        instances=instances,
        options=[
            ("type", "git_repo"),
            ("path", str(KLIPPERSCREEN_DIR)),
            ("orgin", KLIPPERSCREEN_REPO),
            ("env", env_py),
            ("requirements", "scripts/KlipperScreen-requirements.txt"),
            ("install_script", "scripts/KlipperScreen-install.sh"),
        ],
    )


def update_klipperscreen() -> None:
    try:
        control_systemd_service("KlipperScreen", "stop")

        if not KLIPPERSCREEN_DIR.exists():
            Logger.print_info(
                "KlipperScreen does not seem to be installed! Skipping ..."
            )
            return

        Logger.print_status("Updating KlipperScreen ...")

        control_systemd_service("KlipperScreen", "stop")

        settings = KiauhSettings()
        if settings.get("kiauh", "backup_before_update"):
            backup_klipperscreen_dir()

        git_pull_wrapper(KLIPPERSCREEN_REPO, KLIPPERSCREEN_DIR)

        requirements = KLIPPERSCREEN_DIR.joinpath(
            "/scripts/KlipperScreen-requirements.txt"
        )
        install_python_requirements(KLIPPERSCREEN_ENV, requirements)

        control_systemd_service("KlipperScreen", "start")

        Logger.print_ok("KlipperScreen updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        return


def get_klipperscreen_status() -> (
    Dict[
        Literal["status", "status_code", "repo", "local", "remote"],
        Union[str, int],
    ]
):
    files = [
        KLIPPERSCREEN_DIR,
        KLIPPERSCREEN_ENV,
        SYSTEMD.joinpath("KlipperScreen.service"),
    ]
    status = get_install_status(KLIPPERSCREEN_DIR, files)
    return {
        "status": status.get("status"),
        "status_code": status.get("status_code"),
        "repo": get_repo_name(KLIPPERSCREEN_DIR),
        "local": get_local_commit(KLIPPERSCREEN_DIR),
        "remote": get_remote_commit(KLIPPERSCREEN_DIR),
    }


def remove_klipperscreen() -> None:
    Logger.print_status("Removing KlipperScreen ...")
    try:
        if KLIPPERSCREEN_DIR.exists():
            Logger.print_status("Removing KlipperScreen directory ...")
            shutil.rmtree(KLIPPERSCREEN_DIR)
            Logger.print_ok("KlipperScreen directory successfully removed!")
        else:
            Logger.print_warn("KlipperScreen directory not found!")

        if KLIPPERSCREEN_ENV.exists():
            Logger.print_status("Removing KlipperScreen environment ...")
            shutil.rmtree(KLIPPERSCREEN_ENV)
            Logger.print_ok("KlipperScreen environment successfully removed!")
        else:
            Logger.print_warn("KlipperScreen environment not found!")

        service = SYSTEMD.joinpath("KlipperScreen.service")
        if service.exists():
            Logger.print_status("Removing KlipperScreen service ...")
            control_systemd_service(service, "stop")
            control_systemd_service(service, "disable")
            remove_with_sudo(service)
            Logger.print_ok("KlipperScreen service successfully removed!")

        logfile = Path("/tmp/KlipperScreen.log")
        if logfile.exists():
            Logger.print_status("Removing KlipperScreen log file ...")
            remove_with_sudo(logfile)
            Logger.print_ok("KlipperScreen log file successfully removed!")

        kl_im = InstanceManager(Klipper)
        kl_instances: List[Klipper] = kl_im.instances
        for instance in kl_instances:
            logfile = instance.log_dir.joinpath("KlipperScreen.log")
            if logfile.exists():
                Logger.print_status(f"Removing {logfile} ...")
                Path(logfile).unlink()
                Logger.print_ok(f"{logfile} successfully removed!")

        mr_im = InstanceManager(Moonraker)
        mr_instances: List[Moonraker] = mr_im.instances
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
        "KlipperScreen", source=KLIPPERSCREEN_DIR, target=KLIPPERSCREEN_BACKUP_DIR
    )
    bm.backup_directory(
        "KlipperScreen-env", source=KLIPPERSCREEN_ENV, target=KLIPPERSCREEN_BACKUP_DIR
    )
