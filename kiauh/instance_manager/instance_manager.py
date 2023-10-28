#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, List, Type, Union

from kiauh.instance_manager.base_instance import BaseInstance
from kiauh.utils.constants import SYSTEMD
from kiauh.utils.logger import Logger


# noinspection PyMethodMayBeStatic
class InstanceManager:
    def __init__(self, instance_type: Type[BaseInstance],
        current_instance: Optional[BaseInstance] = None) -> None:
        self.instance_type = instance_type
        self.current_instance = current_instance
        self.instance_name = current_instance.name if current_instance is not None else None
        self.instances = []

    def get_current_instance(self) -> BaseInstance:
        return self.current_instance

    def set_current_instance(self, instance: BaseInstance) -> None:
        self.current_instance = instance
        self.instance_name = f"{instance.prefix}-{instance.name}" if instance.name else instance.prefix

    def create_instance(self) -> None:
        if self.current_instance is not None:
            try:
                self.current_instance.create()
            except (OSError, subprocess.CalledProcessError) as e:
                Logger.print_error(f"Creating instance failed: {e}")
                raise
        else:
            raise ValueError("current_instance cannot be None")

    def delete_instance(self, del_remnants=False) -> None:
        if self.current_instance is not None:
            try:
                self.current_instance.delete(del_remnants)
            except (OSError, subprocess.CalledProcessError) as e:
                Logger.print_error(f"Removing instance failed: {e}")
                raise
        else:
            raise ValueError("current_instance cannot be None")

    def enable_instance(self) -> None:
        Logger.print_info(f"Enabling {self.instance_name}.service ...")
        try:
            command = ["sudo", "systemctl", "enable",
                       f"{self.instance_name}.service"]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_name}.service enabled.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error enabling service {self.instance_name}.service:")
            Logger.print_error(f"{e}")

    def disable_instance(self) -> None:
        Logger.print_info(f"Disabling {self.instance_name}.service ...")
        try:
            command = ["sudo", "systemctl", "disable",
                       f"{self.instance_name}.service"]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_name}.service disabled.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error disabling service {self.instance_name}.service:")
            Logger.print_error(f"{e}")

    def start_instance(self) -> None:
        Logger.print_info(f"Starting {self.instance_name}.service ...")
        try:
            command = ["sudo", "systemctl", "start",
                       f"{self.instance_name}.service"]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_name}.service started.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error starting service {self.instance_name}.service:")
            Logger.print_error(f"{e}")

    def stop_instance(self) -> None:
        Logger.print_info(f"Stopping {self.instance_name}.service ...")
        try:
            command = ["sudo", "systemctl", "stop",
                       f"{self.instance_name}.service"]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_name}.service stopped.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error stopping service {self.instance_name}.service:")
            Logger.print_error(f"{e}")
            raise

    def reload_daemon(self) -> None:
        Logger.print_info("Reloading systemd manager configuration ...")
        try:
            command = ["sudo", "systemctl", "daemon-reload"]
            if subprocess.run(command, check=True):
                Logger.print_ok("Systemd manager configuration reloaded")
        except subprocess.CalledProcessError as e:
            Logger.print_error("Error reloading systemd manager configuration:")
            Logger.print_error(f"{e}")
            raise

    def get_instances(self) -> List[BaseInstance]:
        if not self.instances:
            self._find_instances()

        return sorted(self.instances,
                      key=lambda x: self._sort_instance_list(x.name))

    def _find_instances(self) -> None:
        prefix = self.instance_type.__name__.lower()
        pattern = re.compile(f"{prefix}(-[0-9a-zA-Z]+)?.service")

        excluded = self.instance_type.blacklist()
        service_list = [
            os.path.join(SYSTEMD, service)
            for service in os.listdir(SYSTEMD)
            if pattern.search(service)
               and not any(s in service for s in excluded)]

        instance_list = [
            self.instance_type(name=self._get_instance_name(Path(service)))
            for service in service_list]

        self.instances = instance_list

    def _get_instance_name(self, file_path: Path) -> Union[str, None]:
        full_name = str(file_path).split("/")[-1].split(".")[0]
        if full_name.isalnum():
            return None

        return full_name.split("-")[-1]

    def _sort_instance_list(self, s):
        if s is None:
            return

        return int(s) if s.isdigit() else s
