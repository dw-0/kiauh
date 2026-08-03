# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from typing import Dict, List, Literal, Set

from components.moonraker.moonraker import Moonraker
from core.constants import (
    GLOBAL_DEPS,
)
from core.i18n import _tr
from core.logger import DialogType, Logger
from core.types.color import Color
from core.types.component_status import ComponentStatus, StatusCode
from utils.git_utils import (
    get_current_branch,
    get_local_commit,
    get_local_tags,
    get_remote_commit,
    get_repo_name,
    get_repo_url,
)
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)

from kiauh import PROJECT_ROOT


def get_kiauh_version() -> str:
    """
    Helper method to get the current KIAUH version by reading the latest tag
    :return: string of the latest tag or a default value if no tags exist
    """
    tags: List[str] = get_local_tags(PROJECT_ROOT)
    if tags:
        return tags[-1]
    else:
        return "v?.?.?"


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
        Logger.print_status(_tr("Installing dependencies ..."))
        Logger.print_info(_tr("The following packages need installation:"))
        for r in requirements:
            print(Color.apply(f"● {r}", Color.CYAN))
        # Installing against stale or missing package metadata is unsafe, so abort
        # here instead of swallowing the error like the update menu does.
        update_system_package_lists(silent=False)
        install_system_packages(requirements)


def get_install_status(
    repo_dir: Path,
    env_dir: Path | None = None,
    instance_type: type | None = None,
    files: List[Path] | None = None,
) -> ComponentStatus:
    """
    Helper method to get the installation status of software components
    :param repo_dir: the repository directory
    :param env_dir: the python environment directory
    :param instance_type: The component type
    :param files: List of optional files to check for existence
    :return: Dictionary with status string, statuscode and instance count
    """
    from utils.instance_utils import get_instances

    checks = []
    branch: str | None = None

    if repo_dir.exists():
        checks.append(True)
        branch = get_current_branch(repo_dir)

    if env_dir is not None:
        checks.append(env_dir.exists())

    instances = 0
    if instance_type is not None:
        instances = len(get_instances(instance_type))
        checks.append(instances > 0)

    if files is not None:
        for f in files:
            checks.append(f.exists())

    status: StatusCode
    if checks and all(checks):
        status = 2  # installed
    elif not any(checks):
        status = 0  # not installed
    else:
        status = 1  # incomplete

    org, repo = get_repo_name(repo_dir)
    repo_url = get_repo_url(repo_dir) if repo_dir.exists() else None

    return ComponentStatus(
        status=status,
        instances=instances,
        owner=org,
        repo=repo,
        repo_url=repo_url,
        branch=branch,
        local=get_local_commit(repo_dir),
        remote=get_remote_commit(repo_dir),
    )


def moonraker_exists(name: str = "") -> List[Moonraker]:
    """
    Helper method to check if a Moonraker instance exists
    :param name: Optional name of an installer where the check is performed
    :return: True if at least one Moonraker instance exists, False otherwise
    """
    mr_instances: List[Moonraker] = get_instances(Moonraker)

    info = (
        _tr("{} requires Moonraker to be installed").format(name)
        if name
        else _tr("A Moonraker installation is required")
    )

    if not mr_instances:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                _tr("No Moonraker instances found!"),
                _tr("{}. Please install Moonraker first!").format(info),
            ],
        )
        return []
    return mr_instances


def trunc_string(input_str: str, length: int) -> str:
    if len(input_str) > length:
        return f"{input_str[: length - 3]}..."
    return input_str
