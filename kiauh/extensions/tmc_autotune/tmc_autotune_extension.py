# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from extensions.tmc_autotune import (
    KLIPPER_DIR,
    KLIPPER_EXTENSIONS_PATH,
    TMCA_DIR,
    TMCA_EXAMPLE_CONFIG,
    TMCA_MOONRAKER_UPDATER_NAME,
    TMCA_REPO,
)
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import check_file_exist, create_symlink, run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import check_python_version


# noinspection PyMethodMayBeStatic
class TmcAutotuneExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing Klipper TMC Autotune...")

        # Check for Python 3.x, aligned with upstream install script
        if not check_python_version(3, 0):
            Logger.print_warn("Python 3.x is required. Aborting install.")
            return

        klipper_dir_exists = check_file_exist(KLIPPER_DIR)
        if not klipper_dir_exists:
            Logger.print_warn(
                "No Klipper directory found! Unable to install extension."
            )
            return

        tmca_exists = (
            check_file_exist(TMCA_DIR)
            and check_file_exist(KLIPPER_EXTENSIONS_PATH.joinpath("autotune_tmc.py"))
            and check_file_exist(KLIPPER_EXTENSIONS_PATH.joinpath("motor_constants.py"))
            and check_file_exist(KLIPPER_EXTENSIONS_PATH.joinpath("motor_database.cfg"))
        )

        overwrite = True
        if tmca_exists:
            overwrite = get_confirm(
                question="Extension seems to be installed already. Overwrite?",
                default_choice=True,
                allow_go_back=False,
            )

        if not overwrite:
            Logger.print_warn("Installation aborted due to user request.")
            return

        add_moonraker_update_section = get_confirm(
            question="Add Klipper TMC Autotune to Moonraker update manager(s)?",
            default_choice=True,
            allow_go_back=False,
        )

        create_example_config = get_confirm(
            question="Create an example autotune_tmc.cfg for each instance?",
            default_choice=True,
            allow_go_back=False,
        )

        kl_instances = get_instances(Klipper)

        if not self._stop_klipper_instances_interactively(
            kl_instances, "installation of TMC Autotune"
        ):
            return

        try:
            git_clone_wrapper(TMCA_REPO, TMCA_DIR, force=True)

            Logger.print_info("Creating symlinks in Klipper extras directory...")
            create_symlink(
                TMCA_DIR.joinpath("autotune_tmc.py"),
                KLIPPER_EXTENSIONS_PATH.joinpath("autotune_tmc.py"),
            )
            create_symlink(
                TMCA_DIR.joinpath("motor_constants.py"),
                KLIPPER_EXTENSIONS_PATH.joinpath("motor_constants.py"),
            )
            create_symlink(
                TMCA_DIR.joinpath("motor_database.cfg"),
                KLIPPER_EXTENSIONS_PATH.joinpath("motor_database.cfg"),
            )
            Logger.print_ok(
                "Symlinks created successfully for all instances.", end="\n\n"
            )

            if create_example_config:
                self._install_example_cfg(kl_instances)
            else:
                Logger.print_info(
                    "Skipping example config creation as per user request."
                )
                Logger.print_warn(
                    "Make sure to create and include an autotune_tmc.cfg in your printer.cfg in order to use the extension!"
                )

            if add_moonraker_update_section:
                mr_instances = get_instances(Moonraker)
                self._add_moonraker_update_manager_section(mr_instances)
            else:
                Logger.print_info(
                    "Skipping update section creation as per user request."
                )
                Logger.print_warn(
                    "Make sure to create the corresponding section in your moonraker.conf in order to have it appear in your frontend update manager!"
                )

        except Exception as e:
            Logger.print_error(f"Error during Klipper TMC Autotune installation:\n{e}")

            if kl_instances:
                InstanceManager.start_all(kl_instances)
            return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        if create_example_config:
            Logger.print_dialog(
                DialogType.ATTENTION,
                [
                    "Basic configuration files were created per instance. You must edit them to enable the extension.",
                    "Documentation:",
                    f"{TMCA_REPO}",
                    "\n\n",
                    "IMPORTANT:",
                    "Define [autotune_tmc] sections ONLY in 'autotune_tmc.cfg'. ",
                    "Do NOT add them to 'printer.cfg', contrary to official docs. "
                    "While not fatal, mixing configs breaks file segmentation and is bad practice.",
                ],
                margin_bottom=1,
            )

        Logger.print_ok("Klipper TMC Autotune installed successfully!")

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(TMCA_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        backup_before_update = get_confirm(
            question="Backup Klipper TMC Autotune directory before update?",
            default_choice=True,
            allow_go_back=True,
        )

        kl_instances = get_instances(Klipper)

        if not self._stop_klipper_instances_interactively(
            kl_instances, "update of TMC Autotune"
        ):
            return

        Logger.print_status("Updating Klipper TMC Autotune...")
        try:
            if backup_before_update:
                Logger.print_status("Backing up Klipper TMC Autotune directory...")
                svc = BackupService()
                svc.backup_directory(
                    source_path=TMCA_DIR,
                    backup_name="klipper_tmc_autotune",
                )
                Logger.print_ok("Backup completed successfully.")

            git_pull_wrapper(TMCA_DIR)

        except Exception as e:
            Logger.print_error(f"Error during Klipper TMC Autotune update:\n{e}")

            if kl_instances:
                InstanceManager.start_all(kl_instances)
                return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        Logger.print_ok("Klipper TMC Autotune updated successfully.", end="\n\n")

    def remove_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(TMCA_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        kl_instances = get_instances(Klipper)

        if not self._stop_klipper_instances_interactively(
            kl_instances, "removal of TMC Autotune"
        ):
            return

        try:
            Logger.print_info("Removing Klipper TMC Autotune extension ...")
            run_remove_routines(TMCA_DIR)
            Logger.print_info("Removing symlinks from Klipper extras directory ...")
            run_remove_routines(KLIPPER_EXTENSIONS_PATH.joinpath("autotune_tmc.py"))
            run_remove_routines(KLIPPER_EXTENSIONS_PATH.joinpath("motor_constants.py"))
            run_remove_routines(KLIPPER_EXTENSIONS_PATH.joinpath("motor_database.cfg"))

            mr_instances: List[Moonraker] = get_instances(Moonraker)
            self._remove_moonraker_update_manager_section(mr_instances)

            Logger.print_info("Removing include from printer.cfg files ...")
            BackupService().backup_printer_cfg()
            remove_config_section("include autotune_tmc.cfg", kl_instances)

            Logger.print_dialog(
                DialogType.ATTENTION,
                [
                    "Manual edits to 'printer.cfg' may be required if using exotic stepper configurations.",
                    "\n\n",
                    "NOTE:",
                    "'autotune_tmc.cfg' is NOT removed automatically. ",
                    "Please delete it manually if no longer needed.",
                ],
                margin_bottom=1,
            )

        except Exception as e:
            Logger.print_error(f"Unable to remove extension:\n{e}")

            if kl_instances:
                InstanceManager.start_all(kl_instances)
            return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        Logger.print_ok("Klipper TMC Autotune removed successfully.")

    def _install_example_cfg(self, kl_instances: List[Klipper]):
        cfg_dirs = [instance.base.cfg_dir for instance in kl_instances]

        for cfg_dir in cfg_dirs:
            Logger.print_status(f"Create autotune_tmc.cfg in '{cfg_dir}' ...")
            if check_file_exist(cfg_dir.joinpath("autotune_tmc.cfg")):
                Logger.print_info("File already exists! Skipping ...")
                continue
            try:
                shutil.copy(TMCA_EXAMPLE_CONFIG, cfg_dir.joinpath("autotune_tmc.cfg"))
                Logger.print_ok("Done!")
            except OSError as e:
                Logger.print_error(f"Unable to create example config: {e}")

        BackupService().backup_printer_cfg()

        section = "include autotune_tmc.cfg"
        cfg_files = [instance.cfg_file for instance in kl_instances]
        for cfg_file in cfg_files:
            Logger.print_status(f"Include autotune_tmc.cfg in '{cfg_file}' ...")
            scp = SimpleConfigParser()
            scp.read_file(cfg_file)
            if scp.has_section(section):
                Logger.print_info("Section already defined! Skipping ...")
                continue
            scp.add_section(section)
            scp.write_file(cfg_file)
            Logger.print_ok("Done!")

    def _add_moonraker_update_manager_section(
        self, mr_instances: List[Moonraker]
    ) -> None:
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "Moonraker not found! Klipper TMC Autotune update manager support "
                    "for Moonraker will not be added to moonraker.conf.",
                ],
            )
            if not get_confirm(
                "Continue Klipper TMC Autotune installation?",
                default_choice=False,
                allow_go_back=True,
            ):
                Logger.print_info("Installation aborted due to user request.")
                return

        BackupService().backup_moonraker_conf()

        add_config_section(
            section=TMCA_MOONRAKER_UPDATER_NAME,
            instances=mr_instances,
            options=[
                ("type", "git_repo"),
                ("channel", "dev"),
                ("path", TMCA_DIR.as_posix()),
                ("origin", TMCA_REPO),
                ("managed_services", "klipper"),
                ("primary_branch", "main"),
            ],
        )

        InstanceManager.restart_all(mr_instances)

        Logger.print_ok(
            "Klipper TMC Autotune successfully added to Moonraker update manager(s)!"
        )

    def _remove_moonraker_update_manager_section(
        self, mr_instances: List[Moonraker]
    ) -> None:
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "Moonraker not found! Klipper TMC Autotune update manager support "
                    "for Moonraker will not be removed from moonraker.conf.",
                ],
            )
            return

        BackupService().backup_moonraker_conf()

        remove_config_section("update_manager klipper_tmc_autotune", mr_instances)
        InstanceManager.restart_all(mr_instances)

        Logger.print_ok(
            "Klipper TMC Autotune successfully removed from Moonraker update manager(s)!"
        )

    def _stop_klipper_instances_interactively(
        self, kl_instances: List[Klipper], operation_name: str = "operation"
    ) -> bool:
        """
        Interactively stops all active Klipper instances, warning the user that ongoing prints will be disrupted.

        :param kl_instances: List of Klipper instances to stop.
        :param operation_name: Optional name of the operation being performed (for user messaging). Do NOT capitalize.
        :return: True if instances were stopped or no instances found, False if operation was aborted.
        """

        if not kl_instances:
            Logger.print_warn("No instances found, skipping instance stopping.")
            return True

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Do NOT continue if there are ongoing prints running",
                f"All Klipper instances will be restarted during the {operation_name} and "
                "ongoing prints WILL FAIL.",
            ],
        )
        stop_klipper = get_confirm(
            question=f"Stop Klipper now and proceed with {operation_name}?",
            default_choice=False,
            allow_go_back=True,
        )

        if stop_klipper:
            InstanceManager.stop_all(kl_instances)
            return True
        else:
            Logger.print_warn(
                f"{operation_name.capitalize()} aborted due to user request."
            )
            return False
