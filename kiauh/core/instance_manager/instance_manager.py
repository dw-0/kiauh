# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError
from typing import List

from core.logger import Logger
from utils.instance_type import InstanceType
from utils.sys_utils import cmd_sysctl_service


class InstanceManager:
    @staticmethod
    def enable(instance: InstanceType) -> None:
        service_name: str = instance.service_file_path.name
        try:
            cmd_sysctl_service(service_name, "enable")
        except CalledProcessError as e:
            Logger.print_error(f"Error enabling service {service_name}:")
            Logger.print_error(f"{e}")

    @staticmethod
    def disable(instance: InstanceType) -> None:
        service_name: str = instance.service_file_path.name
        try:
            cmd_sysctl_service(service_name, "disable")
        except CalledProcessError as e:
            Logger.print_error(f"Error disabling {service_name}: {e}")
            raise

    @staticmethod
    def start(instance: InstanceType) -> None:
        service_name: str = instance.service_file_path.name
        try:
            cmd_sysctl_service(service_name, "start")
        except CalledProcessError as e:
            Logger.print_error(f"Error starting {service_name}: {e}")
            raise

    @staticmethod
    def stop(instance: InstanceType) -> None:
        name: str = instance.service_file_path.name
        try:
            cmd_sysctl_service(name, "stop")
        except CalledProcessError as e:
            Logger.print_error(f"Error stopping {name}: {e}")
            raise

    @staticmethod
    def restart(instance: InstanceType) -> None:
        name: str = instance.service_file_path.name
        try:
            cmd_sysctl_service(name, "restart")
        except CalledProcessError as e:
            Logger.print_error(f"Error restarting {name}: {e}")
            raise

    @staticmethod
    def start_all(instances: List[InstanceType]) -> None:
        for instance in instances:
            InstanceManager.start(instance)

    @staticmethod
    def stop_all(instances: List[InstanceType]) -> None:
        for instance in instances:
            InstanceManager.stop(instance)

    @staticmethod
    def restart_all(instances: List[InstanceType]) -> None:
        for instance in instances:
            InstanceManager.restart(instance)

    @staticmethod
    def remove(instance: InstanceType) -> None:
        from utils.fs_utils import run_remove_routines
        from utils.sys_utils import remove_system_service

        try:
            # remove the service file
            service_file_path: Path = instance.service_file_path
            if service_file_path is not None:
                remove_system_service(service_file_path.name)

            # then remove all the log files
            if (
                not instance.log_file_name
                or not instance.base.log_dir
                or not instance.base.log_dir.exists()
            ):
                return

            files = instance.base.log_dir.iterdir()
            logs = [f for f in files if f.name.startswith(instance.log_file_name)]
            for log in logs:
                Logger.print_status(f"Remove '{log}'")
                run_remove_routines(log)

        except Exception as e:
            Logger.print_error(f"Error removing service: {e}")
            raise
