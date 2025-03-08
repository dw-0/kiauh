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

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.octoapp import (
    OA_DEPS_JSON_FILE,
    OA_DIR,
    OA_ENV_DIR,
    OA_INSTALL_SCRIPT,
    OA_INSTALLER_LOG_FILE,
    OA_REPO,
    OA_REQ_FILE,
    OA_SYS_CFG_NAME,
)
from extensions.octoapp.octoapp import Octoapp
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
class OctoappExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing OctoApp for Klipper ...")

        # check if moonraker is installed. if not, notify the user and exit
        if not moonraker_exists():
            return

        force_clone = False
        OA_instances: List[Octoapp] = get_instances(Octoapp)
        if OA_instances:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "OctoApp is already installed!",
                    "It is safe to run the installer again to link your "
                    "printer or repair any issues.",
                ],
            )
            if not get_confirm("Re-run OctoApp installation?"):
                Logger.print_info("Exiting OctoApp for Klipper installation ...")
                return
            else:
                Logger.print_status("Re-Installing OctoApp for Klipper ...")
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
                    "The setup will apply the same names to OctoApp!",
                ],
            )

        if not get_confirm(
            "Continue OctoApp for Klipper installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting OctoApp for Klipper installation ...")
            return

        try:
            git_clone_wrapper(OA_REPO, OA_DIR, force=force_clone)

            for moonraker in mr_instances:
                instance = Octoapp(suffix=moonraker.suffix)
                instance.create()

            InstanceManager.restart_all(mr_instances)

            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoApp for Klipper successfully installed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoApp for Klipper installation:\n{e}")

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating OctoApp for Klipper ...")
        try:
            Octoapp.update()
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoApp for Klipper successfully updated!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoApp for Klipper update:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing OctoApp for Klipper ...")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        ob_instances: List[Octoapp] = get_instances(Octoapp)

        try:
            self._remove_OA_instances(ob_instances)
            self._remove_OA_store_dirs()
            self._remove_OA_dir()
            self._remove_OA_env()
            remove_config_section(f"include {OA_SYS_CFG_NAME}", mr_instances)
            run_remove_routines(OA_INSTALLER_LOG_FILE)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["OctoApp for Klipper successfully removed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoApp for Klipper removal:\n{e}")

    def _install_OA_dependencies(self) -> None:
        OA_deps = []
        if OA_DEPS_JSON_FILE.exists():
            with open(OA_DEPS_JSON_FILE, "r") as deps:
                OA_deps = json.load(deps).get("debian", [])
        elif OA_INSTALL_SCRIPT.exists():
            OA_deps = parse_packages_from_file(OA_INSTALL_SCRIPT)

        if not OA_deps:
            raise ValueError("Error reading OctoApp dependencies!")

        check_install_dependencies({*OA_deps})
        install_python_requirements(OA_ENV_DIR, OA_REQ_FILE)

    def _remove_OA_instances(
        self,
        instance_list: List[Octoapp],
    ) -> None:
        if not instance_list:
            Logger.print_info("No OctoApp instances found. Skipped ...")
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)

    def _remove_OA_dir(self) -> None:
        Logger.print_status("Removing OctoApp for Klipper directory ...")

        if not OA_DIR.exists():
            Logger.print_info(f"'{OA_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OA_DIR)

    def _remove_OA_store_dirs(self) -> None:
        Logger.print_status("Removing OctoApp for Klipper store directory ...")

        klipper_instances: List[Moonraker] = get_instances(Klipper)

        for instance in klipper_instances:
            store_dir = instance.data_dir.joinpath("octoapp-store")
            if not store_dir.exists():
                Logger.print_info(f"'{store_dir}' does not exist. Skipped ...")
                return

            run_remove_routines(store_dir)

    def _remove_OA_env(self) -> None:
        Logger.print_status("Removing OctoApp for Klipper environment ...")

        if not OA_ENV_DIR.exists():
            Logger.print_info(f"'{OA_ENV_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OA_ENV_DIR)
