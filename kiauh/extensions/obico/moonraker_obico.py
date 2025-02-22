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
from subprocess import CalledProcessError, run

from components.moonraker.moonraker import Moonraker
from core.constants import CURRENT_USER
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
from utils.fs_utils import create_folders
from utils.sys_utils import get_service_file_path


# noinspection PyMethodMayBeStatic
@dataclass(repr=True)
class MoonrakerObico:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    service_file_path: Path = field(init=False)
    log_file_name: str = OBICO_LOG_NAME
    dir: Path = OBICO_DIR
    env_dir: Path = OBICO_ENV_DIR
    data_dir: Path = field(init=False)
    cfg_file: Path = field(init=False)
    is_linked: bool = False

    def __post_init__(self):
        self.base: BaseInstance = BaseInstance(Moonraker, self.suffix)
        self.base.log_file_name = self.log_file_name

        self.service_file_path: Path = get_service_file_path(
            MoonrakerObico, self.suffix
        )
        self.data_dir: Path = self.base.data_dir
        self.cfg_file = self.base.cfg_dir.joinpath(OBICO_CFG_NAME)
        self.is_linked: bool = self._check_link_status()

    def create(self) -> None:
        from utils.sys_utils import create_env_file, create_service_file

        Logger.print_status("Creating new Obico for Klipper Instance ...")

        try:
            create_folders(self.base.base_folders)
            create_service_file(
                name=self.service_file_path.name,
                content=self._prep_service_file_content(),
            )
            create_env_file(
                path=self.base.sysd_dir.joinpath(OBICO_ENV_FILE_NAME),
                content=self._prep_env_file_content(),
            )

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def link(self) -> None:
        Logger.print_status(
            f"Linking instance for printer {self.data_dir.name} to the Obico server ..."
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
            CURRENT_USER,
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
            self.base.sysd_dir.joinpath(OBICO_ENV_FILE_NAME).as_posix(),
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
            f"{self.cfg_file}",
        )
        return env_file_content

    def _check_link_status(self) -> bool:
        if not self.cfg_file or not self.cfg_file.exists():
            return False

        scp = SimpleConfigParser()
        scp.read_file(self.cfg_file)
        return scp.getval("server", "auth_token", None) is not None
