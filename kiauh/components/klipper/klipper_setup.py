# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from components.klipper import (
    EXIT_KLIPPER_SETUP,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_INSTALL_SCRIPT,
    KLIPPER_REQ_FILE,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    print_select_custom_name_dialog,
)
from components.klipper.klipper_utils import (
    assign_custom_name,
    backup_klipper_dir,
    check_user_groups,
    create_example_printer_cfg,
    get_install_count,
    handle_disruptive_system_packages,
)
from components.moonraker.moonraker import Moonraker
from components.webui_client.client_utils import (
    get_existing_clients,
)
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from utils.common import check_install_dependencies
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
    parse_packages_from_file,
)


def install_klipper() -> None:
    Logger.print_status("Installing Klipper ...")

    klipper_list: List[Klipper] = get_instances(Klipper)
    moonraker_list: List[Moonraker] = get_instances(Moonraker)
    match_moonraker: bool = False

    # if there are more moonraker instances than klipper instances, ask the user to
    # match the klipper instance count to the count of moonraker instances with the same suffix
    if len(moonraker_list) > len(klipper_list):
        is_confirmed = display_moonraker_info(moonraker_list)
        if not is_confirmed:
            Logger.print_status(EXIT_KLIPPER_SETUP)
            return
        match_moonraker = True

    install_count, name_dict = get_install_count_and_name_dict(
        klipper_list, moonraker_list
    )

    if install_count == 0:
        Logger.print_status(EXIT_KLIPPER_SETUP)
        return

    is_multi_install = install_count > 1 or (len(name_dict) >= 1 and install_count >= 1)
    if not name_dict and install_count == 1:
        name_dict = {0: ""}
    elif is_multi_install and not match_moonraker:
        custom_names = use_custom_names_or_go_back()
        if custom_names is None:
            Logger.print_status(EXIT_KLIPPER_SETUP)
            return

        handle_instance_names(install_count, name_dict, custom_names)

    create_example_cfg = get_confirm("Create example printer.cfg?")
    # run the actual installation
    try:
        run_klipper_setup(klipper_list, name_dict, create_example_cfg)
    except Exception as e:
        Logger.print_error(e)
        Logger.print_error("Klipper installation failed!")
        return


def run_klipper_setup(
    klipper_list: List[Klipper], name_dict: Dict[int, str], create_example_cfg: bool
) -> None:
    if not klipper_list:
        setup_klipper_prerequesites()

    for i in name_dict:
        # skip this iteration if there is already an instance with the name
        if name_dict[i] in [n.suffix for n in klipper_list]:
            continue

        instance = Klipper(suffix=name_dict[i])
        instance.create()
        cmd_sysctl_service(instance.service_file_path.name, "enable")

        if create_example_cfg:
            # if a client-config is installed, include it in the new example cfg
            clients = get_existing_clients()
            create_example_printer_cfg(instance, clients)

        cmd_sysctl_service(instance.service_file_path.name, "start")

    cmd_sysctl_manage("daemon-reload")

    # step 4: check/handle conflicting packages/services
    handle_disruptive_system_packages()

    # step 5: check for required group membership
    check_user_groups()


def handle_instance_names(
    install_count: int, name_dict: Dict[int, str], custom_names: bool
) -> None:
    for i in range(install_count):  # 3
        key: int = len(name_dict.keys()) + 1
        if custom_names:
            assign_custom_name(key, name_dict)
        else:
            name_dict[key] = str(len(name_dict) + 1)


def get_install_count_and_name_dict(
    klipper_list: List[Klipper], moonraker_list: List[Moonraker]
) -> Tuple[int, Dict[int, str]]:
    install_count: int | None
    if len(moonraker_list) > len(klipper_list):
        install_count = len(moonraker_list)
        name_dict = {i: moonraker.suffix for i, moonraker in enumerate(moonraker_list)}
    else:
        install_count = get_install_count()
        name_dict = {i: klipper.suffix for i, klipper in enumerate(klipper_list)}

        if install_count is None:
            Logger.print_status(EXIT_KLIPPER_SETUP)
            return 0, {}

    return install_count, name_dict


def setup_klipper_prerequesites() -> None:
    settings = KiauhSettings()
    repo = settings.klipper.repo_url
    branch = settings.klipper.branch

    git_clone_wrapper(repo, KLIPPER_DIR, branch)

    # install klipper dependencies and create python virtualenv
    try:
        install_klipper_packages()
        if create_python_venv(KLIPPER_ENV_DIR):
            install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
    except Exception:
        Logger.print_error("Error during installation of Klipper requirements!")
        raise


def install_klipper_packages() -> None:
    script = KLIPPER_INSTALL_SCRIPT
    packages = parse_packages_from_file(script)

    # Add dbus requirement for DietPi distro
    if Path("/boot/dietpi/.version").exists():
        packages.append("dbus")

    check_install_dependencies({*packages})


def update_klipper() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "Do NOT continue if there are ongoing prints running!",
            "All Klipper instances will be restarted during the update process and "
            "ongoing prints WILL FAIL.",
        ],
    )

    if not get_confirm("Update Klipper now?"):
        return

    settings = KiauhSettings()
    if settings.kiauh.backup_before_update:
        backup_klipper_dir()

    instances = get_instances(Klipper)
    InstanceManager.stop_all(instances)

    git_pull_wrapper(repo=settings.klipper.repo_url, target_dir=KLIPPER_DIR)

    # install possible new system packages
    install_klipper_packages()
    # install possible new python dependencies
    install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)

    InstanceManager.start_all(instances)


def use_custom_names_or_go_back() -> bool | None:
    print_select_custom_name_dialog()
    _input: bool | None = get_confirm(
        "Assign custom names?",
        False,
        allow_go_back=True,
    )
    return _input


def display_moonraker_info(moonraker_list: List[Moonraker]) -> bool:
    # todo: only show the klipper instances that are not already installed
    Logger.print_dialog(
        DialogType.INFO,
        [
            "Existing Moonraker instances detected:",
            *[f"● {m.service_file_path.stem}" for m in moonraker_list],
            "\n\n",
            "The following Klipper instances will be installed:",
            *[f"● klipper-{m.suffix}" for m in moonraker_list],
        ],
    )
    _input: bool = get_confirm("Proceed with installation?")
    return _input
