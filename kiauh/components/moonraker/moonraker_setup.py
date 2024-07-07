# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import json
import subprocess

from components.klipper.klipper import Klipper
from components.moonraker import (
    EXIT_MOONRAKER_SETUP,
    MOONRAKER_DEPS_JSON_FILE,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_INSTALL_SCRIPT,
    MOONRAKER_REQ_FILE,
    MOONRAKER_SPEEDUPS_REQ_FILE,
    POLKIT_FILE,
    POLKIT_LEGACY_FILE,
    POLKIT_SCRIPT,
    POLKIT_USR_FILE,
)
from components.moonraker.moonraker import Moonraker
from components.moonraker.moonraker_dialogs import print_moonraker_overview
from components.moonraker.moonraker_utils import (
    backup_moonraker_dir,
    create_example_moonraker_conf,
)
from components.webui_client.client_utils import (
    enable_mainsail_remotemode,
    get_existing_clients,
)
from components.webui_client.mainsail_data import MainsailData
from core.instance_manager.instance_manager import InstanceManager
from core.settings.kiauh_settings import KiauhSettings
from utils.common import check_install_dependencies
from utils.fs_utils import check_file_exist
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import (
    get_confirm,
    get_selection_input,
)
from utils.logger import Logger
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_manage,
    create_python_venv,
    install_python_requirements,
    parse_packages_from_file,
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

    try:
        check_install_dependencies()
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
                # if a webclient and/or it's config is installed, patch
                # its update section to the config
                clients = get_existing_clients()
                create_example_moonraker_conf(current_instance, used_ports_map, clients)

            mr_im.start_instance()

        cmd_sysctl_manage("daemon-reload")

        # if mainsail is installed, and we installed
        # multiple moonraker instances, we enable mainsails remote mode
        if MainsailData().client_dir.exists() and len(mr_im.instances) > 1:
            enable_mainsail_remotemode()

    except Exception as e:
        Logger.print_error(f"Error while installing Moonraker: {e}")
        return


def check_moonraker_install_requirements() -> bool:
    def check_klipper_instances() -> bool:
        if len(InstanceManager(Klipper).instances) >= 1:
            return True

        Logger.print_warn("Klipper not installed!")
        Logger.print_warn("Moonraker cannot be installed! Install Klipper first.")
        return False

    return check_python_version(3, 7) and check_klipper_instances()


def setup_moonraker_prerequesites() -> None:
    settings = KiauhSettings()
    repo = settings.moonraker.repo_url
    branch = settings.moonraker.branch

    git_clone_wrapper(repo, MOONRAKER_DIR, branch)

    # install moonraker dependencies and create python virtualenv
    install_moonraker_packages()
    create_python_venv(MOONRAKER_ENV_DIR)
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_SPEEDUPS_REQ_FILE)


def install_moonraker_packages() -> None:
    moonraker_deps = []

    if MOONRAKER_DEPS_JSON_FILE.exists():
        with open(MOONRAKER_DEPS_JSON_FILE, "r") as deps:
            moonraker_deps = json.load(deps).get("debian", [])
    elif MOONRAKER_INSTALL_SCRIPT.exists():
        moonraker_deps = parse_packages_from_file(MOONRAKER_INSTALL_SCRIPT)

    if not moonraker_deps:
        raise ValueError("Error reading Moonraker dependencies!")

    check_install_dependencies(moonraker_deps)


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
            command,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Installing Moonraker policykit rules failed!")
            return

        Logger.print_ok("Moonraker policykit rules successfully installed!")
    except subprocess.CalledProcessError as e:
        log = f"Error while installing Moonraker policykit rules: {e.stderr.decode()}"
        Logger.print_error(log)


def update_moonraker() -> None:
    if not get_confirm("Update Moonraker now?"):
        return

    settings = KiauhSettings()
    if settings.kiauh.backup_before_update:
        backup_moonraker_dir()

    instance_manager = InstanceManager(Moonraker)
    instance_manager.stop_all_instance()

    git_pull_wrapper(repo=settings.moonraker.repo_url, target_dir=MOONRAKER_DIR)

    # install possible new system packages
    install_moonraker_packages()
    # install possible new python dependencies
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)

    instance_manager.start_all_instance()
