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

from extensions.base_extension import BaseExtension
from extensions.klipper_backup import (
    KLIPPERBACKUP_REPO_URL,
    KLIPPERBACKUP_DIR,
    KLIPPERBACKUP_CONFIG_DIR,
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

        def is_service_installed(service_names):
            installed = True
            for service_name in service_names:
                try:
                    with open(os.devnull, 'w') as devnull:
                        subprocess.run(["systemctl", "status", service_name], stdout=devnull, stderr=devnull, check=True)
                except subprocess.CalledProcessError:
                    installed = False
                    break
            return installed

        def uninstall_service(service_names):
            for service_name in service_names:
                try:
                    subprocess.run(["sudo", "systemctl", "disable", service_name], check=True)
                    subprocess.run(["sudo", "systemctl", "stop", service_name], check=True)
                    Logger.print_ok(f"The service {service_name} has been successfully uninstalled.")
                except subprocess.CalledProcessError:
                    Logger.print_error(f"Error uninstalling the service {service_name}.")


        extension_installed = check_file_exist(KLIPPERBACKUP_DIR)
        if not extension_installed:
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        question = "Do you really want to remove the extension?"
        if get_confirm(question, True, False):
            try:
                Logger.print_status(f"Removing '{KLIPPERBACKUP_DIR}' ...")
                shutil.rmtree(KLIPPERBACKUP_DIR)
                config_backup_exists = check_file_exist(KLIPPERBACKUP_CONFIG_DIR)
                if config_backup_exists:
                    shutil.rmtree(KLIPPERBACKUP_CONFIG_DIR)
                Logger.print_ok("Extension successfully removed!")
            except OSError as e:
                Logger.print_error(f"Unable to remove extension: {e}")

            service_names = ["klipper-backup-on-boot.service", "klipper-backup-filewatch.service"]

            for service_name in service_names:
                if is_service_installed(service_name):
                    uninstall_service(service_name)
                else:
                    Logger.print_info(f"The service {service_name} is not installed. Skipping ...")