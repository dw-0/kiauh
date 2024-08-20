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

from components.moonraker import (
    MOONRAKER_CFG_NAME,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_ENV_FILE_NAME,
    MOONRAKER_ENV_FILE_TEMPLATE,
    MOONRAKER_LOG_NAME,
    MOONRAKER_SERVICE_TEMPLATE,
)
from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)


# noinspection PyMethodMayBeStatic
@dataclass
class Moonraker(BaseInstance):
    moonraker_dir: Path = MOONRAKER_DIR
    env_dir: Path = MOONRAKER_ENV_DIR
    cfg_file: Path | None = None
    port: int | None = None
    backup_dir: Path | None = None
    certs_dir: Path | None = None
    db_dir: Path | None = None

    def __init__(self, suffix: str = ""):
        super().__init__(suffix=suffix)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.log_file_name = MOONRAKER_LOG_NAME
        self.cfg_file = self.cfg_dir.joinpath(MOONRAKER_CFG_NAME)
        self.port = self._get_port()
        self.backup_dir = self.data_dir.joinpath("backup")
        self.certs_dir = self.data_dir.joinpath("certs")
        self.db_dir = self.data_dir.joinpath("database")

    def create(self, create_example_cfg: bool = False) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Moonraker Instance ...")

        try:
            self.create_folders([self.backup_dir, self.certs_dir, self.db_dir])
            create_service_file(
                name=self.service_file_path.name,
                content=self._prep_service_file_content(),
            )
            create_env_file(
                path=self.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME),
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
            self.user,
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
            self.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME).as_posix(),
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
            self.data_dir.as_posix(),
        )

        return env_file_content

    def _get_port(self) -> int | None:
        if not self.cfg_file or not self.cfg_file.is_file():
            return None

        scp = SimpleConfigParser()
        scp.read(self.cfg_file)
        port: int | None = scp.getint("server", "port", fallback=None)

        return port
