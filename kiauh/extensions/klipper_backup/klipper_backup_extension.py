# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess
from typing import List

from components.klipper.klipper import Klipper
from core.backup_manager.backup_manager import BackupManager
from extensions.base_extension import BaseExtension
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from extensions.klipper_backup import (
    EXTENSION_TARGET_PATH,
    EXTENSION_SRC,
    KLIPPER_DIR,
    DEFAULT_KLIPPERBACKUP_REPO_URL,
    KLIPPERBACKUP_DIR,
    KLIPPERBACKUP_CONFIG_DIR,
    EXAMPLE_CFG_SRC,
    KLIPPER_EXTRAS,
)
from utils.filesystem_utils import check_file_exist
from utils.input_utils import get_confirm
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class KlipperbackupExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        if not KLIPPERBACKUP_DIR.exists():
            subprocess.run(["git", "clone", str(DEFAULT_KLIPPERBACKUP_REPO_URL), str(KLIPPERBACKUP_DIR)])
            subprocess.run(["git", "-C", str(KLIPPERBACKUP_DIR), "checkout", "installer-dev"])
            subprocess.run(["chmod", "+x", str(KLIPPERBACKUP_DIR / "install.sh")])
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "kiauh", "install_repo"])

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return
        else:
            subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "kiauh", "check_updates"])

    def remove_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        question = "Do you really want to remove the extension?"
        if get_confirm(question, True, False):
            try:
                Logger.print_status(f"Removing '{EXTENSION_TARGET_PATH}' ...")
                shutil.rmtree(EXTENSION_TARGET_PATH)
                config_backup_exists = check_file_exist(KLIPPERBACKUP_CONFIG_DIR)
                if config_backup_exists:
                    shutil.rmtree(KLIPPERBACKUP_CONFIG_DIR)
                Logger.print_ok("Extension successfully removed!")
            except OSError as e:
                Logger.print_error(f"Unable to remove extension: {e}")
