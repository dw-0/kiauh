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

from components.moonraker import MOONRAKER_CFG_NAME
from components.moonraker.moonraker import Moonraker
from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from extensions.octoapp import (
    OA_CFG_NAME,
    OA_DIR,
    OA_ENV_DIR,
    OA_INSTALL_SCRIPT,
    OA_LOG_NAME,
    OA_SYS_CFG_NAME,
    OA_UPDATE_SCRIPT,
)
from utils.sys_utils import get_service_file_path


@dataclass
class Octoapp:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    service_file_path: Path = field(init=False)
    log_file_name = OA_LOG_NAME
    dir: Path = OA_DIR
    env_dir: Path = OA_ENV_DIR
    data_dir: Path = field(init=False)
    store_dir: Path = field(init=False)
    cfg_file: Path = field(init=False)
    sys_cfg_file: Path = field(init=False)

    def __post_init__(self):
        self.base: BaseInstance = BaseInstance(Moonraker, self.suffix)
        self.base.log_file_name = self.log_file_name

        self.service_file_path: Path = get_service_file_path(Octoapp, self.suffix)
        self.store_dir = self.base.data_dir.joinpath("store")
        self.cfg_file = self.base.cfg_dir.joinpath(OA_CFG_NAME)
        self.sys_cfg_file = self.base.cfg_dir.joinpath(OA_SYS_CFG_NAME)
        self.data_dir = self.base.data_dir
        self.sys_cfg_file = self.base.cfg_dir.joinpath(OA_SYS_CFG_NAME)

    def create(self) -> None:
        Logger.print_status("Creating OctoApp for Klipper Instance ...")

        try:
            cmd = f"{OA_INSTALL_SCRIPT} {self.base.cfg_dir}/{MOONRAKER_CFG_NAME}"
            run(cmd, check=True, shell=True)

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise

    @staticmethod
    def update() -> None:
        try:
            run(OA_UPDATE_SCRIPT.as_posix(), check=True, shell=True, cwd=OA_DIR)

        except CalledProcessError as e:
            Logger.print_error(f"Error updating OctoApp for Klipper: {e}")
            raise
