# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import json
from typing import List

from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.octoeverywhere import (
    OE_DEPS_JSON_FILE,
    OE_DIR,
    OE_ENV_DIR,
    OE_INSTALL_SCRIPT,
    OE_INSTALLER_LOG_FILE,
    OE_REPO,
    OE_REQ_FILE,
    OE_SYS_CFG_NAME,
)
from extensions.octoeverywhere.octoeverywhere import Octoeverywhere
from utils.common import (
    check_install_dependencies,
    moonraker_exists,
)
from utils.config_utils import (
    remove_config_section,
)
from utils.fs_utils import run_remove_routines
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    install_python_requirements,
    parse_packages_from_file,
)


# noinspection PyMethodMayBeStatic
class OctoeverywhereExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing OctoEverywhere for Klipper ...")

        # check if moonraker is installed. if not, notify the user and exit
        if not moonraker_exists():
            return

        force_clone = False
        oe_instances: List[Octoeverywhere] = get_instances(Octoeverywhere)
        if oe_instances:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "OctoEverywhere is already installed!",
                    "It is safe to run the installer again to link your "
                    "printer or repair any issues.",
                ],
            )
            if not get_confirm("Re-run OctoEverywhere installation?"):
                Logger.print_info("Exiting OctoEverywhere for Klipper installation ...")
                return
            else:
                Logger.print_status("Re-Installing OctoEverywhere for Klipper ...")
                force_clone = True

        mr_instances: List[Moonraker] = get_instances(Moonraker)

        mr_names = [f"● {moonraker.data_dir.name}" for moonraker in mr_instances]
        if len(mr_names) > 1:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "The following Moonraker instances were found:",
                    *mr_names,
                    "\n\n",
                    "The setup will apply the same names to OctoEverywhere!",
                ],
            )

        if not get_confirm(
            "Continue OctoEverywhere for Klipper installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting OctoEverywhere for Klipper installation ...")
            return

        try:
            git_clone_wrapper(OE_REPO, OE_DIR, force=force_clone)

            for moonraker in mr_instances:
                instance = Octoeverywhere(suffix=moonraker.suffix)
                instance.create()

            InstanceManager.restart_all(mr_instances)

            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoEverywhere for Klipper successfully installed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(
                f"Error during OctoEverywhere for Klipper installation:\n{e}"
            )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating OctoEverywhere for Klipper ...")
        try:
            Octoeverywhere.update()
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoEverywhere for Klipper successfully updated!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoEverywhere for Klipper update:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing OctoEverywhere for Klipper ...")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        ob_instances: List[Octoeverywhere] = get_instances(Octoeverywhere)

        try:
            self._remove_oe_instances(ob_instances)
            self._remove_oe_dir()
            self._remove_oe_env()
            remove_config_section(f"include {OE_SYS_CFG_NAME}", mr_instances)
            run_remove_routines(OE_INSTALLER_LOG_FILE)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoEverywhere for Klipper successfully removed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoEverywhere for Klipper removal:\n{e}")

    def _install_oe_dependencies(self) -> None:
        oe_deps = []
        if OE_DEPS_JSON_FILE.exists():
            with open(OE_DEPS_JSON_FILE, "r") as deps:
                oe_deps = json.load(deps).get("debian", [])
        elif OE_INSTALL_SCRIPT.exists():
            oe_deps = parse_packages_from_file(OE_INSTALL_SCRIPT)

        if not oe_deps:
            raise ValueError("Error reading OctoEverywhere dependencies!")

        check_install_dependencies({*oe_deps})
        install_python_requirements(OE_ENV_DIR, OE_REQ_FILE)

    def _remove_oe_instances(
        self,
        instance_list: List[Octoeverywhere],
    ) -> None:
        if not instance_list:
            Logger.print_info("No OctoEverywhere instances found. Skipped ...")
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)

    def _remove_oe_dir(self) -> None:
        Logger.print_status("Removing OctoEverywhere for Klipper directory ...")

        if not OE_DIR.exists():
            Logger.print_info(f"'{OE_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OE_DIR)

    def _remove_oe_env(self) -> None:
        Logger.print_status("Removing OctoEverywhere for Klipper environment ...")

        if not OE_ENV_DIR.exists():
            Logger.print_info(f"'{OE_ENV_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OE_ENV_DIR)
