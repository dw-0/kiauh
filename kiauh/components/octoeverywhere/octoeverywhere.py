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

from components.moonraker import MOONRAKER_CFG_NAME
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


@dataclass
class Octoeverywhere(BaseInstance):
    dir: Path = OE_DIR
    env_dir: Path = OE_ENV_DIR
    store_dir: Path = OE_STORE_DIR
    cfg_file: Path | None = None
    sys_cfg_file: Path | None = None
    log: Path | None = None

    def __init__(self, suffix: str = ""):
        super().__init__(suffix=suffix)

    def __post_init__(self):
        super().__post_init__()
        self.cfg_file = self.cfg_dir.joinpath(OE_CFG_NAME)
        self.sys_cfg_file = self.cfg_dir.joinpath(OE_SYS_CFG_NAME)
        self.log = self.log_dir.joinpath(OE_LOG_NAME)

    def create(self) -> None:
        Logger.print_status("Creating OctoEverywhere for Klipper Instance ...")

        try:
            cmd = f"{OE_INSTALL_SCRIPT} {self.cfg_dir}/{MOONRAKER_CFG_NAME}"
            run(cmd, check=True, shell=True)

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise

    @staticmethod
    def update() -> None:
        try:
            run(OE_UPDATE_SCRIPT.as_posix(), check=True, shell=True, cwd=OE_DIR)

        except CalledProcessError as e:
            Logger.print_error(f"Error updating OctoEverywhere for Klipper: {e}")
            raise

    def delete(self) -> None:
        service_file: str = self.get_service_file_name(extension=True)
        service_file_path: Path = self.get_service_file_path()

        Logger.print_status(
            f"Deleting OctoEverywhere for Klipper Instance: {service_file}"
        )

        try:
            command = ["sudo", "rm", "-f", service_file_path.as_posix()]
            run(command, check=True)
            self.delete_logfiles(OE_LOG_NAME)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise
