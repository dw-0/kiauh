#!/usr/bin/env python3

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
from typing import List

from components.klipper.klipper import Klipper
from core.backup_manager.backup_manager import BackupManager
from core.base_extension import BaseExtension
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from extensions.gcode_shell_cmd import (
    EXTENSION_TARGET_PATH,
    EXTENSION_SRC,
    KLIPPER_DIR,
    EXAMPLE_CFG_SRC,
    KLIPPER_EXTRAS,
)
from utils.filesystem_utils import check_file_exist
from utils.input_utils import get_confirm
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class GcodeShellCmdExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        install_example = get_confirm("Create an example shell command?", False, False)

        klipper_dir_exists = check_file_exist(KLIPPER_DIR)
        if not klipper_dir_exists:
            Logger.print_warn(
                "No Klipper directory found! Unable to install extension."
            )
            return

        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        overwrite = True
        if extension_installed:
            overwrite = get_confirm(
                "Extension seems to be installed already. Overwrite?", True, False
            )

        if not overwrite:
            Logger.print_warn("Installation aborted due to user request.")
            return

        im = InstanceManager(Klipper)
        im.stop_all_instance()

        try:
            Logger.print_status(f"Copy extension to '{KLIPPER_EXTRAS}' ...")
            shutil.copy(EXTENSION_SRC, EXTENSION_TARGET_PATH)
        except OSError as e:
            Logger.print_error(f"Unable to install extension: {e}")
            return

        if install_example:
            self.install_example_cfg(im.instances)

        im.start_all_instance()

        Logger.print_ok("Installing G-Code Shell Command extension successfull!")

    def remove_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        question = "Do you really want to remove the extension?"
        if get_confirm(question, True, False):
            try:
                Logger.print_status(f"Removing '{EXTENSION_TARGET_PATH}' ...")
                os.remove(EXTENSION_TARGET_PATH)
                Logger.print_ok("Extension successfully removed!")
            except OSError as e:
                Logger.print_error(f"Unable to remove extension: {e}")

            Logger.print_warn("PLEASE NOTE:")
            Logger.print_warn(
                "Remaining gcode shell command will cause Klipper to throw an error."
            )
            Logger.print_warn("Make sure to remove them from the printer.cfg!")

    def install_example_cfg(self, instances: List[Klipper]):
        cfg_dirs = [instance.cfg_dir for instance in instances]
        # copy extension to klippy/extras
        for cfg_dir in cfg_dirs:
            Logger.print_status(f"Create shell_command.cfg in '{cfg_dir}' ...")
            if check_file_exist(cfg_dir.joinpath("shell_command.cfg")):
                Logger.print_info("File already exists! Skipping ...")
                continue
            try:
                shutil.copy(EXAMPLE_CFG_SRC, cfg_dir)
                Logger.print_ok("Done!")
            except OSError as e:
                Logger.warn(f"Unable to create example config: {e}")

        # backup each printer.cfg before modification
        bm = BackupManager()
        for instance in instances:
            bm.backup_file(
                instance.cfg_file,
                custom_filename=f"{instance.suffix}.printer.cfg",
            )

        # add section to printer.cfg if not already defined
        section = "include shell_command.cfg"
        cfg_files = [instance.cfg_file for instance in instances]
        for cfg_file in cfg_files:
            Logger.print_status(f"Include shell_command.cfg in '{cfg_file}' ...")
            cm = ConfigManager(cfg_file)
            if cm.config.has_section(section):
                Logger.print_info("Section already defined! Skipping ...")
                continue
            cm.config.add_section(section)
            cm.write_config()
            Logger.print_ok("Done!")
