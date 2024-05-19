# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Type

from components.klipper.klipper import Klipper
from core.instance_manager.base_instance import BaseInstance
from core.instance_manager.instance_manager import InstanceManager
from utils import PRINTER_CFG_BACKUP_DIR
from utils.constants import (
    COLOR_CYAN,
    RESET_FORMAT,
)
from utils.git_utils import get_local_commit, get_remote_commit, get_repo_name
from utils.logger import Logger
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)
from utils.types import ComponentStatus, InstallStatus


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


def check_install_dependencies(deps: List[str]) -> None:
    """
    Common helper method to check if dependencies are installed
    and if not, install them automatically |
    :param deps: List of strings of package names to check if installed
    :return: None
    """
    requirements = check_package_install(deps)
    if requirements:
        Logger.print_status("Installing dependencies ...")
        Logger.print_info("The following packages need installation:")
        for _ in requirements:
            print(f"{COLOR_CYAN}● {_}{RESET_FORMAT}")
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

    if all(checks):
        status = InstallStatus.INSTALLED

    elif not any(checks):
        status = InstallStatus.NOT_INSTALLED

    else:
        status = InstallStatus.INCOMPLETE

    return ComponentStatus(
        status=status,
        instances=instances,
        repo=get_repo_name(repo_dir),
        local=get_local_commit(repo_dir),
        remote=get_remote_commit(repo_dir),
    )


def backup_printer_config_dir():
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
