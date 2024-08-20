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
from utils.fs_utils import (
    check_file_exist,
    remove_with_sudo,
    )
from utils.git_utils import git_cmd_clone
from utils.input_utils import get_confirm
from utils.sys_utils import (
    cmd_sysctl_service,
    remove_system_service,
    unit_file_exists,
)

# noinspection PyMethodMayBeStatic
class KlipperbackupExtension(BaseExtension):

    def remove_extension(self, **kwargs) -> None:

        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        def uninstall_service(service_name: str, unit_type: str) -> bool:
            try:
                full_service_name = f"{service_name}.{unit_type}"
                if unit_type == "service":
                    remove_system_service(full_service_name)
                    return True
                elif unit_type == "timer":
                    full_service_path: Path = SYSTEMD.joinpath(full_service_name)
                    cmd_sysctl_service(full_service_name, "stop")
                    remove_with_sudo(full_service_path)
                    cmd_sysctl_manage("daemon-reload")
                    cmd_sysctl_manage("reset-failed")
                    Logger.print_ok(f"{full_service_name} successfully removed!")
                    return True
                else:
                    return False
            except:
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
                Logger.print_status("Removing Klipper-Backup moonraker entry ...")
                modified_content = original_content.replace(
                    comparison_content, ""
                ).strip()
                modified_content = "\n".join(
                    line for line in modified_content.split("\n") if line.strip()
                )
                with open(original_file_path, "w") as original_file:
                    original_file.write(modified_content)
                    Logger.print_ok("Klipper-Backup moonraker entry successfully removed!")
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
                    for unit_type in unit_types:
                        full_service_name = f"{service_name}.{unit_type}"
                        if unit_file_exists(service_name, unit_type):
                            uninstall_service(service_name, unit_type)
                except Exception as e:
                    Logger.print_error(f"Unable to remove the {service_name} service: {e}")

            # Remove Klipper-Backup cron
            entry_to_check = "/klipper-backup/script.sh"
            try:
                if check_crontab_entry(entry_to_check):
                    Logger.print_status("Removing Klipper-Backup crontab entry ...")
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
                    Logger.print_ok("Klipper-Backup crontab entry successfully removed!")
            except subprocess.CalledProcessError:
                Logger.print_error("Unable to remove the Klipper-Backup cron entry")

            # Remove Moonraker entry
            try:
                remove_moonraker_entry()
            except:
                Logger.print_error("Unable to remove the Klipper-Backup moonraker entry")

            # Remove Klipper-Backup
            Logger.print_status("Removing Klipper-Backup extension ...")
            try:
                shutil.rmtree(KLIPPERBACKUP_DIR)
                config_backup_exists = check_file_exist(KLIPPERBACKUP_CONFIG_DIR)
                if config_backup_exists:
                    shutil.rmtree(KLIPPERBACKUP_CONFIG_DIR)
                Logger.print_ok("Extension Klipper-Backup successfully removed!")
            except OSError as e:
                Logger.print_error(f"Unable to remove Klipper-Backup extension: {e}")

    def install_extension(self, **kwargs) -> None:
        if not KLIPPERBACKUP_DIR.exists():
            git_cmd_clone(KLIPPERBACKUP_REPO_URL, KLIPPERBACKUP_DIR)
            subprocess.run(["chmod", "+x", str(KLIPPERBACKUP_DIR / "install.sh")])
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh")])

    def update_extension(self, **kwargs) -> None:
        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return
        else:
            subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "check_updates"])
