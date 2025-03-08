# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import subprocess
from typing import List

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
from components.moonraker.services.moonraker_instance_service import (
    MoonrakerInstanceService,
)
from components.moonraker.utils.sysdeps_parser import SysDepsParser
from components.moonraker.utils.utils import (
    backup_moonraker_dir,
    create_example_moonraker_conf,
    load_sysdeps_json,
)
from components.webui_client.client_utils import (
    enable_mainsail_remotemode,
    get_existing_clients,
)
from components.webui_client.mainsail_data import MainsailData
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.common import check_install_dependencies
from utils.fs_utils import check_file_exist
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import (
    get_confirm,
    get_selection_input,
)
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    get_ipv4_addr,
    install_python_requirements,
    parse_packages_from_file,
)


def install_moonraker() -> None:
    klipper_list: List[Klipper] = get_instances(Klipper)

    if not check_moonraker_install_requirements(klipper_list):
        return

    instance_service = MoonrakerInstanceService()
    instance_service.load_instances()

    moonraker_list: List[Moonraker] = instance_service.get_all_instances()
    new_instances: List[Moonraker] = []
    selected_option: str | Klipper

    if len(klipper_list) == 1:
        suffix: str = klipper_list[0].suffix
        new_inst = instance_service.create_new_instance(suffix)
        new_instances.append(new_inst)

    else:
        print_moonraker_overview(
            klipper_list,
            moonraker_list,
            show_index=True,
            show_select_all=True,
        )
        options = {str(i + 1): k for i, k in enumerate(klipper_list)}
        additional_options = {"a": None, "b": None}
        options = {**options, **additional_options}
        question = "Select Klipper instance to setup Moonraker for"
        selected_option = get_selection_input(question, options)

        if selected_option == "b":
            Logger.print_status(EXIT_MOONRAKER_SETUP)
            return

        if selected_option == "a":
            new_inst_list: List[Moonraker] = [
                instance_service.create_new_instance(k.suffix) for k in klipper_list
            ]
            new_instances.extend(new_inst_list)
        else:
            klipper_instance: Klipper | None = options.get(selected_option)
            if klipper_instance is None:
                raise Exception("Error selecting instance!")
            new_inst = instance_service.create_new_instance(klipper_instance.suffix)
            new_instances.append(new_inst)

    create_example_cfg = get_confirm("Create example moonraker.conf?")

    try:
        check_install_dependencies()
        setup_moonraker_prerequesites()
        install_moonraker_polkit()

        ports_map = instance_service.get_instance_port_map()
        for instance in new_instances:
            instance.create()
            cmd_sysctl_service(instance.service_file_path.name, "enable")

            if create_example_cfg:
                # if a webclient and/or it's config is installed, patch
                # its update section to the config
                clients = get_existing_clients()
                create_example_moonraker_conf(instance, ports_map, clients)

            cmd_sysctl_service(instance.service_file_path.name, "start")

        cmd_sysctl_manage("daemon-reload")

        # if mainsail is installed, and we installed
        # multiple moonraker instances, we enable mainsails remote mode
        if MainsailData().client_dir.exists() and len(moonraker_list) > 1:
            enable_mainsail_remotemode()

        instance_service.load_instances()
        new_instances = [
            instance_service.get_instance_by_suffix(i.suffix) for i in new_instances
        ]

        ip: str = get_ipv4_addr()
        # noinspection HttpUrlsUsage
        url_list = [
            f"● {i.service_file_path.stem}: http://{ip}:{i.port}"
            for i in new_instances
            if i.port
        ]
        dialog_content = []
        if url_list:
            dialog_content.append("You can access Moonraker via the following URL:")
            dialog_content.extend(url_list)

        Logger.print_dialog(
            DialogType.CUSTOM,
            custom_title="Moonraker successfully installed!",
            custom_color=Color.GREEN,
            content=dialog_content,
        )

    except Exception as e:
        Logger.print_error(f"Error while installing Moonraker: {e}")
        return


def check_moonraker_install_requirements(klipper_list: List[Klipper]) -> bool:
    def check_klipper_instances() -> bool:
        if len(klipper_list) >= 1:
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
    if create_python_venv(MOONRAKER_ENV_DIR):
        install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)
        install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_SPEEDUPS_REQ_FILE)


def install_moonraker_packages() -> None:
    Logger.print_status("Parsing Moonraker system dependencies  ...")

    moonraker_deps = []
    if MOONRAKER_DEPS_JSON_FILE.exists():
        Logger.print_info(
            f"Parsing system dependencies from {MOONRAKER_DEPS_JSON_FILE.name} ..."
        )
        parser = SysDepsParser()
        sysdeps = load_sysdeps_json(MOONRAKER_DEPS_JSON_FILE)
        moonraker_deps.extend(parser.parse_dependencies(sysdeps))

    elif MOONRAKER_INSTALL_SCRIPT.exists():
        Logger.print_warn(f"{MOONRAKER_DEPS_JSON_FILE.name} not found!")
        Logger.print_info(
            f"Parsing system dependencies from {MOONRAKER_INSTALL_SCRIPT.name} ..."
        )
        moonraker_deps = parse_packages_from_file(MOONRAKER_INSTALL_SCRIPT)

    if not moonraker_deps:
        raise ValueError("Error parsing Moonraker dependencies!")

    check_install_dependencies({*moonraker_deps})


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

    instances = get_instances(Moonraker)
    InstanceManager.stop_all(instances)

    git_pull_wrapper(repo=settings.moonraker.repo_url, target_dir=MOONRAKER_DIR)

    # install possible new system packages
    install_moonraker_packages()
    # install possible new python dependencies
    install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)

    InstanceManager.start_all(instances)
