#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import subprocess
import sys
from pathlib import Path
from typing import List

from kiauh import KIAUH_CFG
from kiauh.components.klipper.klipper import Klipper
from kiauh.components.klipper.klipper_dialogs import print_instance_overview
from kiauh.components.mainsail import MAINSAIL_DIR
from kiauh.components.mainsail.mainsail_utils import enable_mainsail_remotemode
from kiauh.components.moonraker import (
    EXIT_MOONRAKER_SETUP,
    DEFAULT_MOONRAKER_REPO_URL,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_REQUIREMENTS_TXT,
    POLKIT_LEGACY_FILE,
    POLKIT_FILE,
    POLKIT_USR_FILE,
    POLKIT_SCRIPT,
)
from kiauh.components.moonraker.moonraker import Moonraker
from kiauh.components.moonraker.moonraker_dialogs import print_moonraker_overview
from kiauh.components.moonraker.moonraker_utils import (
    create_example_moonraker_conf,
    backup_moonraker_dir,
)
from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.utils.filesystem_utils import check_file_exist
from kiauh.utils.input_utils import (
    get_confirm,
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


def install_moonraker() -> None:
    if not check_moonraker_install_requirements():
        return

    kl_im = InstanceManager(Klipper)
    klipper_instances = kl_im.instances
    mr_im = InstanceManager(Moonraker)
    moonraker_instances = mr_im.instances

    selected_klipper_instance = 0
    if len(klipper_instances) > 1:
        print_moonraker_overview(
            klipper_instances,
            moonraker_instances,
            show_index=True,
            show_select_all=True,
        )
        options = [str(i) for i in range(len(klipper_instances))]
        options.extend(["a", "A", "b", "B"])
        question = "Select Klipper instance to setup Moonraker for"
        selected_klipper_instance = get_selection_input(question, options).lower()

    instance_names = []
    if selected_klipper_instance == "b":
        Logger.print_status(EXIT_MOONRAKER_SETUP)
        return

    elif selected_klipper_instance == "a":
        for instance in klipper_instances:
            instance_names.append(instance.suffix)

    else:
        index = int(selected_klipper_instance)
        instance_names.append(klipper_instances[index].suffix)

    create_example_cfg = get_confirm("Create example moonraker.conf?")
    setup_moonraker_prerequesites()
    install_moonraker_polkit()

    used_ports_map = {
        instance.suffix: instance.port for instance in moonraker_instances
    }
    for name in instance_names:
        current_instance = Moonraker(suffix=name)

        mr_im.current_instance = current_instance
        mr_im.create_instance()
        mr_im.enable_instance()

        if create_example_cfg:
            create_example_moonraker_conf(current_instance, used_ports_map)

        mr_im.start_instance()

    mr_im.reload_daemon()

    # if mainsail is installed, and we installed
    # multiple moonraker instances, we enable mainsails remote mode
    if MAINSAIL_DIR.exists() and len(mr_im.instances) > 1:
        enable_mainsail_remotemode()


def check_moonraker_install_requirements() -> bool:
    if not (sys.version_info.major >= 3 and sys.version_info.minor >= 7):
        Logger.print_error("Versioncheck failed!")
        Logger.print_error("Python 3.7 or newer required to run Moonraker.")
        return False

    kl_instance_count = len(InstanceManager(Klipper).instances)
    if kl_instance_count < 1:
        Logger.print_warn("Klipper not installed!")
        Logger.print_warn("Moonraker cannot be installed! Install Klipper first.")
        return False

    mr_instance_count = len(InstanceManager(Moonraker).instances)
    if mr_instance_count >= kl_instance_count:
        Logger.print_warn("Unable to install more Moonraker instances!")
        Logger.print_warn("More Klipper instances required.")
        return False

    return True


def setup_moonraker_prerequesites() -> None:
    cm = ConfigManager(cfg_file=KIAUH_CFG)
    repo = str(
        cm.get_value("moonraker", "repository_url") or DEFAULT_MOONRAKER_REPO_URL
    )
    branch = str(cm.get_value("moonraker", "branch") or "master")

    repo_manager = RepoManager(
        repo=repo,
        branch=branch,
        target_dir=MOONRAKER_DIR,
    )
    repo_manager.clone_repo()

    # install moonraker dependencies and create python virtualenv
    install_moonraker_packages(MOONRAKER_DIR)
    create_python_venv(MOONRAKER_ENV_DIR)
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQUIREMENTS_TXT)


def install_moonraker_packages(moonraker_dir: Path) -> None:
    script = moonraker_dir.joinpath("scripts/install-moonraker.sh")
    packages = parse_packages_from_file(script)
    update_system_package_lists(silent=False)
    install_system_packages(packages)


def install_moonraker_polkit() -> None:
    Logger.print_status("Installing Moonraker policykit rules ...")

    legacy_file_exists = check_file_exist(POLKIT_LEGACY_FILE, True)
    polkit_file_exists = check_file_exist(POLKIT_FILE, True)
    usr_file_exists = check_file_exist(POLKIT_USR_FILE, True)

    if legacy_file_exists or (polkit_file_exists and usr_file_exists):
        Logger.print_info("Moonraker policykit rules are already installed.")
        return

    try:
        command = [POLKIT_SCRIPT, "--disable-systemctl"]
        result = subprocess.run(
            command, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True
        )
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Installing Moonraker policykit rules failed!")
            return

        Logger.print_ok("Moonraker policykit rules successfully installed!")
    except subprocess.CalledProcessError as e:
        log = f"Error while installing Moonraker policykit rules: {e.stderr.decode()}"
        Logger.print_error(log)


def handle_existing_instances(instance_list: List[Klipper]) -> bool:
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_confirm("Add new instances?", allow_go_back=True):
            return False

    return True


def update_moonraker() -> None:
    if not get_confirm("Update Moonraker now?"):
        return

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    if cm.get_value("kiauh", "backup_before_update"):
        backup_moonraker_dir()

    instance_manager = InstanceManager(Moonraker)
    instance_manager.stop_all_instance()

    repo = str(
        cm.get_value("moonraker", "repository_url") or DEFAULT_MOONRAKER_REPO_URL
    )
    branch = str(cm.get_value("moonraker", "branch") or "master")

    repo_manager = RepoManager(
        repo=repo,
        branch=branch,
        target_dir=MOONRAKER_DIR,
    )
    repo_manager.pull_repo()

    # install possible new system packages
    install_moonraker_packages(MOONRAKER_DIR)
    # install possible new python dependencies
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQUIREMENTS_TXT)

    instance_manager.start_all_instance()
