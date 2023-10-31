# !/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import subprocess
from pathlib import Path
from typing import List, Union

from kiauh.config_manager.config_manager import ConfigManager
from kiauh.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import (
    print_instance_overview,
    print_select_instance_count_dialog,
)
from kiauh.modules.klipper.klipper_utils import (
    handle_convert_single_to_multi_instance_names,
    handle_new_multi_instance_names,
    handle_existing_multi_instance_names,
    handle_disruptive_system_packages,
    check_user_groups,
    handle_single_to_multi_conversion,
)
from kiauh.repo_manager.repo_manager import RepoManager
from kiauh.utils.constants import KLIPPER_DIR, KLIPPER_ENV_DIR
from kiauh.utils.input_utils import (
    get_confirm,
    get_number_input,
    get_selection_input,
)
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    parse_packages_from_file,
    create_python_venv,
    install_python_requirements,
    update_system_package_lists,
    install_system_packages,
)


def run_klipper_setup(install: bool) -> None:
    instance_manager = InstanceManager(Klipper)
    instance_list = instance_manager.get_instances()
    instances_installed = len(instance_list)

    is_klipper_installed = check_klipper_installation(instance_manager)
    if not install and not is_klipper_installed:
        Logger.print_warn("Klipper not installed!")
        return

    if install:
        add_additional = handle_existing_instances(instance_manager)
        if is_klipper_installed and not add_additional:
            Logger.print_info("Exiting Klipper setup ...")
            return

        install_klipper(instance_manager)

    if not install:
        if instances_installed == 1:
            remove_single_instance(instance_manager)
        else:
            remove_multi_instance(instance_manager)


def check_klipper_installation(instance_manager: InstanceManager) -> bool:
    instance_list = instance_manager.get_instances()
    instances_installed = len(instance_list)

    if instances_installed < 1:
        return False

    return True


def handle_existing_instances(instance_manager: InstanceManager) -> bool:
    instance_list = instance_manager.get_instances()
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_confirm("Add new instances?"):
            return False

    return True


def install_klipper(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()

    print_select_instance_count_dialog()
    question = f"Number of{' additional' if len(instance_list) > 0 else ''} Klipper instances to set up"
    install_count = get_number_input(question, 1, default=1, allow_go_back=True)
    if install_count is None:
        Logger.print_info("Exiting Klipper setup ...")
        return

    instance_names = set_instance_names(instance_list, install_count)
    if instance_names is None:
        Logger.print_info("Exiting Klipper setup ...")
        return

    if len(instance_list) < 1:
        setup_klipper_prerequesites()

    convert_single_to_multi = (
        True
        if len(instance_list) == 1
        and instance_list[0].name is None
        and install_count >= 1
        else False
    )

    for name in instance_names:
        if convert_single_to_multi:
            handle_single_to_multi_conversion(instance_manager, name)
            convert_single_to_multi = False
        else:
            instance_manager.set_current_instance(Klipper(name=name))

        instance_manager.create_instance()
        instance_manager.enable_instance()
        instance_manager.start_instance()

    instance_manager.reload_daemon()

    # step 4: check/handle conflicting packages/services
    handle_disruptive_system_packages()

    # step 5: check for required group membership
    check_user_groups()


def setup_klipper_prerequesites() -> None:
    cm = ConfigManager()
    cm.read_config()

    repo = str(
        cm.get_value("klipper", "repository_url")
        or "https://github.com/Klipper3D/klipper"
    )
    branch = str(cm.get_value("klipper", "branch") or "master")

    repo_manager = RepoManager(
        repo=repo,
        branch=branch,
        target_dir=KLIPPER_DIR,
    )
    repo_manager.clone_repo()

    # install klipper dependencies and create python virtualenv
    install_klipper_packages(Path(KLIPPER_DIR))
    create_python_venv(Path(KLIPPER_ENV_DIR))
    klipper_py_req = Path(f"{KLIPPER_DIR}/scripts/klippy-requirements.txt")
    install_python_requirements(Path(KLIPPER_ENV_DIR), klipper_py_req)


def install_klipper_packages(klipper_dir: Path) -> None:
    script = f"{klipper_dir}/scripts/install-debian.sh"
    packages = parse_packages_from_file(script)
    packages = [pkg.replace("python-dev", "python3-dev") for pkg in packages]
    # Add dfu-util for octopi-images
    packages.append("dfu-util")
    # Add dbus requirement for DietPi distro
    if os.path.exists("/boot/dietpi/.version"):
        packages.append("dbus")

    update_system_package_lists(silent=False)
    install_system_packages(packages)


def set_instance_names(instance_list, install_count: int) -> List[Union[str, None]]:
    instance_count = len(instance_list)

    # new single instance install
    if instance_count == 0 and install_count == 1:
        return [None]

    # convert single instance install to multi install
    elif instance_count == 1 and instance_list[0].name is None and install_count >= 1:
        return handle_convert_single_to_multi_instance_names(install_count)

    # new multi instance install
    elif instance_count == 0 and install_count > 1:
        return handle_new_multi_instance_names(instance_count, install_count)

    # existing multi instance install
    elif instance_count > 1:
        return handle_existing_multi_instance_names(
            instance_count, install_count, instance_list
        )


def remove_single_instance(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()
    try:
        instance_manager.set_current_instance(instance_list[0])
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=True)
        instance_manager.reload_daemon()
    except (OSError, subprocess.CalledProcessError):
        Logger.print_error("Removing instance failed!")
        return


def remove_multi_instance(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()
    print_instance_overview(instance_list, show_index=True, show_select_all=True)

    options = [str(i) for i in range(len(instance_list))]
    options.extend(["a", "A", "b", "B"])

    selection = get_selection_input("Select Klipper instance to remove", options)
    print(selection)

    if selection == "b".lower():
        return
    elif selection == "a".lower():
        Logger.print_info("Removing all Klipper instances ...")
        for instance in instance_list:
            instance_manager.set_current_instance(instance)
            instance_manager.stop_instance()
            instance_manager.disable_instance()
            instance_manager.delete_instance(del_remnants=True)
    else:
        instance = instance_list[int(selection)]
        Logger.print_info(
            f"Removing Klipper instance: {instance.get_service_file_name()}"
        )
        instance_manager.set_current_instance(instance)
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=False)

    instance_manager.reload_daemon()
