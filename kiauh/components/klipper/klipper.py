# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError

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
from core.logger import Logger


# noinspection PyMethodMayBeStatic
@dataclass
class Klipper(BaseInstance):
    klipper_dir: Path = KLIPPER_DIR
    env_dir: Path = KLIPPER_ENV_DIR
    log_file_name = KLIPPER_LOG_NAME
    cfg_file: Path | None = None
    serial: Path | None = None
    uds: Path | None = None

    def __init__(self, suffix: str = "") -> None:
        super().__init__(suffix=suffix)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.cfg_file = self.cfg_dir.joinpath(KLIPPER_CFG_NAME)
        self.serial = self.comms_dir.joinpath(KLIPPER_SERIAL_NAME)
        self.uds = self.comms_dir.joinpath(KLIPPER_UDS_NAME)

    def create(self) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Klipper Instance ...")

        try:
            self.create_folders()

            create_service_file(
                name=self.service_file_path.name,
                content=self._prep_service_file_content(),
            )

            create_env_file(
                path=self.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME),
                content=self._prep_env_file_content(),
            )

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def _prep_service_file_content(self) -> str:
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

    def _prep_env_file_content(self) -> str:
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
            self.serial.as_posix() if self.serial else "",
        )
        env_file_content = env_file_content.replace(
            "%LOG%",
            self.log_dir.joinpath(self.log_file_name).as_posix(),
        )
        env_file_content = env_file_content.replace(
            "%UDS%",
            self.uds.as_posix() if self.uds else "",
        )

        return env_file_content
