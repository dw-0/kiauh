# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
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

from components.klipper.klipper import Klipper
from components.moonraker import (
    MOONRAKER_CFG_NAME,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_ENV_FILE_NAME,
    MOONRAKER_ENV_FILE_TEMPLATE,
    MOONRAKER_LOG_NAME,
    MOONRAKER_SERVICE_TEMPLATE,
)
from core.constants import CURRENT_USER
from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from utils.fs_utils import create_folders
from utils.sys_utils import get_service_file_path


# noinspection PyMethodMayBeStatic
@dataclass
class Moonraker:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    service_file_path: Path = field(init=False)
    log_file_name: str = MOONRAKER_LOG_NAME
    moonraker_dir: Path = MOONRAKER_DIR
    env_dir: Path = MOONRAKER_ENV_DIR
    data_dir: Path = field(init=False)
    cfg_file: Path = field(init=False)
    env_file: Path = field(init=False)
    backup_dir: Path = field(init=False)
    certs_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    port: int | None = field(init=False)

    def __post_init__(self):
        self.base: BaseInstance = BaseInstance(Klipper, self.suffix)
        self.base.log_file_name = self.log_file_name

        self.service_file_path: Path = get_service_file_path(Moonraker, self.suffix)
        self.data_dir: Path = self.base.data_dir
        self.cfg_file: Path = self.base.cfg_dir.joinpath(MOONRAKER_CFG_NAME)
        self.env_file: Path = self.base.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME)
        self.backup_dir: Path = self.base.data_dir.joinpath("backup")
        self.certs_dir: Path = self.base.data_dir.joinpath("certs")
        self.db_dir: Path = self.base.data_dir.joinpath("database")
        self.port: int | None = self._get_port()

    def create(self) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Moonraker Instance ...")

        try:
            create_folders(self.base.base_folders)

            create_service_file(
                name=self.service_file_path.name,
                content=self._prep_service_file_content(),
            )
            create_env_file(
                path=self.base.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME),
                content=self._prep_env_file_content(),
            )

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def _prep_service_file_content(self) -> str:
        template = MOONRAKER_SERVICE_TEMPLATE

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
            "%MOONRAKER_DIR%",
            self.moonraker_dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV%",
            self.env_dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV_FILE%",
            self.base.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME).as_posix(),
        )
        return service_content

    def _prep_env_file_content(self) -> str:
        template = MOONRAKER_ENV_FILE_TEMPLATE

        try:
            with open(template, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(f"Unable to open {template} - File not found")
            raise

        env_file_content = env_template_file_content.replace(
            "%MOONRAKER_DIR%",
            self.moonraker_dir.as_posix(),
        )
        env_file_content = env_file_content.replace(
            "%PRINTER_DATA%",
            self.base.data_dir.as_posix(),
        )

        return env_file_content

    def _get_port(self) -> int | None:
        if not self.cfg_file or not self.cfg_file.is_file():
            return None

        scp = SimpleConfigParser()
        scp.read_file(self.cfg_file)
        port: int | None = scp.getint("server", "port", fallback=None)

        return port
