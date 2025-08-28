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
from textwrap import dedent

from components.klipper.klipper import Klipper
from core.constants import CURRENT_USER
from core.instance_manager.base_instance import BaseInstance
from core.logger import Logger
from extensions.octoprint import (
    OP_BASEDIR_PREFIX,
    OP_ENV_PREFIX,
    OP_LOG_NAME,
)
from utils.fs_utils import create_folders
from utils.sys_utils import create_service_file, get_service_file_path


@dataclass
class Octoprint:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    service_file_path: Path = field(init=False)
    log_file_name = OP_LOG_NAME
    env_dir: Path = field(init=False)
    basedir: Path = field(init=False)
    cfg_file: Path = field(init=False)

    def __post_init__(self):
        self.base = BaseInstance(Klipper, self.suffix)
        self.base.log_file_name = self.log_file_name

        self.service_file_path = get_service_file_path(Octoprint, self.suffix)

        # OctoPrint stores its data under ~/.octoprint[_SUFFIX]
        self.basedir = (
            Path.home().joinpath(OP_BASEDIR_PREFIX)
            if self.suffix == ""
            else Path.home().joinpath(f"{OP_BASEDIR_PREFIX}_{self.suffix}")
        )
        self.cfg_file = self.basedir.joinpath("config.yaml")

        # OctoPrint virtualenv lives under ~/OctoPrint[_SUFFIX]
        self.env_dir = (
            Path.home().joinpath(OP_ENV_PREFIX)
            if self.suffix == ""
            else Path.home().joinpath(f"{OP_ENV_PREFIX}_{self.suffix}")
        )

    def create(self, port: int) -> None:
        Logger.print_status(
            f"Creating OctoPrint instance '{self.service_file_path.stem}' ..."
        )

        # Ensure basedir exists and config.yaml is present
        create_folders([self.basedir])
        if not self.cfg_file.exists():
            Logger.print_status("Creating config.yaml ...")
            self.cfg_file.write_text(self._prep_config_yaml())
            Logger.print_ok("config.yaml created!")
        else:
            Logger.print_info("config.yaml already exists. Skipped ...")

        create_service_file(self.service_file_path.name, self._prep_service_content(port))

    def _prep_service_content(self, port: int) -> str:
        basedir = self.basedir.as_posix()
        cfg = self.cfg_file.as_posix()
        octo_exec = self.env_dir.joinpath("bin/octoprint").as_posix()

        return dedent(
            f"""\
            [Unit]
            Description=Starts OctoPrint on startup
            After=network-online.target
            Wants=network-online.target

            [Service]
            Environment="LC_ALL=C.UTF-8"
            Environment="LANG=C.UTF-8"
            Type=simple
            User={CURRENT_USER}
            ExecStart={octo_exec} --basedir {basedir} --config {cfg} --port={port} serve

            [Install]
            WantedBy=multi-user.target
            """
        )

    def _prep_config_yaml(self) -> str:
        printer = self.base.comms_dir.joinpath("klippy.serial").as_posix()
        restart_service = self.service_file_path.stem

        return dedent(
            f"""\
            serial:
                additionalPorts:
                - {printer}
                disconnectOnErrors: false
                port: {printer}
            server:
                commands:
                    serverRestartCommand: sudo service {restart_service} restart
                    systemRestartCommand: sudo shutdown -r now
                    systemShutdownCommand: sudo shutdown -h now
            """
        )
