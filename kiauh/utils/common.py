#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, List, Type

from kiauh.core.instance_manager.base_instance import BaseInstance
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.utils.constants import (
    COLOR_CYAN,
    RESET_FORMAT,
    COLOR_YELLOW,
    COLOR_GREEN,
    COLOR_RED,
)
from kiauh.utils.filesystem_utils import check_file_exist
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import check_package_install, install_system_packages


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
        install_system_packages(requirements)


def get_repo_name(repo_dir: Path) -> str:
    """
    Helper method to extract the organisation and name of a repository |
    :param repo_dir: repository to extract the values from
    :return: String in form of "<orga>/<name>"
    """
    try:
        cmd = ["git", "-C", repo_dir, "config", "--get", "remote.origin.url"]
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        result = "/".join(result.decode().strip().split("/")[-2:])
        return f"{COLOR_CYAN}{result}{RESET_FORMAT}"
    except subprocess.CalledProcessError:
        return f"{COLOR_YELLOW}Unknown{RESET_FORMAT}"


def get_install_status_common(
    instance_type: Type[BaseInstance], repo_dir: Path, env_dir: Path
) -> str:
    """
    Helper method to get the installation status of software components,
    which only consist of 3 major parts and if those parts exist, the
    component can be considered as "installed". Typically, Klipper or
    Moonraker match that criteria.
    :param instance_type: The component type
    :param repo_dir: the repository directory
    :param env_dir: the python environment directory
    :return: formatted string, containing the status
    """
    im = InstanceManager(instance_type)
    instances_exist = len(im.instances) > 0
    status = [repo_dir.exists(), env_dir.exists(), instances_exist]
    if all(status):
        return f"{COLOR_GREEN}Installed: {len(im.instances)}{RESET_FORMAT}"
    elif not any(status):
        return f"{COLOR_RED}Not installed!{RESET_FORMAT}"
    else:
        return f"{COLOR_YELLOW}Incomplete!{RESET_FORMAT}"


def get_install_status_webui(
    install_dir: Path, nginx_cfg: Path, upstreams_cfg: Path, common_cfg: Path
) -> str:
    """
    Helper method to get the installation status of webuis
    like Mainsail or Fluidd |
    :param install_dir: folder of the static webui files
    :param nginx_cfg: the webuis NGINX config
    :param upstreams_cfg: the required upstreams.conf
    :param common_cfg: the required common_vars.conf
    :return: formatted string, containing the status
    """
    dir_exist = install_dir.exists()
    nginx_cfg_exist = check_file_exist(nginx_cfg)
    upstreams_cfg_exist = check_file_exist(upstreams_cfg)
    common_cfg_exist = check_file_exist(common_cfg)
    status = [dir_exist, nginx_cfg_exist, upstreams_cfg_exist, common_cfg_exist]
    if all(status):
        return f"{COLOR_GREEN}Installed!{RESET_FORMAT}"
    elif not any(status):
        return f"{COLOR_RED}Not installed!{RESET_FORMAT}"
    else:
        return f"{COLOR_YELLOW}Incomplete!{RESET_FORMAT}"
