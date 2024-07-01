# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run
from typing import List

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
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from utils.constants import SYSTEMD
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class Moonraker(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu", "obico"]

    def __init__(self, suffix: str = ""):
        super().__init__(instance_type=self, suffix=suffix)
        self.moonraker_dir: Path = MOONRAKER_DIR
        self.env_dir: Path = MOONRAKER_ENV_DIR
        self.cfg_file = self.cfg_dir.joinpath(MOONRAKER_CFG_NAME)
        self.port = self._get_port()
        self.backup_dir = self.data_dir.joinpath("backup")
        self.certs_dir = self.data_dir.joinpath("certs")
        self._db_dir = self.data_dir.joinpath("database")
        self._comms_dir = self.data_dir.joinpath("comms")
        self.log = self.log_dir.joinpath(MOONRAKER_LOG_NAME)

    @property
    def db_dir(self) -> Path:
        return self._db_dir

    @property
    def comms_dir(self) -> Path:
        return self._comms_dir

    def create(self, create_example_cfg: bool = False) -> None:
        Logger.print_status("Creating new Moonraker Instance ...")

        try:
            self.create_folders([self.backup_dir, self.certs_dir, self._db_dir])
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

        Logger.print_status(f"Removing Moonraker Instance: {service_file}")

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
        env_file_target = self.sysd_dir.joinpath(MOONRAKER_ENV_FILE_NAME)

        with open(env_file_target, "w") as env_file:
            env_file.write(env_file_content)
        Logger.print_ok(f"Env file created: {env_file_target}")

    def _prep_service_file(self) -> str:
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

    def _prep_env_file(self) -> str:
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
        if not self.cfg_file.is_file():
            return None

        scp = SimpleConfigParser()
        scp.read(self.cfg_file)
        port = scp.getint("server", "port", fallback=None)

        return port

    def _delete_logfiles(self) -> None:
        from utils.fs_utils import run_remove_routines

        files = self.log_dir.iterdir()
        logs = [f for f in files if f.name.startswith(MOONRAKER_LOG_NAME)]
        for log in logs:
            Logger.print_status(f"Remove '{log}'")
            run_remove_routines(log)
