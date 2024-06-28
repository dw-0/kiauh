# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List

from components.octoeverywhere import (
    OE_CFG_NAME,
    OE_DIR,
    OE_ENV_DIR,
    OE_INSTALL_SCRIPT,
    OE_LOG_NAME,
    OE_STORE_DIR,
    OE_SYS_CFG_NAME,
    OE_UPDATE_SCRIPT,
)
from core.instance_manager.base_instance import BaseInstance
from utils.logger import Logger


class Octoeverywhere(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu", "bambu", "companion"]

    def __init__(self, suffix: str = ""):
        super().__init__(instance_type=self, suffix=suffix)
        self.dir: Path = OE_DIR
        self.env_dir: Path = OE_ENV_DIR
        self.store_dir: Path = OE_STORE_DIR
        self._cfg_file = self.cfg_dir.joinpath(OE_CFG_NAME)
        self._sys_cfg_file = self.cfg_dir.joinpath(OE_SYS_CFG_NAME)
        self._log = self.log_dir.joinpath(OE_LOG_NAME)

    @property
    def cfg_file(self) -> Path:
        return self._cfg_file

    @property
    def sys_cfg_file(self) -> Path:
        return self._sys_cfg_file

    @property
    def log(self) -> Path:
        return self._log

    def create(self) -> None:
        Logger.print_status("Creating OctoEverywhere for Klipper Instance ...")

        try:
            cmd = f"{OE_INSTALL_SCRIPT} {self.cfg_dir}/moonraker.conf"
            run(cmd, check=True, shell=True)

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise

    @staticmethod
    def update():
        try:
            run(str(OE_UPDATE_SCRIPT), check=True, shell=True, cwd=OE_DIR)

        except CalledProcessError as e:
            Logger.print_error(f"Error updating OctoEverywhere for Klipper: {e}")
            raise

    def delete(self) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(
            f"Deleting OctoEverywhere for Klipper Instance: {service_file}"
        )

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            run(command, check=True)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise
