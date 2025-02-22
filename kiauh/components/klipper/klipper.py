# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import dataclass, field
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
from core.constants import CURRENT_USER
from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from utils.fs_utils import create_folders, get_data_dir
from utils.sys_utils import get_service_file_path


# noinspection PyMethodMayBeStatic
@dataclass(repr=True)
class Klipper:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    service_file_path: Path = field(init=False)
    log_file_name: str = KLIPPER_LOG_NAME
    klipper_dir: Path = KLIPPER_DIR
    env_dir: Path = KLIPPER_ENV_DIR
    data_dir: Path = field(init=False)
    cfg_file: Path = field(init=False)
    env_file: Path = field(init=False)
    serial: Path = field(init=False)
    uds: Path = field(init=False)

    def __post_init__(self):
        self.base: BaseInstance = BaseInstance(Klipper, self.suffix)
        self.base.log_file_name = self.log_file_name

        self.service_file_path: Path = get_service_file_path(Klipper, self.suffix)
        self.data_dir: Path = get_data_dir(Klipper, self.suffix)
        self.cfg_file: Path = self.base.cfg_dir.joinpath(KLIPPER_CFG_NAME)
        self.env_file: Path = self.base.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME)
        self.serial: Path = self.base.comms_dir.joinpath(KLIPPER_SERIAL_NAME)
        self.uds: Path = self.base.comms_dir.joinpath(KLIPPER_UDS_NAME)

    def create(self) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Klipper Instance ...")

        try:
            create_folders(self.base.base_folders)

            create_service_file(
                name=self.service_file_path.name,
                content=self._prep_service_file_content(),
            )

            create_env_file(
                path=self.base.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME),
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
            CURRENT_USER,
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
            self.base.sysd_dir.joinpath(KLIPPER_ENV_FILE_NAME).as_posix(),
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
            f"{self.base.cfg_dir}/{KLIPPER_CFG_NAME}",
        )
        env_file_content = env_file_content.replace(
            "%SERIAL%",
            self.serial.as_posix() if self.serial else "",
        )
        env_file_content = env_file_content.replace(
            "%LOG%",
            self.base.log_dir.joinpath(self.log_file_name).as_posix(),
        )
        env_file_content = env_file_content.replace(
            "%UDS%",
            self.uds.as_posix() if self.uds else "",
        )

        return env_file_content
