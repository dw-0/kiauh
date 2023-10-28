# !/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import pwd
import shutil
import subprocess
from pathlib import Path
from typing import List

from kiauh.instance_manager.base_instance import BaseInstance
from kiauh.utils.constants import CURRENT_USER, SYSTEMD, KLIPPER_DIR, KLIPPER_ENV_DIR
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import create_directory


# noinspection PyMethodMayBeStatic
class Klipper(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu"]

    def __init__(self, name: str):
        super().__init__(name=name,
                         prefix="klipper",
                         user=CURRENT_USER,
                         data_dir_name=self._get_data_dir_from_name(name))
        self.klipper_dir = KLIPPER_DIR
        self.env_dir = KLIPPER_ENV_DIR
        self.cfg_file = f"{self.cfg_dir}/printer.cfg"
        self.log = f"{self.log_dir}/klippy.log"
        self.serial = f"{self.comms_dir}/klippy.serial"
        self.uds = f"{self.comms_dir}/klippy.sock"

    def create(self) -> None:
        Logger.print_info("Creating Klipper Instance")
        module_path = os.path.dirname(os.path.abspath(__file__))
        service_template_path = os.path.join(module_path, "res",
                                             "klipper.service")
        env_template_file_path = os.path.join(module_path, "res", "klipper.env")
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = f"{SYSTEMD}/{service_file_name}"
        env_file_target = os.path.abspath(f"{self.sysd_dir}/klipper.env")

        # create folder structure
        dirs = [self.data_dir, self.cfg_dir, self.log_dir,
                self.comms_dir, self.sysd_dir]
        for _dir in dirs:
            create_directory(Path(_dir))

        try:
            # writing the klipper service file (requires sudo!)
            service_content = self._prep_service_file(service_template_path,
                                                      env_file_target)
            command = ["sudo", "tee", service_file_target]
            subprocess.run(command, input=service_content.encode(),
                           stdout=subprocess.DEVNULL, check=True)
            Logger.print_ok(f"Service file created: {service_file_target}")

            # writing the klipper.env file
            env_file_content = self._prep_env_file(env_template_file_path)
            with open(env_file_target, "w") as env_file:
                env_file.write(env_file_content)
            Logger.print_ok(f"Env file created: {env_file_target}")

        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error creating service file {service_file_target}: {e}")
            raise
        except OSError as e:
            Logger.print_error(
                f"Error creating env file {env_file_target}: {e}")
            raise

    def read(self) -> None:
        print("Reading Klipper Instance")

    def update(self) -> None:
        print("Updating Klipper Instance")

    def delete(self, del_remnants: bool) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self._get_service_file_path()

        Logger.print_info(f"Deleting Klipper Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            subprocess.run(command, check=True)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise

        if del_remnants:
            self._delete_klipper_remnants()

    def _delete_klipper_remnants(self) -> None:
        try:
            Logger.print_info(f"Delete {self.klipper_dir} ...")
            shutil.rmtree(Path(self.klipper_dir))
            Logger.print_info(f"Delete {self.env_dir} ...")
            shutil.rmtree(Path(self.env_dir))
        except FileNotFoundError:
            Logger.print_info("Cannot delete Klipper directories. Not found.")
        except PermissionError as e:
            Logger.print_error(f"Error deleting Klipper directories: {e}")
            raise

        Logger.print_ok("Directories successfully deleted.")

    def get_service_file_name(self, extension=False) -> str:
        name = self.prefix if self.name is None else self.prefix + '-' + self.name
        return name if not extension else f"{name}.service"

    def _get_service_file_path(self):
        return f"{SYSTEMD}/{self.get_service_file_name(extension=True)}"

    def _get_data_dir_from_name(self, name: str) -> str:
        if name is None:
            return "printer"
        elif int(name.isdigit()):
            return f"printer_{name}"
        else:
            return name

    def _prep_service_file(self, service_template_path, env_file_path):
        try:
            with open(service_template_path, "r") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {service_template_path} - File not found")
            raise
        service_content = template_content.replace("%USER%", self.user)
        service_content = service_content.replace("%KLIPPER_DIR%",
                                                  self.klipper_dir)
        service_content = service_content.replace("%ENV%", self.env_dir)
        service_content = service_content.replace("%ENV_FILE%", env_file_path)
        return service_content

    def _prep_env_file(self, env_template_file_path):
        try:
            with open(env_template_file_path, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {env_template_file_path} - File not found")
            raise
        env_file_content = env_template_file_content.replace("%KLIPPER_DIR%",
                                                             self.klipper_dir)
        env_file_content = env_file_content.replace("%CFG%", self.cfg_file)
        env_file_content = env_file_content.replace("%SERIAL%", self.serial)
        env_file_content = env_file_content.replace("%LOG%", self.log)
        env_file_content = env_file_content.replace("%UDS%", self.uds)
        return env_file_content