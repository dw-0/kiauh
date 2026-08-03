# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  It integrates Klipper Adaptive Meshing & Purging (KAMP):               #
#  https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging           #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.i18n import _tr
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from extensions.klipper_adaptive_meshing_purging import (
    KAMP_DIR,
    KAMP_MOONRAKER_UPDATER_NAME,
    KAMP_REPO,
    KLIPPER_DIR,
)
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import check_file_exist, create_symlink, run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances, stop_klipper_instances_interactively


# noinspection PyMethodMayBeStatic
class KlipperAdaptiveMeshingPurgingExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Installing Klipper Adaptive Meshing Purging..."))

        klipper_dir_exists = check_file_exist(KLIPPER_DIR)
        if not klipper_dir_exists:
            Logger.print_warn(
                _tr("No Klipper directory found! Unable to install extension.")
            )
            return

        kl_instances: List[Klipper] = get_instances(Klipper)

        kamp_exists = check_file_exist(KAMP_DIR) and self._check_cfg_exists(
            kl_instances
        )

        overwrite = True
        if kamp_exists:
            overwrite = get_confirm(
                question=_tr("Extension seems to be installed already. Overwrite?"),
                default_choice=True,
                allow_go_back=False,
            )

        if not overwrite:
            Logger.print_warn(_tr("Installation aborted due to user request."))
            return

        add_moonraker_update_section = get_confirm(
            question=_tr("Add Klipper Adaptive Meshing and Purging to Moonraker update manager(s)?"),
            default_choice=True,
            allow_go_back=False,
        )

        if not stop_klipper_instances_interactively(
            kl_instances, _tr("installation of KAMP")
        ):
            return

        try:
            git_clone_wrapper(KAMP_REPO, KAMP_DIR, force=True)

            self._install_cfg(kl_instances)

            if add_moonraker_update_section:
                mr_instances: List[Moonraker] = get_instances(Moonraker)
                self._add_moonraker_update_manager_section(mr_instances)
            else:
                Logger.print_info(
                    _tr("Skipping update section creation as per user request.")
                )
                Logger.print_warn(
                    _tr("Make sure to create the corresponding section in your moonraker.conf in order to have it appear in your frontend update manager!")
                )

        except Exception as e:
            Logger.print_error(
                _tr("Error during Klipper Adaptive Meshing and Purging installation:\n{}").format(e)
            )

            if kl_instances:
                InstanceManager.start_all(kl_instances)
            return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                _tr("Basic configuration files were created per instance. You must edit them to enable the extension."),
                _tr("Documentation:"),
                f"{KAMP_REPO}",
                "\n\n",
                _tr("IMPORTANT:"),
                _tr("1. If you'd like to use adaptive meshing, Klipper already has built-in support. Just call BED_MESH_CALIBRATE ADAPTIVE=1 in your PRINT_START macro. DO NOT USE THE FEATURE FROM THE EXTENSION"),
                _tr("2. You MUST be thoughtful when editing values for the purge settings, as there is a risk to break parts of your printer."),
                _tr("3. According to KAMP's documentation, you should define 'max_extrude_cross_section' in 'printer.cfg' according to your needs."),
            ],
            margin_bottom=1,
        )

        Logger.print_ok(_tr("Klipper Adaptive Meshing and Purging installed successfully!"))

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(KAMP_DIR)
        if not extension_installed:
            Logger.print_info(_tr("Extension does not seem to be installed! Skipping ..."))
            return

        backup_before_update = get_confirm(
            question=_tr("Backup Klipper Adaptive Meshing and Purging directory before update?"),
            default_choice=True,
            allow_go_back=True,
        )

        kl_instances: List[Klipper] = get_instances(Klipper)

        if not stop_klipper_instances_interactively(kl_instances, _tr("update of KAMP")):
            return

        Logger.print_status(_tr("Updating Klipper Adaptive Meshing and Purging..."))
        try:
            if backup_before_update:
                Logger.print_status(
                    _tr("Backing up Klipper Adaptive Meshing and Purging directory ...")
                )
                svc = BackupService()
                svc.backup_directory(
                    source_path=KAMP_DIR,
                    backup_name="Klipper-Adaptive-Meshing-Purging",
                )
                Logger.print_ok(_tr("Backup completed successfully."))

            git_pull_wrapper(KAMP_DIR)

        except Exception as e:
            Logger.print_error(
                _tr("Error during Klipper Adaptive Meshing and Purging update:\n{}").format(e)
            )

            if kl_instances:
                InstanceManager.start_all(kl_instances)
                return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        Logger.print_ok(
            _tr("Klipper Adaptive Meshing and Purging updated successfully."), end="\n\n"
        )

    def remove_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(KAMP_DIR)
        if not extension_installed:
            Logger.print_info(_tr("Extension does not seem to be installed! Skipping ..."))
            return

        kl_instances: List[Klipper] = get_instances(Klipper)

        if not stop_klipper_instances_interactively(kl_instances, _tr("removal of KAMP")):
            return

        try:
            run_remove_routines(KAMP_DIR)
            self._remove_cfg(kl_instances)

            mr_instances: List[Moonraker] = get_instances(Moonraker)
            self._remove_moonraker_update_manager_section(mr_instances)

            BackupService().backup_printer_cfg()
            remove_config_section("include KAMP_Settings.cfg", kl_instances)

            Logger.print_dialog(
                DialogType.ATTENTION,
                [
                    _tr("You might want to remove [exclude_object] sections from 'printer.cfg', unless you use them for some other reason."),
                    "\n\n",
                    _tr("You might also want to remove the [file_manager] sections from 'moonraker.conf', unless used otherwise."),
                    "\n\n",
                    _tr("NOTE:"),
                    _tr("'KAMP_Settings.cfg' is NOT removed automatically. "),
                    _tr("Please delete it manually if no longer needed."),
                ],
                margin_bottom=1,
            )

        except Exception as e:
            Logger.print_error(_tr("Unable to remove extension:\n{}").format(e))

            if kl_instances:
                InstanceManager.start_all(kl_instances)
            return

        if kl_instances:
            InstanceManager.start_all(kl_instances)

        Logger.print_ok(_tr("Klipper Adaptive Meshing and Purging removed successfully."))

    def _install_cfg(self, kl_instances: List[Klipper]):
        is_multi_instance = len(kl_instances) > 1
        for instance in kl_instances:
            cfg_dir = instance.base.cfg_dir
            Logger.print_status(
                _tr("Creating symlink for KAMP directory in '{}' ...").format(cfg_dir)
            )
            create_symlink(KAMP_DIR.joinpath("Configuration"), cfg_dir.joinpath("KAMP"))
            if is_multi_instance:
                Logger.print_ok(_tr("Symlink successfully created for instance '{}'.").format(instance.suffix))
            else:
                Logger.print_ok(_tr("Symlink successfully created."))

            Logger.print_status(_tr("Creating KAMP_Settings.cfg in '{}' ...").format(cfg_dir))
            if check_file_exist(cfg_dir.joinpath("KAMP_Settings.cfg")):
                Logger.print_info(_tr("File already exists! Skipping ..."))
                continue
            try:
                shutil.copy(
                    KAMP_DIR.joinpath("Configuration/KAMP_Settings.cfg"),
                    cfg_dir.joinpath("KAMP_Settings.cfg"),
                )
                if is_multi_instance:
                    Logger.print_ok(_tr("Config file successfully created for instance '{}'.").format(instance.suffix))
                else:
                    Logger.print_ok(_tr("Config file successfully created."))
            except OSError as e:
                Logger.print_error(_tr("Unable to create example config: {}").format(e))

        BackupService().backup_printer_cfg()

        sections = ["include KAMP_Settings.cfg", "exclude_object"]
        for instance in kl_instances:
            cfg_file = instance.cfg_file
            scp = SimpleConfigParser()
            scp.read_file(cfg_file)

            for section in sections:
                if scp.has_section(section):
                    continue
                Logger.print_status(_tr("Add '{}' to '{}' ...").format(section, cfg_file))
                scp.add_section(section)
                scp.write_file(cfg_file)
                Logger.print_ok(_tr("Done!"))

    def _add_moonraker_update_manager_section(
        self, mr_instances: List[Moonraker]
    ) -> None:
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    _tr("Moonraker not found! Klipper Adaptive Meshing and Purging update manager support for Moonraker will not be added to moonraker.conf."),
                ],
            )
            if not get_confirm(
                _tr("Continue Klipper Adaptive Meshing and Purging installation?"),
                default_choice=False,
                allow_go_back=True,
            ):
                Logger.print_info(_tr("Installation aborted due to user request."))
                return

        BackupService().backup_moonraker_conf()

        add_config_section(
            section=KAMP_MOONRAKER_UPDATER_NAME,
            instances=mr_instances,
            options=[
                ("type", "git_repo"),
                ("channel", "dev"),
                ("path", KAMP_DIR.as_posix()),
                ("origin", KAMP_REPO),
                ("managed_services", "klipper"),
                ("primary_branch", "main"),
            ],
        )

        add_config_section(
            section="file_manager",
            instances=mr_instances,
            options=[
                ("enable_object_processing", "True"),
            ],
        )

        InstanceManager.restart_all(mr_instances)

        Logger.print_ok(
            _tr("Klipper Adaptive Meshing and Purging successfully added to Moonraker update manager(s)!")
        )

    def _remove_moonraker_update_manager_section(
        self, mr_instances: List[Moonraker]
    ) -> None:
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    _tr("Moonraker not found! Klipper Adaptive Meshing and Purging update manager support for Moonraker will not be removed from moonraker.conf."),
                ],
            )
            return

        BackupService().backup_moonraker_conf()

        remove_config_section(KAMP_MOONRAKER_UPDATER_NAME, mr_instances)
        InstanceManager.restart_all(mr_instances)

        Logger.print_ok(
            _tr("Klipper Adaptive Meshing and Purging successfully removed from Moonraker update manager(s)!")
        )

    def _check_cfg_exists(self, kl_instances: List[Klipper]) -> bool:
        cfg_dirs = [instance.base.cfg_dir for instance in kl_instances]

        for cfg_dir in cfg_dirs:
            if (
                check_file_exist(cfg_dir.joinpath("KAMP_Settings.cfg"))
                and check_file_exist(cfg_dir.joinpath("KAMP/KAMP_Settings.cfg"))
                and check_file_exist(cfg_dir.joinpath("KAMP/Adaptive_Meshing.cfg"))
                and check_file_exist(cfg_dir.joinpath("KAMP/Line_Purge.cfg"))
                and check_file_exist(cfg_dir.joinpath("KAMP/Smart_Park.cfg"))
                and check_file_exist(cfg_dir.joinpath("KAMP/Voron_Purge.cfg"))
            ):
                return True

        return False

    def _remove_cfg(self, kl_instances: List[Klipper]) -> None:
        cfg_dirs = [instance.base.cfg_dir for instance in kl_instances]

        for cfg_dir in cfg_dirs:
            Logger.print_status(_tr("Removing KAMP symlink in '{}' ...").format(cfg_dir))
            run_remove_routines(cfg_dir.joinpath("KAMP"))
