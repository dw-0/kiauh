# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Type

from components.klipper.klipper import Klipper
from core.constants import (
    COLOR_CYAN,
    GLOBAL_DEPS,
    PRINTER_CFG_BACKUP_DIR,
    RESET_FORMAT,
)
from core.instance_manager.base_instance import BaseInstance
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.types import ComponentStatus, StatusCode
from utils.git_utils import get_local_commit, get_remote_commit, get_repo_name
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)


def convert_camelcase_to_kebabcase(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def get_current_date() -> Dict[Literal["date", "time"], str]:
    """
    Get the current date |
    :return: Dict holding a date and time key:value pair
    """
    now: datetime = datetime.today()
    date: str = now.strftime("%Y%m%d")
    time: str = now.strftime("%H%M%S")

    return {"date": date, "time": time}


def check_install_dependencies(
    deps: Set[str] | None = None, include_global: bool = True
) -> None:
    """
    Common helper method to check if dependencies are installed
    and if not, install them automatically |
    :param include_global: Wether to include the global dependencies or not
    :param deps: List of strings of package names to check if installed
    :return: None
    """
    if deps is None:
        deps = set()

    if include_global:
        deps.update(GLOBAL_DEPS)

    requirements = check_package_install(deps)
    if requirements:
        Logger.print_status("Installing dependencies ...")
        Logger.print_info("The following packages need installation:")
        for r in requirements:
            print(f"{COLOR_CYAN}● {r}{RESET_FORMAT}")
        update_system_package_lists(silent=False)
        install_system_packages(requirements)


def get_install_status(
    repo_dir: Path,
    env_dir: Optional[Path] = None,
    instance_type: Optional[Type[BaseInstance]] = None,
    files: Optional[List[Path]] = None,
) -> ComponentStatus:
    """
    Helper method to get the installation status of software components
    :param repo_dir: the repository directory
    :param env_dir: the python environment directory
    :param instance_type: The component type
    :param files: List of optional files to check for existence
    :return: Dictionary with status string, statuscode and instance count
    """
    checks = [repo_dir.exists()]

    if env_dir is not None:
        checks.append(env_dir.exists())

    im = InstanceManager(instance_type)
    instances = 0
    if instance_type is not None:
        instances = len(im.instances)
        checks.append(instances > 0)

    if files is not None:
        for f in files:
            checks.append(f.exists())

    status: StatusCode
    if all(checks):
        status = 2  # installed
    elif not any(checks):
        status = 0  # not installed
    else:
        status = 1  # incomplete

    return ComponentStatus(
        status=status,
        instances=instances,
        repo=get_repo_name(repo_dir),
        local=get_local_commit(repo_dir),
        remote=get_remote_commit(repo_dir),
    )


def backup_printer_config_dir() -> None:
    # local import to prevent circular import
    from core.backup_manager.backup_manager import BackupManager

    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.instances
    bm = BackupManager()

    for instance in instances:
        name = f"config-{instance.data_dir_name}"
        bm.backup_directory(
            name,
            source=instance.cfg_dir,
            target=PRINTER_CFG_BACKUP_DIR,
        )


def moonraker_exists(name: str = "") -> bool:
    """
    Helper method to check if a Moonraker instance exists
    :param name: Optional name of an installer where the check is performed
    :return: True if at least one Moonraker instance exists, False otherwise
    """
    from components.moonraker.moonraker import Moonraker

    mr_im = InstanceManager(Moonraker)
    mr_instances: List[Moonraker] = mr_im.instances

    info = (
        f"{name} requires Moonraker to be installed"
        if name
        else "A Moonraker installation is required"
    )

    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "No Moonraker instances found!",
                f"{info}. Please install Moonraker first!",
            ],
        )
        return False
    return True
