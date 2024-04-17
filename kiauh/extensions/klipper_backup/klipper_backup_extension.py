# ======================================================================= #
#  Copyright (C) 2023 - 2024 Staubgeborener and Tylerjet                  #
#  https://github.com/Staubgeborener/klipper-backup                       #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess

from components.moonraker import MOONRAKER_DIR
from extensions.base_extension import BaseExtension
from extensions.klipper_backup import (
    KLIPPERBACKUP_REPO_URL,
    KLIPPERBACKUP_DIR,
    KLIPPERBACKUP_CONFIG_DIR,
    MOONRAKER_CONF,
)

from utils.filesystem_utils import check_file_exist
from utils.input_utils import get_confirm
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class KlipperbackupExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        if not KLIPPERBACKUP_DIR.exists():
            subprocess.run(["git", "clone", str(KLIPPERBACKUP_REPO_URL), str(KLIPPERBACKUP_DIR)])
            subprocess.run(["git", "-C", str(KLIPPERBACKUP_DIR), "checkout", "installer-dev"])
            subprocess.run(["chmod", "+x", str(KLIPPERBACKUP_DIR / "install.sh")])
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh")])

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return
        else:
            subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "check_updates"])

    def remove_extension(self, **kwargs) -> None:
        def is_service_installed(service_name):
            command = ["systemctl", "status", service_name]
            result = subprocess.run(command, capture_output=True, text=True)
            # Doesn't matter whether the service is active or not, what matters is whether it is installed. So let's search for "Loaded:" in stdout
            if "Loaded:" in result.stdout:
                return True
            else:
                return False

        def uninstall_service(service_name):
            try:
                subprocess.run(["sudo", "systemctl", "stop", service_name], check=True)
                subprocess.run(["sudo", "systemctl", "disable", service_name], check=True)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                service_path = f'/etc/systemd/system/{service_name}'
                os.system(f'sudo rm {service_path}')
                return True
            except subprocess.CalledProcessError:
                return False

        def check_crontab_entry(entry):
            try:
                crontab_content = subprocess.check_output(["crontab", "-l"], stderr=subprocess.DEVNULL, text=True)
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
            comparison_file_path = os.path.join(str(KLIPPERBACKUP_DIR), 'install-files', 'moonraker.conf')
            if not os.path.exists(original_file_path) or not os.path.exists(comparison_file_path):
                return False
            with open(original_file_path, 'r') as original_file, open(comparison_file_path, 'r') as comparison_file:
                original_content = original_file.read()
                comparison_content = comparison_file.read().strip()
            if comparison_content in original_content:
                modified_content = original_content.replace(comparison_content, '').strip()
                modified_content = "\n".join(line for line in modified_content.split("\n") if line.strip())
                with open(original_file_path, 'w') as original_file:
                    original_file.write(modified_content)
                    return True
            else:
                return False

        question = "Do you really want to remove the extension?"
        if get_confirm(question, True, False):

            # Remove Klipper-Backup services
            service_names = ["klipper-backup-on-boot.service", "klipper-backup-filewatch.service"]
            for service_name in service_names:
                try:
                    Logger.print_status(f"Check whether the service {service_name} is installed ...")
                    if is_service_installed(service_name):
                        Logger.print_info(f"Service {service_name} detected.")
                        if uninstall_service(service_name):
                            Logger.print_ok(f"The service {service_name} has been successfully uninstalled.")
                        else:
                            Logger.print_error(f"Error uninstalling the service {service_name}.")
                    else:
                        Logger.print_info(f"The service {service_name} is not installed. Skipping ...")
                except:
                    Logger.print_error(f"Unable to remove the service {service_name}")

            # Remove Klipper-Backup cron
            Logger.print_status("Check for Klipper-Backup cron entry ...")
            entry_to_check = "/klipper-backup/script.sh"
            try:
                if check_crontab_entry(entry_to_check):
                    crontab_content = subprocess.check_output(["crontab", "-l"], text=True)
                    modified_content = "\n".join(line for line in crontab_content.splitlines() if entry_to_check not in line)
                    subprocess.run(["crontab", "-"], input=modified_content, text=True, check=True)
                    Logger.print_ok("The Klipper-Backup entry has been removed from the crontab.")
                else:
                    Logger.print_info("The Klipper-Backup entry is not present in the crontab. Skipping ...")
            except:
                Logger.print_error("Unable to remove the Klipper-Backup cron entry")

            # Remove Moonraker entry
            Logger.print_status(f"Check for Klipper-Backup moonraker entry ...")
            try:
                if remove_moonraker_entry():
                    Logger.print_ok("Klipper-Backup entry in moonraker.conf removed")
                else:
                    Logger.print_info("Klipper-Backup entry not found in moonraker.conf. Skipping ...")
            except:
                Logger.print_error("Unknown error, either the moonraker.conf is not found or the Klipper-Backup entry under ~/klipper-backup/install-files/moonraker.conf. Skipping ...")

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
