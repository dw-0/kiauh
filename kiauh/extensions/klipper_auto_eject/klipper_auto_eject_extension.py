# ======================================================================= #
#  Copyright (C) 2026 Ahmed Bebars                                        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from subprocess import CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.settings.kiauh_settings import KiauhSettings
from extensions.base_extension import BaseExtension
from extensions.klipper_auto_eject import (
    AE_DIR,
    AE_INSTALL_SCRIPT,
    AE_REPO,
    AE_SERVICE_FILE,
    AE_SERVICE_NAME,
)
from utils.fs_utils import run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import cmd_sysctl_service


# noinspection PyMethodMayBeStatic
class KlipperAutoEjectExtension(BaseExtension):
    """
    Klipper Auto-Eject comes with its own installer (install.sh), which asks
    what to set up: the macros, the web page, remote access, notifications,
    the printer farm and Spoolman. This extension clones the repository and
    runs that installer for each Klipper instance, so both ways of
    installing stay the same. The installer never restarts Klipper while it
    prints.
    """

    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing Klipper Auto-Eject ...")

        kl_instances: List[Klipper] = get_instances(Klipper)
        if not kl_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "Klipper not found! Klipper Auto-Eject is a set of Klipper "
                    "macros: install Klipper and Moonraker first.",
                ],
            )
            return

        if AE_DIR.exists() and not get_confirm(
            "Klipper Auto-Eject seems to be installed already. "
            "Run its installer again?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Installation aborted due to user request.")
            return

        try:
            if not AE_DIR.exists():
                git_clone_wrapper(AE_REPO, AE_DIR)
            for instance in kl_instances:
                if len(kl_instances) > 1:
                    Logger.print_status(f"Printer '{instance.data_dir.name}' ...")
                self._run_installer("--config-dir", instance.base.cfg_dir.as_posix())
        except CalledProcessError as e:
            Logger.print_error(f"Error installing Klipper Auto-Eject:\n{e}")
            return

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Mount the blade, then type AUTO_EJECT_SETUP in the console of "
                "Mainsail or Fluidd: it guides you through every setting.",
                "\n\n",
                "In your slicer, add this line at the end of the end G-code:",
                "AUTO_EJECT HEIGHT=[max_layer_z] HOME=1",
                "\n\n",
                "Documentation:",
                "https://github.com/ahmedbebars/klipper-auto-eject",
            ],
            margin_bottom=1,
        )
        Logger.print_ok("Klipper Auto-Eject installed successfully!")

    def update_extension(self, **kwargs) -> None:
        if not AE_DIR.exists():
            Logger.print_info(
                "Klipper Auto-Eject does not seem to be installed! Skipping ..."
            )
            return

        Logger.print_status("Updating Klipper Auto-Eject ...")
        try:
            settings = KiauhSettings()
            if settings.kiauh.backup_before_update:
                BackupService().backup_directory(
                    source_path=AE_DIR,
                    backup_name="klipper-auto-eject",
                )
            git_pull_wrapper(AE_DIR)
            # the notification and farm service runs from the repository
            if AE_SERVICE_FILE.exists():
                cmd_sysctl_service(AE_SERVICE_NAME, "restart")
        except CalledProcessError as e:
            Logger.print_error(f"Error updating Klipper Auto-Eject:\n{e}")
            return

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Restart Klipper to load the new macros: type FIRMWARE_RESTART "
                "in the console when the printer is not printing.",
            ],
            margin_bottom=1,
        )
        Logger.print_ok("Klipper Auto-Eject updated successfully.", end="\n\n")

    def remove_extension(self, **kwargs) -> None:
        if not AE_DIR.exists():
            Logger.print_info(
                "Klipper Auto-Eject does not seem to be installed! Skipping ..."
            )
            return

        Logger.print_status("Removing Klipper Auto-Eject ...")
        try:
            # takes out what the installer put in: the [include] lines, the
            # update manager section, the web page and the service
            for instance in get_instances(Klipper):
                self._run_installer(
                    "--uninstall", "--config-dir", instance.base.cfg_dir.as_posix()
                )
            Logger.print_status("Removing Klipper Auto-Eject directory ...")
            run_remove_routines(AE_DIR)
        except CalledProcessError as e:
            Logger.print_error(f"Unable to remove Klipper Auto-Eject:\n{e}")
            return

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Your settings in auto_eject_settings.cfg were kept, and so were "
                "the values saved from the web page, in the file of "
                "[save_variables] (lines starting with auto_eject_). Delete them "
                "if you like.",
                "\n\n",
                "Take AUTO_EJECT and AUTO_EJECT_GUARD out of your slicer's G-code, "
                "then restart Klipper (FIRMWARE_RESTART) when it is not printing.",
            ],
            margin_bottom=1,
        )
        Logger.print_ok("Klipper Auto-Eject removed successfully.")

    def _run_installer(self, *args: str) -> None:
        # interactive: it runs in the same terminal and asks its own questions
        run(["bash", AE_INSTALL_SCRIPT.as_posix(), *args], check=True)
