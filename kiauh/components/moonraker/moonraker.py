# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from components.moonraker import MODULE_PATH, MOONRAKER_DIR, MOONRAKER_ENV_DIR
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
        self.cfg_file = self.cfg_dir.joinpath("moonraker.conf")
        self.port = self._get_port()
        self.backup_dir = self.data_dir.joinpath("backup")
        self.certs_dir = self.data_dir.joinpath("certs")
        self._db_dir = self.data_dir.joinpath("database")
        self._comms_dir = self.data_dir.joinpath("comms")
        self.log = self.log_dir.joinpath("moonraker.log")

    @property
    def db_dir(self) -> Path:
        return self._db_dir

    @property
    def comms_dir(self) -> Path:
        return self._comms_dir

    def create(self, create_example_cfg: bool = False) -> None:
        Logger.print_status("Creating new Moonraker Instance ...")
        service_template_path = MODULE_PATH.joinpath("assets/moonraker.service")
        env_template_file_path = MODULE_PATH.joinpath("assets/moonraker.env")
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = SYSTEMD.joinpath(service_file_name)
        env_file_target = self.sysd_dir.joinpath("moonraker.env")

        try:
            self.create_folders([self.backup_dir, self.certs_dir, self._db_dir])
            self.write_service_file(
                service_template_path, service_file_target, env_file_target
            )
            self.write_env_file(env_template_file_path, env_file_target)

        except subprocess.CalledProcessError as e:
            Logger.print_error(
                f"Error creating service file {service_file_target}: {e}"
            )
            raise
        except OSError as e:
            Logger.print_error(f"Error writing file: {e}")
            raise

    def delete(self) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(f"Deleting Moonraker Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            subprocess.run(command, check=True)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except subprocess.CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise

    def write_service_file(
        self,
        service_template_path: Path,
        service_file_target: Path,
        env_file_target: Path,
    ) -> None:
        service_content = self._prep_service_file(
            service_template_path, env_file_target
        )
        command = ["sudo", "tee", service_file_target]
        subprocess.run(
            command,
            input=service_content.encode(),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {service_file_target}")

    def write_env_file(
        self, env_template_file_path: Path, env_file_target: Path
    ) -> None:
        env_file_content = self._prep_env_file(env_template_file_path)
        with open(env_file_target, "w") as env_file:
            env_file.write(env_file_content)
        Logger.print_ok(f"Env file created: {env_file_target}")

    def _prep_service_file(
        self, service_template_path: Path, env_file_path: Path
    ) -> str:
        try:
            with open(service_template_path, "r") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {service_template_path} - File not found"
            )
            raise
        service_content = template_content.replace("%USER%", self.user)
        service_content = service_content.replace(
            "%MOONRAKER_DIR%", str(self.moonraker_dir)
        )
        service_content = service_content.replace("%ENV%", str(self.env_dir))
        service_content = service_content.replace("%ENV_FILE%", str(env_file_path))
        return service_content

    def _prep_env_file(self, env_template_file_path: Path) -> str:
        try:
            with open(env_template_file_path, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {env_template_file_path} - File not found"
            )
            raise
        env_file_content = env_template_file_content.replace(
            "%MOONRAKER_DIR%", str(self.moonraker_dir)
        )
        env_file_content = env_file_content.replace(
            "%PRINTER_DATA%", str(self.data_dir)
        )
        return env_file_content

    def _get_port(self) -> int | None:
        if not self.cfg_file.is_file():
            return None

        scp = SimpleConfigParser()
        scp.read(self.cfg_file)
        port = scp.getint("server", "port", fallback=None)

        return port
