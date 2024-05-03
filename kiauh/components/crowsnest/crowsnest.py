# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
import textwrap
from pathlib import Path
from subprocess import run, CalledProcessError
from typing import List, Dict, Literal, Union

from components.crowsnest import CROWSNEST_REPO, CROWSNEST_DIR
from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from utils.common import get_install_status, check_install_dependencies
from utils.constants import COLOR_CYAN, RESET_FORMAT, CURRENT_USER
from utils.git_utils import (
    git_clone_wrapper,
    get_repo_name,
    get_local_commit,
    get_remote_commit,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.logger import Logger
from utils.sys_utils import (
    parse_packages_from_file,
    cmd_sysctl_service,
)


def install_crowsnest() -> None:
    # Step 1: Clone crowsnest repo
    git_clone_wrapper(CROWSNEST_REPO, CROWSNEST_DIR, "master")

    # Step 2: Install dependencies
    check_install_dependencies(["make"])

    # Step 3: Check for Multi Instance
    im = InstanceManager(Klipper)
    instances: List[Klipper] = im.find_instances()

    if len(instances) > 1:
        Logger.print_status("Multi instance install detected ...")
        info = textwrap.dedent("""
            Crowsnest is NOT designed to support multi instances.
            A workaround for this is to choose the most used instance as a 'master'
            Use this instance to set up your 'crowsnest.conf' and steering it's service.
            Found the following instances:
            """)[:-1]
        print(info, end="")
        for instance in instances:
            print(f"● {instance.data_dir_name}")

        Logger.print_status("\nLaunching crowsnest's configuration tool ...")

    if not get_confirm("Continue with configuration?", False, allow_go_back=True):
        Logger.print_info("Installation aborted by user ... Exiting!")
        return

    config = Path(CROWSNEST_DIR).joinpath("tools/.config")
    try:
        run(
            "make config",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        if config.exists():
            Path.unlink(config)
        return

    if not config.exists():
        Logger.print_error("Generating .config failed, installation aborted")
        return

    # Step 4: Launch crowsnest installer
    print(f"{COLOR_CYAN}Installer will prompt you for sudo password!{RESET_FORMAT}")
    Logger.print_status("Launching crowsnest installer ...")
    try:
        run(
            f"sudo make install BASE_USER={CURRENT_USER}",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        return


def update_crowsnest() -> None:
    try:
        cmd_sysctl_service("crowsnest", "stop")

        if not CROWSNEST_DIR.exists():
            git_clone_wrapper(CROWSNEST_REPO, CROWSNEST_DIR, "master")
        else:
            Logger.print_status("Updating Crowsnest ...")

            git_pull_wrapper(CROWSNEST_REPO, CROWSNEST_DIR)

            script = CROWSNEST_DIR.joinpath("tools/install.sh")
            deps = parse_packages_from_file(script)
            check_install_dependencies(deps)

        cmd_sysctl_service("crowsnest", "restart")

        Logger.print_ok("Crowsnest updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        return


def get_crowsnest_status() -> (
    Dict[
        Literal["status", "status_code", "repo", "local", "remote"],
        Union[str, int],
    ]
):
    files = [
        Path("/usr/local/bin/crowsnest"),
        Path("/etc/logrotate.d/crowsnest"),
        Path("/etc/systemd/system/crowsnest.service"),
    ]
    status = get_install_status(CROWSNEST_DIR, files)
    return {
        "status": status.get("status"),
        "status_code": status.get("status_code"),
        "repo": get_repo_name(CROWSNEST_DIR),
        "local": get_local_commit(CROWSNEST_DIR),
        "remote": get_remote_commit(CROWSNEST_DIR),
    }


def remove_crowsnest() -> None:
    if not CROWSNEST_DIR.exists():
        Logger.print_info("Crowsnest does not seem to be installed! Skipping ...")
        return

    try:
        run(
            "make uninstall",
            cwd=CROWSNEST_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        return

    Logger.print_status("Removing crowsnest directory ...")
    shutil.rmtree(CROWSNEST_DIR)
    Logger.print_ok("Directory removed!")
