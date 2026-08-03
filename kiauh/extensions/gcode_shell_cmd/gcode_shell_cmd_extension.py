# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
from datetime import datetime
from typing import List

from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from core.i18n import _tr
from core.logger import Logger
from core.services.backup_service import BackupService
from core.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from extensions.gcode_shell_cmd import (
    EXAMPLE_CFG_SRC,
    EXTENSION_SRC,
    EXTENSION_TARGET_PATH,
    KLIPPER_DIR,
    KLIPPER_EXTRAS,
)
from utils.fs_utils import check_file_exist
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances


# noinspection PyMethodMayBeStatic
class GcodeShellCmdExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        install_example = get_confirm(_tr("Create an example shell command?"), False, False)

        klipper_dir_exists = check_file_exist(KLIPPER_DIR)
        if not klipper_dir_exists:
            Logger.print_warn(
                _tr("No Klipper directory found! Unable to install extension.")
            )
            return

        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        overwrite = True
        if extension_installed:
            overwrite = get_confirm(
                _tr("Extension seems to be installed already. Overwrite?"),
                True,
                False,
            )

        if not overwrite:
            Logger.print_warn(_tr("Installation aborted due to user request."))
            return

        instances = get_instances(Klipper)
        InstanceManager.stop_all(instances)

        try:
            Logger.print_status(_tr("Copy extension to '{}' ...").format(KLIPPER_EXTRAS))
            shutil.copy(EXTENSION_SRC, EXTENSION_TARGET_PATH)
        except OSError as e:
            Logger.print_error(_tr("Unable to install extension: {}").format(e))
            return

        if install_example:
            self.install_example_cfg(instances)

        InstanceManager.start_all(instances)

        Logger.print_ok(_tr("Installing G-Code Shell Command extension successful!"))

    def remove_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(EXTENSION_TARGET_PATH)
        if not extension_installed:
            Logger.print_info(_tr("Extension does not seem to be installed! Skipping ..."))
            return

        question = _tr("Do you really want to remove the extension?")
        if get_confirm(question, True, False):
            try:
                Logger.print_status(_tr("Removing '{}' ...").format(EXTENSION_TARGET_PATH))
                os.remove(EXTENSION_TARGET_PATH)
                Logger.print_ok(_tr("Extension successfully removed!"))
            except OSError as e:
                Logger.print_error(_tr("Unable to remove extension: {}").format(e))

            Logger.print_warn(_tr("PLEASE NOTE:"))
            Logger.print_warn(
                _tr("Remaining gcode shell command will cause Klipper to throw an error.")
            )
            Logger.print_warn(_tr("Make sure to remove them from the printer.cfg!"))

    def install_example_cfg(self, instances: List[Klipper]):
        cfg_dirs = [instance.base.cfg_dir for instance in instances]
        for cfg_dir in cfg_dirs:
            Logger.print_status(_tr("Create shell_command.cfg in '{}' ...").format(cfg_dir))
            if check_file_exist(cfg_dir.joinpath("shell_command.cfg")):
                Logger.print_info(_tr("File already exists! Skipping ..."))
                continue
            try:
                shutil.copy(EXAMPLE_CFG_SRC, cfg_dir)
                Logger.print_ok(_tr("Done!"))
            except OSError as e:
                Logger.print_error(_tr("Unable to create example config: {}").format(e))

        svc = BackupService()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        for instance in instances:
            svc.backup_file(
                source_path=instance.cfg_file,
                target_path=f"{instance.data_dir.name}/config_{timestamp}",
                target_name=instance.cfg_file.name,
            )

        section = "include shell_command.cfg"
        cfg_files = [instance.cfg_file for instance in instances]
        for cfg_file in cfg_files:
            Logger.print_status(_tr("Include shell_command.cfg in '{}' ...").format(cfg_file))
            scp = SimpleConfigParser()
            scp.read_file(cfg_file)
            if scp.has_section(section):
                Logger.print_info(_tr("Section already defined! Skipping ..."))
                continue
            scp.add_section(section)
            scp.write_file(cfg_file)
            Logger.print_ok(_tr("Done!"))
