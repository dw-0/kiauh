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
import re
import subprocess
from typing import List, Optional, Union, TypeVar

from kiauh.core.instance_manager.base_instance import BaseInstance
from kiauh.utils.constants import SYSTEMD
from kiauh.utils.logger import Logger


I = TypeVar(name="I", bound=BaseInstance, covariant=True)


# noinspection PyMethodMayBeStatic
class InstanceManager:
    def __init__(self, instance_type: I) -> None:
        self._instance_type = instance_type
        self._current_instance: Optional[I] = None
        self._instance_suffix: Optional[str] = None
        self._instance_service: Optional[str] = None
        self._instance_service_full: Optional[str] = None
        self._instance_service_path: Optional[str] = None
        self._instances: List[I] = []

    @property
    def instance_type(self) -> I:
        return self._instance_type

    @instance_type.setter
    def instance_type(self, value: I):
        self._instance_type = value

    @property
    def current_instance(self) -> I:
        return self._current_instance

    @current_instance.setter
    def current_instance(self, value: I) -> None:
        self._current_instance = value
        self.instance_suffix = value.suffix
        self.instance_service = value.get_service_file_name()
        self.instance_service_path = value.get_service_file_path()

    @property
    def instance_suffix(self) -> str:
        return self._instance_suffix

    @instance_suffix.setter
    def instance_suffix(self, value: str):
        self._instance_suffix = value

    @property
    def instance_service(self) -> str:
        return self._instance_service

    @instance_service.setter
    def instance_service(self, value: str):
        self._instance_service = value

    @property
    def instance_service_full(self) -> str:
        return f"{self._instance_service}.service"

    @property
    def instance_service_path(self) -> str:
        return self._instance_service_path

    @instance_service_path.setter
    def instance_service_path(self, value: str):
        self._instance_service_path = value

    @property
    def instances(self) -> List[I]:
        if not self._instances:
            self._instances = self._find_instances()

        return sorted(self._instances, key=lambda x: self._sort_instance_list(x.suffix))

    @instances.setter
    def instances(self, value: List[I]):
        self._instances = value

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
        Logger.print_status(f"Enabling {self.instance_service_full} ...")
        try:
            command = ["sudo", "systemctl", "enable", self.instance_service_full]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_service_full} enabled.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error enabling service {self.instance_service_full}:")
            Logger.print_error(f"{e}")

    def disable_instance(self) -> None:
        Logger.print_status(f"Disabling {self.instance_service_full} ...")
        try:
            command = ["sudo", "systemctl", "disable", self.instance_service_full]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_service_full} disabled.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error disabling {self.instance_service_full}:")
            Logger.print_error(f"{e}")

    def start_instance(self) -> None:
        Logger.print_status(f"Starting {self.instance_service_full} ...")
        try:
            command = ["sudo", "systemctl", "start", self.instance_service_full]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_service_full} started.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error starting {self.instance_service_full}:")
            Logger.print_error(f"{e}")

    def restart_instance(self) -> None:
        Logger.print_status(f"Restarting {self.instance_service_full} ...")
        try:
            command = ["sudo", "systemctl", "restart", self.instance_service_full]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_service_full} restarted.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error restarting {self.instance_service_full}:")
            Logger.print_error(f"{e}")

    def start_all_instance(self) -> None:
        for instance in self.instances:
            self.current_instance = instance
            self.start_instance()

    def restart_all_instance(self) -> None:
        for instance in self.instances:
            self.current_instance = instance
            self.restart_instance()

    def stop_instance(self) -> None:
        Logger.print_status(f"Stopping {self.instance_service_full} ...")
        try:
            command = ["sudo", "systemctl", "stop", self.instance_service_full]
            if subprocess.run(command, check=True):
                Logger.print_ok(f"{self.instance_service_full} stopped.")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error stopping {self.instance_service_full}:")
            Logger.print_error(f"{e}")
            raise

    def stop_all_instance(self) -> None:
        for instance in self.instances:
            self.current_instance = instance
            self.stop_instance()

    def reload_daemon(self) -> None:
        Logger.print_status("Reloading systemd manager configuration ...")
        try:
            command = ["sudo", "systemctl", "daemon-reload"]
            if subprocess.run(command, check=True):
                Logger.print_ok("Systemd manager configuration reloaded")
        except subprocess.CalledProcessError as e:
            Logger.print_error("Error reloading systemd manager configuration:")
            Logger.print_error(f"{e}")
            raise

    def _find_instances(self) -> List[I]:
        name = self.instance_type.__name__.lower()
        pattern = re.compile(f"^{name}(-[0-9a-zA-Z]+)?.service$")
        excluded = self.instance_type.blacklist()

        service_list = [
            os.path.join(SYSTEMD, service)
            for service in os.listdir(SYSTEMD)
            if pattern.search(service) and not any(s in service for s in excluded)
        ]

        instance_list = [
            self.instance_type(suffix=self._get_instance_suffix(service))
            for service in service_list
        ]

        return instance_list

    def _get_instance_suffix(self, file_path: str) -> Union[str, None]:
        full_name = file_path.split("/")[-1].split(".")[0]

        return full_name.split("-")[-1] if "-" in full_name else None

    def _sort_instance_list(self, s: Union[int, str, None]):
        if s is None:
            return

        return int(s) if s.isdigit() else s
