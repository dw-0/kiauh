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

from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper import (
    EXIT_KLIPPER_SETUP,
    DEFAULT_KLIPPER_REPO_URL,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_REQUIREMENTS_TXT,
)
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import (
    print_instance_overview,
    print_select_instance_count_dialog,
    print_update_warn_dialog,
)
from kiauh.modules.klipper.klipper_utils import (
    handle_convert_single_to_multi_instance_names,
    handle_new_multi_instance_names,
    handle_existing_multi_instance_names,
    handle_disruptive_system_packages,
    check_user_groups,
    handle_single_to_multi_conversion,
)
from kiauh.core.repo_manager.repo_manager import RepoManager
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
    instance_list = instance_manager.instances
    instances_installed = len(instance_list)

    is_klipper_installed = instances_installed > 0
    if not install and not is_klipper_installed:
        Logger.print_warn("Klipper not installed!")
        return

    if install:
        add_additional = handle_existing_instances(instance_list)
        if is_klipper_installed and not add_additional:
            Logger.print_info(EXIT_KLIPPER_SETUP)
            return

        install_klipper(instance_manager, instance_list)

    if not install:
        if instances_installed == 1:
            remove_single_instance(instance_manager, instance_list)
        else:
            remove_multi_instance(instance_manager, instance_list)


def handle_existing_instances(instance_list: List[Klipper]) -> bool:
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_confirm("Add new instances?", allow_go_back=True):
            return False

    return True


def install_klipper(
    instance_manager: InstanceManager, instance_list: List[Klipper]
) -> None:
    print_select_instance_count_dialog()
    question = f"Number of{' additional' if len(instance_list) > 0 else ''} Klipper instances to set up"
    install_count = get_number_input(question, 1, default=1, allow_go_back=True)
    if install_count is None:
        Logger.print_info(EXIT_KLIPPER_SETUP)
        return

    instance_names = set_instance_suffix(instance_list, install_count)
    if instance_names is None:
        Logger.print_info(EXIT_KLIPPER_SETUP)
        return

    if len(instance_list) < 1:
        setup_klipper_prerequesites()

    convert_single_to_multi = (
        len(instance_list) == 1
        and instance_list[0].suffix is None
        and install_count >= 1
    )

    for name in instance_names:
        if convert_single_to_multi:
            handle_single_to_multi_conversion(instance_manager, name)
            convert_single_to_multi = False
        else:
            instance_manager.current_instance = Klipper(suffix=name)

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

    repo = str(cm.get_value("klipper", "repository_url") or DEFAULT_KLIPPER_REPO_URL)
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
    klipper_py_req = Path(KLIPPER_REQUIREMENTS_TXT)
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


def set_instance_suffix(
    instance_list: List[Klipper], install_count: int
) -> List[Union[str, None]]:
    instance_count = len(instance_list)

    # new single instance install
    if instance_count == 0 and install_count == 1:
        return [None]

    # convert single instance install to multi install
    elif instance_count == 1 and install_count >= 1 and instance_list[0].suffix is None:
        return handle_convert_single_to_multi_instance_names(install_count)

    # new multi instance install
    elif instance_count == 0 and install_count > 1:
        return handle_new_multi_instance_names(instance_count, install_count)

    # existing multi instance install
    elif instance_count > 1:
        return handle_existing_multi_instance_names(
            instance_count, install_count, instance_list
        )


def remove_single_instance(
    instance_manager: InstanceManager, instance_list: List[Klipper]
) -> None:
    question = f"Delete {KLIPPER_DIR} and {KLIPPER_ENV_DIR}?"
    del_remnants = get_confirm(question, allow_go_back=True)
    if del_remnants is None:
        Logger.print_info("Exiting Klipper Uninstaller ...")
        return

    try:
        instance_manager.current_instance = instance_list[0]
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=del_remnants)
        instance_manager.reload_daemon()
    except (OSError, subprocess.CalledProcessError):
        Logger.print_error("Removing instance failed!")
        return


def remove_multi_instance(
    instance_manager: InstanceManager, instance_list: List[Klipper]
) -> None:
    print_instance_overview(instance_list, show_index=True, show_select_all=True)

    options = [str(i) for i in range(len(instance_list))]
    options.extend(["a", "A", "b", "B"])

    selection = get_selection_input("Select Klipper instance to remove", options)

    if selection == "b".lower():
        return
    elif selection == "a".lower():
        question = f"Delete {KLIPPER_DIR} and {KLIPPER_ENV_DIR}?"
        del_remnants = get_confirm(question, allow_go_back=True)
        if del_remnants is None:
            Logger.print_info("Exiting Klipper Uninstaller ...")
            return

        Logger.print_info("Removing all Klipper instances ...")
        for instance in instance_list:
            instance_manager.current_instance = instance
            instance_manager.stop_instance()
            instance_manager.disable_instance()
            instance_manager.delete_instance(del_remnants=del_remnants)
    else:
        instance = instance_list[int(selection)]
        log = f"Removing Klipper instance: {instance.get_service_file_name()}"
        Logger.print_info(log)
        instance_manager.current_instance = instance
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=False)

    instance_manager.reload_daemon()


def update_klipper() -> None:
    print_update_warn_dialog()

    if not get_confirm("Update Klipper now?"):
        return

    instance_manager = InstanceManager(Klipper)
    instance_manager.stop_all_instance()

    cm = ConfigManager()
    cm.read_config()

    repo = str(cm.get_value("klipper", "repository_url") or DEFAULT_KLIPPER_REPO_URL)
    branch = str(cm.get_value("klipper", "branch") or "master")

    repo_manager = RepoManager(
        repo=repo,
        branch=branch,
        target_dir=KLIPPER_DIR,
    )
    repo_manager.pull_repo()
    instance_manager.start_all_instance()
