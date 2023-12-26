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
from typing import List

from kiauh import KIAUH_CFG
from kiauh.core.backup_manager.backup_manager import BackupManager
from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.core.instance_manager.name_scheme import NameScheme
from kiauh.modules.klipper import (
    EXIT_KLIPPER_SETUP,
    DEFAULT_KLIPPER_REPO_URL,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_REQUIREMENTS_TXT,
)
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import (
    print_update_warn_dialog,
    print_select_custom_name_dialog,
)
from kiauh.modules.klipper.klipper_utils import (
    handle_disruptive_system_packages,
    check_user_groups,
    handle_to_multi_instance_conversion,
    create_example_printer_cfg,
    detect_name_scheme,
    add_to_existing,
    get_install_count,
    assign_custom_name,
)
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils.input_utils import get_confirm, get_number_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    parse_packages_from_file,
    create_python_venv,
    install_python_requirements,
    update_system_package_lists,
    install_system_packages,
)


# TODO: this method needs refactoring! (but it works for now)
def install_klipper() -> None:
    im = InstanceManager(Klipper)
    kl_instances: List[Klipper] = im.instances

    # ask to add new instances, if there are existing ones
    if kl_instances and not add_to_existing():
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    install_count = get_install_count()
    # install_count = None -> user entered "b" to go back
    if install_count is None:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    # create a dict of the size of the existing instances + install count
    name_scheme = NameScheme.SINGLE
    single_to_multi = len(kl_instances) == 1 and kl_instances[0].suffix == ""
    name_dict = {c: "" for c in range(len(kl_instances) + install_count)}

    if (not kl_instances and install_count > 1) or single_to_multi:
        print_select_custom_name_dialog()
        if get_confirm("Assign custom names?", False, allow_go_back=True):
            name_scheme = NameScheme.CUSTOM
        else:
            name_scheme = NameScheme.INDEX

    # if there are more moonraker instances installed than klipper, we
    # load their names into the name_dict, as we will detect and enforce that naming scheme
    mr_instances: List[Moonraker] = InstanceManager(Moonraker).instances
    if len(mr_instances) > len(kl_instances):
        for k, v in enumerate(mr_instances):
            name_dict[k] = v.suffix
        name_scheme = detect_name_scheme(mr_instances)
    elif len(kl_instances) > 1:
        for k, v in enumerate(kl_instances):
            name_dict[k] = v.suffix
        name_scheme = detect_name_scheme(kl_instances)

    # set instance names if multiple instances will be created
    if name_scheme != NameScheme.SINGLE:
        for k in name_dict:
            if name_dict[k] == "" and name_scheme == NameScheme.INDEX:
                name_dict[k] = str(k + 1)
            elif name_dict[k] == "" and name_scheme == NameScheme.CUSTOM:
                assign_custom_name(k, name_dict)

    create_example_cfg = get_confirm("Create example printer.cfg?")

    if not kl_instances:
        setup_klipper_prerequesites()

    count = 0
    for name in name_dict:
        if name_dict[name] in [n.suffix for n in kl_instances]:
            continue
        else:
            count += 1

        if single_to_multi:
            handle_to_multi_instance_conversion(name_dict[name])
            single_to_multi = False
            count -= 1
        else:
            new_instance = Klipper(suffix=name_dict[name])
            im.current_instance = new_instance
            im.create_instance()
            im.enable_instance()
            if create_example_cfg:
                create_example_printer_cfg(new_instance)
            im.start_instance()

        if count == install_count:
            break

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
