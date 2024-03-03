#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from components.webui_client.client_utils import get_existing_client_config
from kiauh import KIAUH_CFG
from components.klipper import (
    EXIT_KLIPPER_SETUP,
    DEFAULT_KLIPPER_REPO_URL,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_REQUIREMENTS_TXT,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import print_update_warn_dialog
from components.klipper.klipper_utils import (
    handle_disruptive_system_packages,
    check_user_groups,
    handle_to_multi_instance_conversion,
    create_example_printer_cfg,
    add_to_existing,
    get_install_count,
    init_name_scheme,
    check_is_single_to_multi_conversion,
    update_name_scheme,
    handle_instance_naming,
    backup_klipper_dir,
)
from components.moonraker.moonraker import Moonraker
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from core.repo_manager.repo_manager import RepoManager
from utils.input_utils import get_confirm
from utils.logger import Logger
from utils.system_utils import (
    parse_packages_from_file,
    create_python_venv,
    install_python_requirements,
    update_system_package_lists,
    install_system_packages,
)


def install_klipper() -> None:
    kl_im = InstanceManager(Klipper)

    # ask to add new instances, if there are existing ones
    if kl_im.instances and not add_to_existing():
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    install_count = get_install_count()
    if install_count is None:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    # create a dict of the size of the existing instances + install count
    name_dict = {c: "" for c in range(len(kl_im.instances) + install_count)}
    name_scheme = init_name_scheme(kl_im.instances, install_count)
    mr_im = InstanceManager(Moonraker)
    name_scheme = update_name_scheme(
        name_scheme, name_dict, kl_im.instances, mr_im.instances
    )

    handle_instance_naming(name_dict, name_scheme)

    create_example_cfg = get_confirm("Create example printer.cfg?")

    try:
        if not kl_im.instances:
            setup_klipper_prerequesites()

        count = 0
        for name in name_dict:
            if name_dict[name] in [n.suffix for n in kl_im.instances]:
                continue

            if check_is_single_to_multi_conversion(kl_im.instances):
                handle_to_multi_instance_conversion(name_dict[name])
                continue

            count += 1
            create_klipper_instance(name_dict[name], create_example_cfg)

            if count == install_count:
                break

        kl_im.reload_daemon()

    except Exception:
        Logger.print_error("Klipper installation failed!")
        return

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
    try:
        install_klipper_packages(KLIPPER_DIR)
        create_python_venv(KLIPPER_ENV_DIR)
        install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQUIREMENTS_TXT)
    except Exception:
        Logger.print_error("Error during installation of Klipper requirements!")
        raise


def install_klipper_packages(klipper_dir: Path) -> None:
    script = klipper_dir.joinpath("scripts/install-debian.sh")
    packages = parse_packages_from_file(script)
    packages = [pkg.replace("python-dev", "python3-dev") for pkg in packages]
    packages.append("python3-venv")
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
        backup_klipper_dir()

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

    # install possible new system packages
    install_klipper_packages(KLIPPER_DIR)
    # install possible new python dependencies
    install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQUIREMENTS_TXT)

    instance_manager.start_all_instance()


def create_klipper_instance(name: str, create_example_cfg: bool) -> None:
    kl_im = InstanceManager(Klipper)
    new_instance = Klipper(suffix=name)
    kl_im.current_instance = new_instance
    kl_im.create_instance()
    kl_im.enable_instance()
    if create_example_cfg:
        # if a client-config is installed, include it in the new example cfg
        client_configs = get_existing_client_config()
        create_example_printer_cfg(new_instance, client_configs)
    kl_im.start_instance()
