#!/usr/bin/env python3

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
from typing import List

from kiauh import KIAUH_CFG
from kiauh.core.backup_manager.backup_manager import BackupManager
from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import (
    print_instance_overview,
    print_update_warn_dialog,
)
from kiauh.core.repo_manager.repo_manager import RepoManager
from kiauh.modules.moonraker import (
    EXIT_MOONRAKER_SETUP,
    DEFAULT_MOONRAKER_REPO_URL,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_REQUIREMENTS_TXT,
    POLKIT_LEGACY_FILE,
    POLKIT_FILE,
    POLKIT_USR_FILE,
    POLKIT_SCRIPT,
    DEFAULT_MOONRAKER_PORT,
    MODULE_PATH,
)
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.modules.moonraker.moonraker_dialogs import print_moonraker_overview
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
    check_file_exists,
    get_ipv4_addr,
)


def run_moonraker_setup(install: bool) -> None:
    kl_im = InstanceManager(Klipper)
    kl_instance_list = kl_im.instances
    kl_instance_count = len(kl_instance_list)
    mr_im = InstanceManager(Moonraker)
    mr_instance_list = mr_im.instances
    mr_instance_count = len(mr_instance_list)

    is_klipper_installed = kl_instance_count > 0
    if install and not is_klipper_installed:
        Logger.print_warn("Klipper not installed!")
        Logger.print_warn("Moonraker cannot be installed! Install Klipper first.")
        return

    is_moonraker_installed = mr_instance_count > 0
    if not install and not is_moonraker_installed:
        Logger.print_warn("Moonraker not installed!")
        return

    if install:
        install_moonraker(mr_im, mr_instance_list, kl_instance_list)

    if not install:
        remove_moonraker(mr_im, mr_instance_list)


def handle_existing_instances(instance_list: List[Klipper]) -> bool:
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_confirm("Add new instances?", allow_go_back=True):
            return False

    return True


def install_moonraker(
    instance_manager: InstanceManager,
    moonraker_instances: List[Moonraker],
    klipper_instances: List[Klipper],
) -> None:
    print_moonraker_overview(
        klipper_instances, moonraker_instances, show_index=True, show_select_all=True
    )

    options = [str(i) for i in range(len(klipper_instances))]
    options.extend(["a", "A", "b", "B"])
    question = "Select Klipper instance to setup Moonraker for"
    selection = get_selection_input(question, options).lower()

    instance_names = []
    if selection == "b":
        Logger.print_status(EXIT_MOONRAKER_SETUP)
        return

    elif selection == "a":
        for instance in klipper_instances:
            instance_names.append(instance.suffix)

    else:
        index = int(selection)
        instance_names.append(klipper_instances[index].suffix)

    create_example_cfg = get_confirm("Create example moonraker.conf?")
    setup_moonraker_prerequesites()
    install_moonraker_polkit()

    ports_in_use = [
        instance.port for instance in moonraker_instances if instance.port is not None
    ]
    for name in instance_names:
        current_instance = Moonraker(suffix=name)

        instance_manager.current_instance = current_instance
        instance_manager.create_instance()
        instance_manager.enable_instance()

        if create_example_cfg:
            cfg_dir = current_instance.cfg_dir
            Logger.print_status(f"Creating example moonraker.conf in '{cfg_dir}'")
            if current_instance.cfg_file is None:
                create_example_moonraker_conf(current_instance, ports_in_use)
                Logger.print_ok(f"Example moonraker.conf created in '{cfg_dir}'")
            else:
                Logger.print_info(f"moonraker.conf in '{cfg_dir}' already exists.")

        instance_manager.start_instance()

    instance_manager.reload_daemon()


def setup_moonraker_prerequesites() -> None:
    cm = ConfigManager(cfg_file=KIAUH_CFG)
    cm.read_config()

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
    install_moonraker_packages(Path(MOONRAKER_DIR))
    create_python_venv(Path(MOONRAKER_ENV_DIR))
    moonraker_py_req = Path(MOONRAKER_REQUIREMENTS_TXT)
    install_python_requirements(Path(MOONRAKER_ENV_DIR), moonraker_py_req)


def install_moonraker_packages(moonraker_dir: Path) -> None:
    script = Path(f"{moonraker_dir}/scripts/install-moonraker.sh")
    packages = parse_packages_from_file(script)
    update_system_package_lists(silent=False)
    install_system_packages(packages)


def install_moonraker_polkit() -> None:
    Logger.print_status("Installing Moonraker policykit rules ...")

    legacy_file_exists = check_file_exists(Path(POLKIT_LEGACY_FILE))
    polkit_file_exists = check_file_exists(Path(POLKIT_FILE))
    usr_file_exists = check_file_exists(Path(POLKIT_USR_FILE))

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


def remove_moonraker(
    instance_manager: InstanceManager, instance_list: List[Moonraker]
) -> None:
    print_instance_overview(instance_list, True, True)

    options = [str(i) for i in range(len(instance_list))]
    options.extend(["a", "A", "b", "B"])

    selection = get_selection_input("Select Moonraker instance to remove", options)

    del_remnants = False
    remove_polkit = False
    instances_to_remove = []
    if selection == "b".lower():
        return
    elif selection == "a".lower():
        question = f"Delete {MOONRAKER_DIR} and {MOONRAKER_ENV_DIR}?"
        del_remnants = get_confirm(question, False, True)
        instances_to_remove.extend(instance_list)
        remove_polkit = True
        Logger.print_status("Removing all Moonraker instances ...")
    else:
        instance = instance_list[int(selection)]
        instance_name = instance.get_service_file_name()
        instances_to_remove.append(instance)
        is_last_instance = len(instance_list) == 1
        if is_last_instance:
            question = f"Delete {MOONRAKER_DIR} and {MOONRAKER_ENV_DIR}?"
            del_remnants = get_confirm(question, False, True)
            remove_polkit = True
        Logger.print_status(f"Removing Moonraker instance {instance_name} ...")

    if del_remnants is None:
        Logger.print_status("Exiting Moonraker Uninstaller ...")
        return

    remove_instances(
        instance_manager,
        instances_to_remove,
        remove_polkit,
        del_remnants,
    )


def remove_instances(
    instance_manager: InstanceManager,
    instance_list: List[Moonraker],
    remove_polkit: bool,
    del_remnants: bool,
) -> None:
    for instance in instance_list:
        instance_manager.current_instance = instance
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=del_remnants)

    if remove_polkit:
        remove_polkit_rules()

    instance_manager.reload_daemon()


def remove_polkit_rules() -> None:
    Logger.print_status("Removing all Moonraker policykit rules ...")
    if not Path(MOONRAKER_DIR).exists():
        log = "Cannot remove policykit rules. Moonraker directory not found."
        Logger.print_warn(log)
        return

    try:
        command = [f"{MOONRAKER_DIR}/scripts/set-policykit-rules.sh", "--clear"]
        subprocess.run(
            command, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, check=True
        )
    except subprocess.CalledProcessError as e:
        Logger.print_error(f"Error while removing policykit rules: {e}")

    Logger.print_ok("Policykit rules successfully removed!")


def update_moonraker() -> None:
    print_update_warn_dialog()
    if not get_confirm("Update Moonraker now?"):
        return

    cm = ConfigManager(cfg_file=KIAUH_CFG)
    cm.read_config()

    if cm.get_value("kiauh", "backup_before_update"):
        backup_manager = BackupManager(source=MOONRAKER_DIR, backup_name="moonraker")
        backup_manager.backup()
        backup_manager.backup_name = "moonraker-env"
        backup_manager.source = MOONRAKER_ENV_DIR
        backup_manager.backup()

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
    instance_manager.start_all_instance()


def create_example_moonraker_conf(instance: Moonraker, ports: List[int]) -> None:
    port = max(ports) + 1 if ports else DEFAULT_MOONRAKER_PORT
    ports.append(port)
    instance.port = port
    example_cfg_path = os.path.join(MODULE_PATH, "res", "moonraker.conf")

    with open(f"{instance.cfg_dir}/moonraker.conf", "w") as cfg:
        cfg.write(_prep_example_moonraker_conf(instance, example_cfg_path))


def _prep_example_moonraker_conf(instance: Moonraker, example_cfg_path: str) -> str:
    try:
        with open(example_cfg_path, "r") as cfg:
            example_cfg_content = cfg.read()
    except FileNotFoundError:
        Logger.print_error(f"Unable to open {example_cfg_path} - File not found")
        raise

    example_cfg_content = example_cfg_content.replace("%PORT%", str(instance.port))
    example_cfg_content = example_cfg_content.replace(
        "%UDS%", f"{instance.comms_dir}/klippy.sock"
    )

    ip = get_ipv4_addr().split(".")[:2]
    ip.extend(["0", "0/16"])
    example_cfg_content = example_cfg_content.replace("%LAN%", ".".join(ip))

    return example_cfg_content
