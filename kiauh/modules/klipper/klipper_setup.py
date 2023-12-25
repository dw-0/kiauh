#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from typing import List, Union

from kiauh import KIAUH_CFG
from kiauh.core.backup_manager.backup_manager import BackupManager
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
    create_example_printer_cfg,
)
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.utils.input_utils import get_confirm, get_number_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    parse_packages_from_file,
    create_python_venv,
    install_python_requirements,
    update_system_package_lists,
    install_system_packages,
)


def install_klipper() -> None:
    im = InstanceManager(Klipper)

    add_additional = handle_existing_instances(im.instances)
    if len(im.instances) > 0 and not add_additional:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    print_select_instance_count_dialog()
    question = f"Number of{' additional' if len(im.instances) > 0 else ''} Klipper instances to set up"
    install_count = get_number_input(question, 1, default=1, allow_go_back=True)
    if install_count is None:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    instance_names = set_instance_suffix(im.instances, install_count)
    if instance_names is None:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    create_example_cfg = get_confirm("Create example printer.cfg?")

    if len(im.instances) < 1:
        setup_klipper_prerequesites()

    convert_single_to_multi = (
        len(im.instances) == 1 and im.instances[0].suffix is None and install_count >= 1
    )

    for name in instance_names:
        if convert_single_to_multi:
            current_instance = handle_single_to_multi_conversion(im, name)
            convert_single_to_multi = False
        else:
            current_instance = Klipper(suffix=name)

        im.current_instance = current_instance
        im.create_instance()
        im.enable_instance()

        if create_example_cfg:
            create_example_printer_cfg(current_instance)

        im.start_instance()

    im.reload_daemon()

    # step 4: check/handle conflicting packages/services
    handle_disruptive_system_packages()

    # step 5: check for required group membership
    check_user_groups()


def setup_klipper_prerequesites() -> None:
    cm = ConfigManager(cfg_file=KIAUH_CFG)
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
    script = klipper_dir.joinpath("scripts/install-debian.sh")
    packages = parse_packages_from_file(script)
    packages = [pkg.replace("python-dev", "python3-dev") for pkg in packages]
    # Add dfu-util for octopi-images
    packages.append("dfu-util")
    # Add dbus requirement for DietPi distro
    if Path("/boot/dietpi/.version").exists():
        packages.append("dbus")

    update_system_package_lists(silent=False)
    install_system_packages(packages)


def handle_existing_instances(instance_list: List[Klipper]) -> bool:
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_confirm("Add new instances?", allow_go_back=True):
            return False

    return True


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


def update_klipper() -> None:
    print_update_warn_dialog()
    if not get_confirm("Update Klipper now?"):
        return

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    if cm.get_value("kiauh", "backup_before_update"):
        bm = BackupManager()
        bm.backup_directory("klipper", KLIPPER_DIR)
        bm.backup_directory("klippy-env", KLIPPER_ENV_DIR)

    instance_manager = InstanceManager(Klipper)
    instance_manager.stop_all_instance()

    repo = str(cm.get_value("klipper", "repository_url") or DEFAULT_KLIPPER_REPO_URL)
    branch = str(cm.get_value("klipper", "branch") or "master")

    repo_manager = RepoManager(
        repo=repo,
        branch=branch,
        target_dir=KLIPPER_DIR,
    )
    repo_manager.pull_repo()
    instance_manager.start_all_instance()
