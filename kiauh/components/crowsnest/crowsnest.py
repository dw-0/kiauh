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
from typing import List

from components.crowsnest import CROWSNEST_REPO, CROWSNEST_DIR
from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from utils.constants import COLOR_CYAN, RESET_FORMAT, CURRENT_USER
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_confirm
from utils.logger import Logger
from utils.system_utils import check_package_install, install_system_packages


def install_crowsnest() -> None:
    # Step 1: Clone crowsnest repo
    git_clone_wrapper(CROWSNEST_REPO, "master", CROWSNEST_DIR)

    # Step 2: Install dependencies
    requirements: List[str] = check_package_install(["make"])
    if requirements:
        install_system_packages(requirements)

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
    pass


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
