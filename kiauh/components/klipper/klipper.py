# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run
from typing import List

from components.klipper import (
    KLIPPER_CFG_NAME,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_ENV_FILE_NAME,
    KLIPPER_ENV_FILE_TEMPLATE,
    KLIPPER_LOG_NAME,
    KLIPPER_SERIAL_NAME,
    KLIPPER_SERVICE_TEMPLATE,
    KLIPPER_UDS_NAME,
)
from core.instance_manager.base_instance import BaseInstance
from utils.constants import SYSTEMD
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class Klipper(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu"]

    def __init__(self, suffix: str = ""):
        super().__init__(instance_type=self, suffix=suffix)
        self.klipper_dir: Path = KLIPPER_DIR
        self.env_dir: Path = KLIPPER_ENV_DIR
        self._cfg_file = self.cfg_dir.joinpath(KLIPPER_CFG_NAME)
        self._log = self.log_dir.joinpath(KLIPPER_LOG_NAME)
        self._serial = self.comms_dir.joinpath(KLIPPER_SERIAL_NAME)
        self._uds = self.comms_dir.joinpath(KLIPPER_UDS_NAME)

    @property
    def cfg_file(self) -> Path:
        return self._cfg_file

    @property
    def log(self) -> Path:
        return self._log

    @property
    def serial(self) -> Path:
        return self._serial

    @property
    def uds(self) -> Path:
        return self._uds

    def create(self) -> None:
        Logger.print_status("Creating new Klipper Instance ...")

        try:
            self.create_folders()
            self._write_service_file()
            self._write_env_file()

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def delete(self) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(f"Removing Klipper Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            run(command, check=True)
            self._delete_logfiles()
            Logger.print_ok("Instance successfully removed!")
        except CalledProcessError as e:
            Logger.print_error(f"Error removing instance: {e}")
            raise

    def _write_service_file(self) -> None:
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = SYSTEMD.joinpath(service_file_name)
        service_content = self._prep_service_file()
        command = ["sudo", "tee", service_file_target]
        run(
            command,
            input=service_content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {service_file_target}")

    def _write_env_file(self) -> None:
        env_file_content = self._prep_env_file()
        env_file_target = self.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME)

        with open(env_file_target, "w") as env_file:
            env_file.write(env_file_content)

        Logger.print_ok(f"Env file created: {env_file_target}")

    def _prep_service_file(self) -> str:
        template = KLIPPER_SERVICE_TEMPLATE

        try:
            with open(template, "r") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            Logger.print_error(f"Unable to open {template} - File not found")
            raise

        service_content = template_content.replace(
            "%USER%",
            self.user,
        )
        service_content = service_content.replace(
            "%KLIPPER_DIR%",
            self.klipper_dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV%",
            self.env_dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV_FILE%",
            self.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME).as_posix(),
        )
        return service_content

    def _prep_env_file(self) -> str:
        template = KLIPPER_ENV_FILE_TEMPLATE

        try:
            with open(template, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(f"Unable to open {template} - File not found")
            raise

        env_file_content = env_template_file_content.replace(
            "%KLIPPER_DIR%", self.klipper_dir.as_posix()
        )
        env_file_content = env_file_content.replace(
            "%CFG%",
            f"{self.cfg_dir}/{KLIPPER_CFG_NAME}",
        )
        env_file_content = env_file_content.replace(
            "%SERIAL%",
            self.serial.as_posix(),
        )
        env_file_content = env_file_content.replace(
            "%LOG%",
            self.log.as_posix(),
        )
        env_file_content = env_file_content.replace(
            "%UDS%",
            self.uds.as_posix(),
        )

        return env_file_content

    def _delete_logfiles(self) -> None:
        from utils.fs_utils import run_remove_routines

        files = self.log_dir.iterdir()
        logs = [f for f in files if f.name.startswith(KLIPPER_LOG_NAME)]
        for log in logs:
            Logger.print_status(f"Remove '{log}'")
            run_remove_routines(log)
