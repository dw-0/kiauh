# ======================================================================= #
#  Copyright (C) 2023 - 2026 Staubgeborener and Tylerjet                  #
#  https://github.com/Staubgeborener/klipper-backup                       #
#  https://klipperbackup.xyz                                              #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import subprocess
from pathlib import Path

from core.constants import SYSTEMD
from core.i18n import _tr
from core.logger import Logger
from extensions.base_extension import BaseExtension
from extensions.klipper_backup import (
    KLIPPERBACKUP_CONFIG_DIR,
    KLIPPERBACKUP_DIR,
    KLIPPERBACKUP_REPO_URL,
    MOONRAKER_CONF,
)
from utils.fs_utils import check_file_exist, remove_with_sudo
from utils.git_utils import git_cmd_clone
from utils.input_utils import get_confirm
from utils.sys_utils import cmd_sysctl_manage, remove_system_service, unit_file_exists


class KlipperbackupExtension(BaseExtension):
    def remove_extension(self, **kwargs) -> None:
        if not check_file_exist(KLIPPERBACKUP_DIR):
            Logger.print_info(_tr("Extension does not seem to be installed! Skipping ..."))
            return

        def uninstall_service(service_name: str, unit_type: str) -> bool:
            try:
                full_service_name = f"{service_name}.{unit_type}"
                if unit_type == "service":
                    remove_system_service(full_service_name)
                elif unit_type == "timer":
                    full_service_path: Path = SYSTEMD.joinpath(full_service_name)
                    Logger.print_status(_tr("Removing {} ...").format(full_service_name))
                    remove_with_sudo(full_service_path)
                    Logger.print_ok(_tr("{}.{} successfully removed!").format(service_name, unit_type))
                    cmd_sysctl_manage("daemon-reload")
                    cmd_sysctl_manage("reset-failed")
                else:
                    Logger.print_error(
                        _tr("Unknown unit type {} of {}").format(unit_type, full_service_name)
                    )
            except Exception as e:
                Logger.print_error(_tr("Failed to remove {}: {}").format(full_service_name, str(e)))

        def check_crontab_entry(entry) -> bool:
            try:
                crontab_content = subprocess.check_output(
                    ["crontab", "-l"], stderr=subprocess.DEVNULL, text=True
                )
            except subprocess.CalledProcessError:
                return False
            return any(entry in line for line in crontab_content.splitlines())

        def remove_moonraker_entry():
            original_file_path = MOONRAKER_CONF
            comparison_file_path = os.path.join(
                str(KLIPPERBACKUP_DIR), "install-files", "moonraker.conf"
            )
            if not (
                os.path.exists(original_file_path)
                and os.path.exists(comparison_file_path)
            ):
                return False
            with open(original_file_path, "r") as original_file, open(
                comparison_file_path, "r"
            ) as comparison_file:
                original_content = original_file.read()
                comparison_content = comparison_file.read()
            if comparison_content in original_content:
                Logger.print_status(_tr("Removing Klipper-Backup moonraker entry ..."))
                modified_content = original_content.replace(
                    comparison_content, ""
                ).strip()
                modified_content = "\n".join(
                    line for line in modified_content.split("\n") if line.strip()
                )
                with open(original_file_path, "w") as original_file:
                    original_file.write(modified_content)
                Logger.print_ok(_tr("Klipper-Backup moonraker entry successfully removed!"))
                return True
            return False

        if get_confirm(_tr("Do you really want to remove the extension?"), True, False):
            service_names = [
                "klipper-backup-on-boot",
                "klipper-backup-filewatch",
                "klipper-backup",
            ]
            unit_types = ["timer", "service"]

            for service_name in service_names:
                for unit_type in unit_types:
                    if unit_file_exists(service_name, unit_type):
                        uninstall_service(service_name, unit_type)

            try:
                if check_crontab_entry("/klipper-backup/script.sh"):
                    Logger.print_status(_tr("Removing Klipper-Backup crontab entry ..."))
                    crontab_content = subprocess.check_output(
                        ["crontab", "-l"], text=True
                    )
                    modified_content = "\n".join(
                        line
                        for line in crontab_content.splitlines()
                        if "/klipper-backup/script.sh" not in line
                    )
                    subprocess.run(
                        ["crontab", "-"],
                        input=modified_content + "\n",
                        text=True,
                        check=True,
                    )
                    Logger.print_ok(
                        _tr("Klipper-Backup crontab entry successfully removed!")
                    )
            except subprocess.CalledProcessError:
                Logger.print_error(_tr("Unable to remove the Klipper-Backup cron entry"))

            try:
                remove_moonraker_entry()
            except Exception:
                Logger.print_error(
                    _tr("Unable to remove the Klipper-Backup moonraker entry")
                )

            Logger.print_status(_tr("Removing Klipper-Backup extension ..."))
            try:
                remove_with_sudo(KLIPPERBACKUP_DIR)
                if check_file_exist(KLIPPERBACKUP_CONFIG_DIR):
                    remove_with_sudo(KLIPPERBACKUP_CONFIG_DIR)
                Logger.print_ok(_tr("Extension Klipper-Backup successfully removed!"))
            except Exception:
                Logger.print_error(_tr("Unable to remove Klipper-Backup extension"))

    def install_extension(self, **kwargs) -> None:
        if not KLIPPERBACKUP_DIR.exists():
            git_cmd_clone(KLIPPERBACKUP_REPO_URL, KLIPPERBACKUP_DIR)
            subprocess.run(["chmod", "+x", str(KLIPPERBACKUP_DIR / "install.sh")])
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh")])

    def update_extension(self, **kwargs) -> None:
        if not check_file_exist(KLIPPERBACKUP_DIR):
            Logger.print_info(_tr("Extension does not seem to be installed! Skipping ..."))
            return
        subprocess.run([str(KLIPPERBACKUP_DIR / "install.sh"), "check_updates"])
