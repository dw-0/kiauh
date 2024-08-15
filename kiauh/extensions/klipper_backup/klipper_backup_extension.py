# ======================================================================= #
#  Copyright (C) 2023 - 2024 Staubgeborener and Tylerjet                  #
#  https://github.com/Staubgeborener/klipper-backup                       #
#  https://klipperbackup.xyz                                              #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess

from core.constants import SYSTEMD
from core.logger import Logger
from extensions.base_extension import BaseExtension
from extensions.klipper_backup import (
    KLIPPERBACKUP_CONFIG_DIR,
    KLIPPERBACKUP_DIR,
    KLIPPERBACKUP_REPO_URL,
    MOONRAKER_CONF,
)
from utils.fs_utils import check_file_exist
from utils.input_utils import get_confirm
from utils.sys_utils import unit_file_exists


# noinspection PyMethodMayBeStatic
class KlipperbackupExtension(BaseExtension):

    def remove_extension(self, **kwargs) -> None:
        def uninstall_service(service_name: str, unit_type: str) -> bool:
            try:
                full_service_name = f"{service_name}.{unit_type}"
                subprocess.run(["sudo", "systemctl", "stop", full_service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["sudo", "systemctl", "disable", full_service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                service_path = f"{SYSTEMD}/{full_service_name}"
                subprocess.run(["sudo", "rm", service_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "reset-failed"], check=True)
                return True
            except subprocess.CalledProcessError:
                return False

        def check_crontab_entry(entry) -> bool:
            try:
                crontab_content = subprocess.check_output(
                    ["crontab", "-l"], stderr=subprocess.DEVNULL, text=True
                )
            except subprocess.CalledProcessError:
                return False
            for line in crontab_content.splitlines():
                if entry in line:
                    return True
            return False

        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        def remove_moonraker_entry():
            original_file_path = MOONRAKER_CONF
            comparison_file_path = os.path.join(
                str(KLIPPERBACKUP_DIR), "install-files", "moonraker.conf"
            )
            if not os.path.exists(original_file_path) or not os.path.exists(
                comparison_file_path
            ):
                return False
            with open(original_file_path, "r") as original_file, open(
                comparison_file_path, "r"
            ) as comparison_file:
                original_content = original_file.read()
                comparison_content = comparison_file.read()
            if comparison_content in original_content:
                modified_content = original_content.replace(
                    comparison_content, ""
                ).strip()
                modified_content = "\n".join(
                    line for line in modified_content.split("\n") if line.strip()
                )
                with open(original_file_path, "w") as original_file:
                    original_file.write(modified_content)
                    return True
            else:
                return False

        question = "Do you really want to remove the extension?"
        if get_confirm(question, True, False):
            # Remove Klipper-Backup services
            service_names = [
                "klipper-backup-on-boot",
                "klipper-backup-filewatch",
                "klipper-backup",
            ]

            unit_types = ["timer", "service"]

            for service_name in service_names:
                try:
                    Logger.print_status(f"Check whether a {service_name} unit is installed ...")

                    for unit_type in unit_types:
                        full_service_name = f"{service_name}.{unit_type}"
                        Logger.print_info(f"Checking for {unit_type} unit {full_service_name}")

                        if unit_file_exists(service_name, unit_type):
                            Logger.print_info(f"{unit_type.capitalize()} unit {full_service_name} detected.")

                            if uninstall_service(service_name, unit_type):
                                Logger.print_ok(f"The {unit_type} unit {full_service_name} has been successfully uninstalled.")
                            else:
                                Logger.print_error(f"Error uninstalling {full_service_name}.")
                        else:
                            Logger.print_info(f"No {unit_type} unit for {full_service_name} detected.")
                except Exception as e:
                    Logger.print_error(f"Unable to remove the {service_name} service: {e}")

            # Remove Klipper-Backup cron
            Logger.print_status("Check for Klipper-Backup cron entry ...")
            entry_to_check = "/klipper-backup/script.sh"
            try:
                if check_crontab_entry(entry_to_check):
                    crontab_content = subprocess.check_output(
                        ["crontab", "-l"], text=True
                    )
                    modified_content = "\n".join(
                        line
                        for line in crontab_content.splitlines()
                        if entry_to_check not in line
                    )
                    if not modified_content.endswith("\n"):
                        modified_content += "\n"

                    subprocess.run(
                        ["crontab", "-"], input=modified_content, text=True, check=True
                    )
                    Logger.print_ok("The Klipper-Backup entry has been removed from the crontab.")
                else:
                    Logger.print_info("The Klipper-Backup entry is not present in the crontab. Skipping ...")
            except subprocess.CalledProcessError:
                Logger.print_error("Unable to remove the Klipper-Backup cron entry")


            # Remove Klipper-Backup
            Logger.print_status(f"Removing '{KLIPPERBACKUP_DIR}' ...")
            try:
                shutil.rmtree(KLIPPERBACKUP_DIR)
                config_backup_exists = check_file_exist(KLIPPERBACKUP_CONFIG_DIR)
                if config_backup_exists:
                    shutil.rmtree(KLIPPERBACKUP_CONFIG_DIR)
                Logger.print_ok("Extension Klipper-Backup successfully removed!")
            except OSError as e:
                Logger.print_error(f"Unable to remove extension: {e}")

    def install_extension(self, **kwargs) -> None:
        if not KLIPPERBACKUP_DIR.exists():
            subprocess.run(
                ["git", "clone", str(KLIPPERBACKUP_REPO_URL), str(KLIPPERBACKUP_DIR)]
            )
            subprocess.run(["chmod", "+x", str(KLIPPERBACKUP_DIR / "install.sh")])
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh")])

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            remove_extension()
        else:
            subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "check_updates"])
