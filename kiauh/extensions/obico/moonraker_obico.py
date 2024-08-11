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
from subprocess import CalledProcessError, run

from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.obico import (
    OBICO_CFG_NAME,
    OBICO_DIR,
    OBICO_ENV_DIR,
    OBICO_ENV_FILE_NAME,
    OBICO_ENV_FILE_TEMPLATE,
    OBICO_LINK_SCRIPT,
    OBICO_LOG_NAME,
    OBICO_SERVICE_TEMPLATE,
)


# noinspection PyMethodMayBeStatic
@dataclass
class MoonrakerObico(BaseInstance):
    dir: Path = OBICO_DIR
    env_dir: Path = OBICO_ENV_DIR
    cfg_file: Path | None = None
    log: Path | None = None
    is_linked: bool = False

    def __init__(self, suffix: str = ""):
        super().__init__(suffix=suffix)

    def __post_init__(self):
        super().__post_init__()
        self.cfg_file = self.cfg_dir.joinpath(OBICO_CFG_NAME)
        self.log = self.log_dir.joinpath(OBICO_LOG_NAME)
        self.is_linked: bool = self._check_link_status()

    def create(self) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Obico for Klipper Instance ...")

        try:
            self.create_folders()
            create_service_file(
                name=self.get_service_file_name(extension=True),
                content=self._prep_service_file_content(),
            )
            create_env_file(
                path=self.sysd_dir.joinpath(OBICO_ENV_FILE_NAME),
                content=self._prep_env_file_content(),
            )

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def delete(self) -> None:
        service_file: str = self.get_service_file_name(extension=True)
        service_file_path: Path = self.get_service_file_path()

        Logger.print_status(f"Deleting Obico for Klipper Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path.as_posix()]
            run(command, check=True)
            self.delete_logfiles(OBICO_LOG_NAME)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise

    def link(self) -> None:
        Logger.print_status(
            f"Linking instance for printer {self.data_dir_name} to the Obico server ..."
        )
        try:
            cmd = [f"{OBICO_LINK_SCRIPT} -q -c {self.cfg_file}"]
            if self.suffix:
                cmd.append(f"-n {self.suffix}")
            run(cmd, check=True, shell=True)
        except CalledProcessError as e:
            Logger.print_error(f"Error during Obico linking: {e}")
            raise

    def _prep_service_file_content(self) -> str:
        template = OBICO_SERVICE_TEMPLATE

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
            "%OBICO_DIR%",
            self.dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV%",
            self.env_dir.as_posix(),
        )
        service_content = service_content.replace(
            "%ENV_FILE%",
            self.sysd_dir.joinpath(OBICO_ENV_FILE_NAME).as_posix(),
        )
        return service_content

    def _prep_env_file_content(self) -> str:
        template = OBICO_ENV_FILE_TEMPLATE

        try:
            with open(template, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(f"Unable to open {template} - File not found")
            raise
        env_file_content = env_template_file_content.replace(
            "%CFG%",
            f"{self.cfg_dir}/{self.cfg_file}",
        )
        return env_file_content

    def _check_link_status(self) -> bool:
        if not self.cfg_file or not self.cfg_file.exists():
            return False

        scp = SimpleConfigParser()
        scp.read(self.cfg_file)
        return scp.get("server", "auth_token", None) is not None
