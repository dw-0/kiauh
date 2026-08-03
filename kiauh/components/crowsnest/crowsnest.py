# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import shutil
import time
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List

from components.crowsnest import (
    CROWSNEST_BIN_FILE,
    CROWSNEST_DEPS_JSON_FILE,
    CROWSNEST_DIR,
    CROWSNEST_ENV_DIR,
    CROWSNEST_INSTALL_SCRIPT,
    CROWSNEST_LOGROTATE_FILE,
    CROWSNEST_MULTI_CONFIG,
    CROWSNEST_REPO,
    CROWSNEST_SERVICE_FILE,
    CROWSNEST_SERVICE_NAME,
)
from components.klipper.klipper import Klipper
from components.moonraker.utils.sysdeps_parser import SysDepsParser
from components.moonraker.utils.utils import load_sysdeps_json
from core.i18n import _tr
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings
from core.types.component_status import ComponentStatus
from utils.common import (
    check_install_dependencies,
    get_install_status,
)
from utils.git_utils import (
    get_current_branch,
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_service,
    parse_packages_from_file,
)


def install_crowsnest() -> None:
    git_clone_wrapper(CROWSNEST_REPO, CROWSNEST_DIR)

    check_install_dependencies({"make"})

    instances: List[Klipper] = get_instances(Klipper)

    if len(instances) > 1:
        print_multi_instance_warning(instances)

        if not get_confirm(_tr("Do you want to continue with the installation?")):
            Logger.print_info(_tr("Crowsnest installation aborted!"))
            return

        Logger.print_status(_tr("Launching crowsnest's install configurator ..."))
        time.sleep(3)
        configure_multi_instance()

    Logger.print_status(_tr("Launching crowsnest installer ..."))
    Logger.print_info(_tr("Installer will prompt you for sudo password!"))
    try:
        run(
            "sudo make install",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(_tr("Something went wrong! Please try again...\n{}").format(e))
        return


def print_multi_instance_warning(instances: List[Klipper]) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            _tr("Multi instance install detected!"),
            "\n\n",
            _tr("Crowsnest is NOT designed to support multi instances. A workaround "
                "for this is to choose the most used instance as a 'master' and use "
                "this instance to set up your 'crowsnest.conf' and steering it's service."),
            "\n\n",
            _tr("The following instances were found:"),
            *[_tr("● {}").format(instance.data_dir.name) for instance in instances],
        ],
    )


def configure_multi_instance() -> None:
    try:
        run(
            "make config",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(_tr("Something went wrong! Please try again...\n{}").format(e))
        if CROWSNEST_MULTI_CONFIG.exists():
            Path.unlink(CROWSNEST_MULTI_CONFIG)
        return

    if not CROWSNEST_MULTI_CONFIG.exists():
        Logger.print_error(_tr("Generating .config failed, installation aborted"))


def update_crowsnest() -> None:
    try:
        cmd_sysctl_service(CROWSNEST_SERVICE_NAME, "stop")

        if not CROWSNEST_DIR.exists():
            git_clone_wrapper(CROWSNEST_REPO, CROWSNEST_DIR, "master")
        else:
            Logger.print_status(_tr("Updating Crowsnest ..."))

            settings = KiauhSettings()
            if settings.kiauh.backup_before_update:
                svc = BackupService()
                svc.backup_directory(
                    source_path=CROWSNEST_DIR,
                    target_path="crowsnest",
                    backup_name="crowsnest",
                )

            git_pull_wrapper(CROWSNEST_DIR)

            install_crowsnest_packages()

        cmd_sysctl_service(CROWSNEST_SERVICE_NAME, "restart")

        Logger.print_ok(_tr("Crowsnest updated successfully."), end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(_tr("Something went wrong! Please try again...\n{}").format(e))
        return


def get_crowsnest_status() -> ComponentStatus:
    files_dict = {
        4: [
            CROWSNEST_BIN_FILE,
            CROWSNEST_LOGROTATE_FILE,
            CROWSNEST_SERVICE_FILE,
        ],
        5: [CROWSNEST_SERVICE_FILE],
    }
    version = get_crowsnest_version()

    non_existant = CROWSNEST_DIR.joinpath("non_existant")
    files = files_dict.get(version, [non_existant])

    env_dir = None
    if version >= 5:
        env_dir = CROWSNEST_ENV_DIR
    return get_install_status(CROWSNEST_DIR, files=files, env_dir=env_dir)


def get_crowsnest_version() -> int:
    version = get_current_branch(CROWSNEST_DIR)
    if version is None:
        return 0
    if version == "master":
        return 4
    return int(version.removeprefix("v"))


def install_crowsnest_packages() -> None:
    Logger.print_status(_tr("Parsing Crowsnest system dependencies  ..."))

    crowsnest_deps = []
    crowsnest_version = get_crowsnest_version()
    if crowsnest_version >= 5 and CROWSNEST_DEPS_JSON_FILE.exists():
        Logger.print_info(
            _tr("Parsing system dependencies from {} ...").format(
                CROWSNEST_DEPS_JSON_FILE.name
            )
        )
        parser = SysDepsParser()
        sysdeps = load_sysdeps_json(CROWSNEST_DEPS_JSON_FILE)
        crowsnest_deps.extend(parser.parse_dependencies(sysdeps))

    elif crowsnest_version <= 4 and CROWSNEST_INSTALL_SCRIPT.exists():
        Logger.print_info(
            _tr("Parsing system dependencies from {} ...").format(
                CROWSNEST_INSTALL_SCRIPT.name
            )
        )
        crowsnest_deps = parse_packages_from_file(CROWSNEST_INSTALL_SCRIPT)

    if not crowsnest_deps:
        raise ValueError(_tr("Error parsing crowsnest dependencies!"))

    check_install_dependencies({*crowsnest_deps})


def remove_crowsnest() -> None:
    if not CROWSNEST_DIR.exists():
        Logger.print_info(_tr("Crowsnest does not seem to be installed! Skipping ..."))
        return

    try:
        run(
            "make uninstall",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(_tr("Something went wrong! Please try again...\n{}").format(e))
        return

    Logger.print_status(_tr("Removing crowsnest directory ..."))
    shutil.rmtree(CROWSNEST_DIR)
    Logger.print_ok(_tr("Directory removed!"))
