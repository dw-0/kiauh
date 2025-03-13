# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import grp
import os
import shutil
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Dict, List

from components.klipper import (
    KLIPPER_BACKUP_DIR,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_INSTALL_SCRIPT,
    MODULE_PATH,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    print_instance_overview,
    print_select_instance_count_dialog,
)
from components.webui_client.base_data import BaseWebClient
from components.webui_client.client_config.client_config_setup import (
    create_client_config_symlink,
)
from core.backup_manager.backup_manager import BackupManager
from core.constants import CURRENT_USER
from core.instance_manager.base_instance import SUFFIX_BLACKLIST
from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from core.types.component_status import ComponentStatus
from utils.common import check_install_dependencies, get_install_status
from utils.fs_utils import check_file_exist
from utils.input_utils import get_confirm, get_number_input, get_string_input
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_service,
    install_python_packages,
    parse_packages_from_file,
)


def get_klipper_status() -> ComponentStatus:
    return get_install_status(KLIPPER_DIR, KLIPPER_ENV_DIR, Klipper)


def add_to_existing() -> bool | None:
    kl_instances: List[Klipper] = get_instances(Klipper)
    print_instance_overview(kl_instances)
    _input: bool | None = get_confirm("Add new instances?", allow_go_back=True)
    return _input


def get_install_count() -> int | None:
    """
    Print a dialog for selecting the amount of Klipper instances
    to set up with an option to navigate back. Returns None if the
    user selected to go back, otherwise an integer greater or equal than 1 |
    :return: Integer >= 1 or None
    """
    kl_instances = get_instances(Klipper)
    print_select_instance_count_dialog()
    question = (
        f"Number of"
        f"{' additional' if len(kl_instances) > 0 else ''} "
        f"Klipper instances to set up"
    )
    _input: int | None = get_number_input(question, 1, default=1, allow_go_back=True)
    return _input


def assign_custom_name(key: int, name_dict: Dict[int, str]) -> None:
    existing_names = []
    existing_names.extend(SUFFIX_BLACKLIST)
    existing_names.extend(name_dict[n] for n in name_dict)
    pattern = r"^[a-zA-Z0-9]+$"

    question = f"Enter name for instance {key}"
    name_dict[key] = get_string_input(question, exclude=existing_names, regex=pattern)


def check_user_groups() -> None:
    user_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]
    missing_groups = [g for g in ["tty", "dialout"] if g not in user_groups]

    if not missing_groups:
        return

    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            "Your current user is not in group:",
            *[f"● {g}" for g in missing_groups],
            "\n\n",
            "It is possible that you won't be able to successfully connect and/or "
            "flash the controller board without your user being a member of that "
            "group. If you want to add the current user to the group(s) listed above, "
            "answer with 'Y'. Else skip with 'n'.",
            "\n\n",
            "INFO:",
            "Relog required for group assignments to take effect!",
        ],
    )

    if not get_confirm(f"Add user '{CURRENT_USER}' to group(s) now?"):
        log = "Skipped adding user to required groups. You might encounter issues."
        Logger.warn(log)
        return

    try:
        for group in missing_groups:
            Logger.print_status(f"Adding user '{CURRENT_USER}' to group {group} ...")
            command = ["sudo", "usermod", "-a", "-G", group, CURRENT_USER]
            run(command, check=True)
            Logger.print_ok(f"Group {group} assigned to user '{CURRENT_USER}'.")
    except CalledProcessError as e:
        Logger.print_error(f"Unable to add user to usergroups: {e}")
        raise

    log = "Remember to relog/restart this machine for the group(s) to be applied!"
    Logger.print_warn(log)


def handle_disruptive_system_packages() -> None:
    services = []

    command = ["systemctl", "is-enabled", "brltty"]
    brltty_status = run(command, capture_output=True, text=True)

    command = ["systemctl", "is-enabled", "brltty-udev"]
    brltty_udev_status = run(command, capture_output=True, text=True)

    command = ["systemctl", "is-enabled", "ModemManager"]
    modem_manager_status = run(command, capture_output=True, text=True)

    if "enabled" in brltty_status.stdout:
        services.append("brltty")
    if "enabled" in brltty_udev_status.stdout:
        services.append("brltty-udev")
    if "enabled" in modem_manager_status.stdout:
        services.append("ModemManager")

    for service in services if services else []:
        try:
            cmd_sysctl_service(service, "mask")
        except CalledProcessError:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    f"KIAUH was unable to mask the {service} system service. "
                    "Please fix the problem manually. Otherwise, this may have "
                    "undesirable effects on the operation of Klipper."
                ],
            )


def create_example_printer_cfg(
    instance: Klipper, clients: List[BaseWebClient] | None = None
) -> None:
    Logger.print_status(f"Creating example printer.cfg in '{instance.base.cfg_dir}'")
    if instance.cfg_file.is_file():
        Logger.print_info(f"'{instance.cfg_file}' already exists.")
        return

    source = MODULE_PATH.joinpath("assets/printer.cfg")
    target = instance.cfg_file
    try:
        shutil.copy(source, target)
    except OSError as e:
        Logger.print_error(f"Unable to create example printer.cfg:\n{e}")
        return

    scp = SimpleConfigParser()
    scp.read_file(target)
    scp.set_option("virtual_sdcard", "path", str(instance.base.gcodes_dir))

    # include existing client configs in the example config
    if clients is not None and len(clients) > 0:
        for c in clients:
            client_config = c.client_config
            section = client_config.config_section
            scp.add_section(section=section)
            create_client_config_symlink(client_config, [instance])

    scp.write_file(target)

    Logger.print_ok(f"Example printer.cfg created in '{instance.base.cfg_dir}'")


def backup_klipper_dir() -> None:
    bm = BackupManager()
    bm.backup_directory("klipper", source=KLIPPER_DIR, target=KLIPPER_BACKUP_DIR)
    bm.backup_directory("klippy-env", source=KLIPPER_ENV_DIR, target=KLIPPER_BACKUP_DIR)


def install_klipper_packages() -> None:
    script = KLIPPER_INSTALL_SCRIPT
    packages = parse_packages_from_file(script)

    # Add pkg-config for rp2040 build
    packages.append("pkg-config")

    # Add dbus requirement for DietPi distro
    if check_file_exist(Path("/boot/dietpi/.version")):
        packages.append("dbus")

    check_install_dependencies({*packages})


def install_input_shaper_deps() -> None:
    if not KLIPPER_ENV_DIR.exists():
        Logger.print_warn("Required Klipper python environment not found!")
        return

    Logger.print_dialog(
        DialogType.CUSTOM,
        [
            "Resonance measurements and shaper auto-calibration require additional "
            "software dependencies which are not installed by default. "
            "If you agree, the following additional system packages will be installed:",
            "● python3-numpy",
            "● python3-matplotlib",
            "● libatlas-base-dev",
            "● libopenblas-dev",
            "\n\n",
            "Also, the following Python package will be installed:",
            "● numpy",
        ],
        custom_title="Install Input Shaper Dependencies",
    )
    if not get_confirm(
        "Do you want to install the required packages?", default_choice=False
    ):
        return

    apt_deps = (
        "python3-numpy",
        "python3-matplotlib",
        "libatlas-base-dev",
        "libopenblas-dev",
    )
    check_install_dependencies({*apt_deps})

    py_deps = ("numpy",)

    install_python_packages(KLIPPER_ENV_DIR, {*py_deps})
