# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path

from components.klipper import (
    EXIT_KLIPPER_SETUP,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_INSTALL_SCRIPT,
    KLIPPER_REQ_FILE,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_utils import (
    add_to_existing,
    backup_klipper_dir,
    check_is_single_to_multi_conversion,
    check_user_groups,
    create_example_printer_cfg,
    get_install_count,
    handle_disruptive_system_packages,
    handle_instance_naming,
    handle_to_multi_instance_conversion,
    init_name_scheme,
    update_name_scheme,
)
from components.moonraker.moonraker import Moonraker
from components.webui_client.client_utils import (
    get_existing_clients,
)
from core.instance_manager.instance_manager import InstanceManager
from core.settings.kiauh_settings import KiauhSettings
from utils.common import check_install_dependencies
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.logger import DialogType, Logger
from utils.sys_utils import (
    cmd_sysctl_manage,
    create_python_venv,
    install_python_requirements,
    parse_packages_from_file,
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
            check_install_dependencies(["git"])
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

        cmd_sysctl_manage("daemon-reload")

    except Exception as e:
        Logger.print_error(e)
        Logger.print_error("Klipper installation failed!")
        return

    # step 4: check/handle conflicting packages/services
    handle_disruptive_system_packages()

    # step 5: check for required group membership
    check_user_groups()


def setup_klipper_prerequesites() -> None:
    settings = KiauhSettings()
    repo = settings.klipper.repo_url
    branch = settings.klipper.branch

    git_clone_wrapper(repo, KLIPPER_DIR, branch)

    # install klipper dependencies and create python virtualenv
    try:
        install_klipper_packages()
        create_python_venv(KLIPPER_ENV_DIR)
        install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
    except Exception:
        Logger.print_error("Error during installation of Klipper requirements!")
        raise


def install_klipper_packages() -> None:
    script = KLIPPER_INSTALL_SCRIPT
    packages = parse_packages_from_file(script)
    packages.append("python3-venv")  # todo: remove once switched to virtualenv

    # Add dbus requirement for DietPi distro
    if Path("/boot/dietpi/.version").exists():
        packages.append("dbus")

    check_install_dependencies(packages)


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

    instance_manager = InstanceManager(Klipper)
    instance_manager.stop_all_instance()

    git_pull_wrapper(repo=settings.klipper.repo_url, target_dir=KLIPPER_DIR)

    # install possible new system packages
    install_klipper_packages()
    # install possible new python dependencies
    install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)

    instance_manager.start_all_instance()


def create_klipper_instance(name: str, create_example_cfg: bool) -> None:
    kl_im = InstanceManager(Klipper)
    new_instance = Klipper(suffix=name)
    kl_im.current_instance = new_instance
    kl_im.create_instance()
    kl_im.enable_instance()
    if create_example_cfg:
        # if a client-config is installed, include it in the new example cfg
        clients = get_existing_clients()
        create_example_printer_cfg(new_instance, clients)
    kl_im.start_instance()
