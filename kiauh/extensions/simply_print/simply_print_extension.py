# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from typing import List

from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from utils.common import backup_printer_config_dir, moonraker_exists
from utils.input_utils import get_confirm


# noinspection PyMethodMayBeStatic
class SimplyPrintExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing SimplyPrint ...")

        if not (mr_instances := moonraker_exists("SimplyPrint Installer")):
            return

        Logger.print_dialog(
            DialogType.INFO,
            self._construct_dialog(mr_instances, True),
        )

        if not get_confirm(
            "Continue SimplyPrint installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting SimplyPrint installation ...")
            return

        try:
            self._patch_moonraker_confs(mr_instances, True)

        except Exception as e:
            Logger.print_error(f"Error during SimplyPrint installation:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing SimplyPrint ...")

        if not (mr_instances := moonraker_exists("SimplyPrint Uninstaller")):
            return

        Logger.print_dialog(
            DialogType.INFO,
            self._construct_dialog(mr_instances, False),
        )

        if not get_confirm(
            "Do you really want to uninstall SimplyPrint?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting SimplyPrint uninstallation ...")
            return

        try:
            self._patch_moonraker_confs(mr_instances, False)

        except Exception as e:
            Logger.print_error(f"Error during SimplyPrint installation:\n{e}")

    def _construct_dialog(
        self, mr_instances: List[Moonraker], is_install: bool
    ) -> List[str]:
        mr_names = [f"● {m.service_file_path.name}" for m in mr_instances]
        _type = "install" if is_install else "uninstall"

        return [
            "The following Moonraker instances were found:",
            *mr_names,
            "\n\n",
            f"The setup will {_type} SimplyPrint for all Moonraker instances. "
            f"After {_type}ation, all Moonraker services will be restarted!",
        ]

    def _patch_moonraker_confs(
        self, mr_instances: List[Moonraker], is_install: bool
    ) -> None:
        section = "simplyprint"
        _type, _ft = ("Adding", "to") if is_install else ("Removing", "from")

        patched_files = []
        for moonraker in mr_instances:
            Logger.print_status(
                f"{_type} section 'simplyprint' {_ft} {moonraker.cfg_file} ..."
            )
            scp = SimpleConfigParser()
            scp.read_file(moonraker.cfg_file)

            install_and_has_section = is_install and scp.has_section(section)
            uninstall_and_has_no_section = not is_install and not scp.has_section(
                section
            )

            if install_and_has_section or uninstall_and_has_no_section:
                status = "already" if is_install else "does not"
                Logger.print_info(
                    f"Section 'simplyprint' {status} exists! Skipping ..."
                )
                continue

            if is_install and not scp.has_section("simplyprint"):
                backup_printer_config_dir()
                scp.add_section(section)
            elif not is_install and scp.has_section("simplyprint"):
                backup_printer_config_dir()
                scp.remove_section(section)
            scp.write_file(moonraker.cfg_file)
            patched_files.append(moonraker.cfg_file)

        if patched_files:
            InstanceManager.restart_all(mr_instances)

        install_state = "successfully" if patched_files else "was already"
        Logger.print_dialog(
            DialogType.SUCCESS,
            [f"SimplyPrint {install_state} {'' if is_install else 'un'}installed!"],
            center_content=True,
        )
