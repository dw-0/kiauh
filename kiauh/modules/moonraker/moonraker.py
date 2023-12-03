#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Union

from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.core.instance_manager.base_instance import BaseInstance
from kiauh.modules.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR, MODULE_PATH
from kiauh.utils.constants import SYSTEMD
from kiauh.utils.logger import Logger


# noinspection PyMethodMayBeStatic
class Moonraker(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu"]

    def __init__(self, suffix: str = None):
        super().__init__(instance_type=self, suffix=suffix)
        self.moonraker_dir = MOONRAKER_DIR
        self.env_dir = MOONRAKER_ENV_DIR
        self.cfg_file = self._get_cfg()
        self.port = self._get_port()
        self.backup_dir = f"{self.data_dir}/backup"
        self.certs_dir = f"{self.data_dir}/certs"
        self.db_dir = f"{self.data_dir}/database"
        self.log = f"{self.log_dir}/moonraker.log"

    def create(self, create_example_cfg: bool = False) -> None:
        Logger.print_status("Creating new Moonraker Instance ...")
        service_template_path = os.path.join(MODULE_PATH, "res", "moonraker.service")
        env_template_file_path = os.path.join(MODULE_PATH, "res", "moonraker.env")
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = f"{SYSTEMD}/{service_file_name}"
        env_file_target = os.path.abspath(f"{self.sysd_dir}/moonraker.env")

        try:
            self.create_folders([self.backup_dir, self.certs_dir, self.db_dir])
            self.write_service_file(
                service_template_path, service_file_target, env_file_target
            )
            self.write_env_file(env_template_file_path, env_file_target)

        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error creating service file {service_file_target}: {e}"
            )
            raise
        except OSError as e:
            Logger.print_error(f"Error writing file: {e}")
            raise

    def delete(self, del_remnants: bool) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(f"Deleting Moonraker Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            subprocess.run(command, check=True)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise

        if del_remnants:
            self._delete_moonraker_remnants()

    def write_service_file(
        self, service_template_path: str, service_file_target: str, env_file_target: str
    ):
        service_content = self._prep_service_file(
            service_template_path, env_file_target
        )
        command = ["sudo", "tee", service_file_target]
        subprocess.run(
            command,
            input=service_content.encode(),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {service_file_target}")

    def write_env_file(self, env_template_file_path: str, env_file_target: str):
        env_file_content = self._prep_env_file(env_template_file_path)
        with open(env_file_target, "w") as env_file:
            env_file.write(env_file_content)
        Logger.print_ok(f"Env file created: {env_file_target}")

    def _delete_moonraker_remnants(self) -> None:
        try:
            Logger.print_status(f"Delete {self.moonraker_dir} ...")
            shutil.rmtree(Path(self.moonraker_dir))
            Logger.print_status(f"Delete {self.env_dir} ...")
            shutil.rmtree(Path(self.env_dir))
        except FileNotFoundError:
            Logger.print_status("Cannot delete Moonraker directories. Not found.")
        except PermissionError as e:
            Logger.print_error(f"Error deleting Moonraker directories: {e}")
            raise

        Logger.print_ok("Directories successfully deleted.")

    def _prep_service_file(self, service_template_path, env_file_path):
        try:
            with open(service_template_path, "r") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {service_template_path} - File not found"
            )
            raise
        service_content = template_content.replace("%USER%", self.user)
        service_content = service_content.replace("%MOONRAKER_DIR%", self.moonraker_dir)
        service_content = service_content.replace("%ENV%", self.env_dir)
        service_content = service_content.replace("%ENV_FILE%", env_file_path)
        return service_content

    def _prep_env_file(self, env_template_file_path):
        try:
            with open(env_template_file_path, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {env_template_file_path} - File not found"
            )
            raise
        env_file_content = env_template_file_content.replace(
            "%MOONRAKER_DIR%", self.moonraker_dir
        )
        env_file_content = env_file_content.replace("%PRINTER_DATA%", self.data_dir)
        return env_file_content

    def _get_cfg(self):
        cfg_file_loc = f"{self.cfg_dir}/moonraker.conf"
        if Path(cfg_file_loc).is_file():
            return cfg_file_loc
        return None

    def _get_port(self) -> Union[int, None]:
        if self.cfg_file is None:
            return None

        cm = ConfigManager(cfg_file=self.cfg_file)
        cm.read_config()
        port = cm.get_value("server", "port")

        return int(port) if port is not None else port
