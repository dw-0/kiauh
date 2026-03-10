# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from core.constants import SYSTEMD
from core.instance_manager.base_instance import SUFFIX_BLACKLIST
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from utils.input_utils import get_confirm
from utils.instance_type import InstanceType


def get_instances(
    instance_type: type, suffix_blacklist: List[str] = SUFFIX_BLACKLIST
) -> List[InstanceType]:
    from utils.common import convert_camelcase_to_kebabcase

    if not isinstance(instance_type, type):
        raise ValueError("instance_type must be a class")

    name = convert_camelcase_to_kebabcase(instance_type.__name__)
    pattern = re.compile(f"^{name}(-[0-9a-zA-Z]+)?.service$")

    service_list = [
        Path(SYSTEMD, service)
        for service in SYSTEMD.iterdir()
        if pattern.search(service.name)
        and not any(s in service.name for s in suffix_blacklist)
    ]

    instance_list = [
        instance_type(get_instance_suffix(name, service)) for service in service_list
    ]

    def _sort_instance_list(suffix: int | str | None):
        if suffix is None:
            return
        elif isinstance(suffix, str) and suffix.isdigit():
            return f"{int(suffix):04}"
        else:
            return suffix

    return sorted(instance_list, key=lambda x: _sort_instance_list(x.suffix))


def get_instance_suffix(name: str, file_path: Path) -> str:
    # to get the suffix of the instance, we remove the name of the instance from
    # the file name, if the remaining part an empty string we return it
    # otherwise there is and hyphen left, and we return the part after the hyphen
    suffix = file_path.stem[len(name) :]
    return suffix[1:] if suffix else ""


def stop_klipper_instances_interactively(
    self, kl_instances: List[Klipper], operation_name: str = "operation"
) -> bool:
    """
    Interactively stops all active Klipper instances, warning the user that ongoing prints will be disrupted.

    :param kl_instances: List of Klipper instances to stop.
    :param operation_name: Optional name of the operation being performed (for user messaging). Do NOT capitalize.
    :return: True if instances were stopped or no instances found, False if operation was aborted.
    """

    if not kl_instances:
        Logger.print_warn("No instances found, skipping instance stopping.")
        return True

    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            "Do NOT continue if there are ongoing prints running",
            f"All Klipper instances will be restarted during the {operation_name} and "
            "ongoing prints WILL FAIL.",
        ],
    )
    stop_klipper = get_confirm(
        question=f"Stop Klipper now and proceed with {operation_name}?",
        default_choice=False,
        allow_go_back=True,
    )

    if stop_klipper:
        InstanceManager.stop_all(kl_instances)
        return True
    else:
        Logger.print_warn(f"{operation_name.capitalize()} aborted due to user request.")
        return False
