# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from core.constants import CURRENT_USER, SYSTEMD
from core.logger import Logger


@dataclass
class BaseInstance(ABC):
    suffix: str
    user: str = field(default=CURRENT_USER, init=False)
    service_file_path: Path | None = None
    is_legacy_instance: bool = False
    data_dir: Path | None = None
    data_dir_name: str = ""
    cfg_dir: Path | None = None
    sysd_dir: Path | None = None  # NOT to be confused with /etc/systemd/system
    comms_dir: Path | None = None
    gcodes_dir: Path | None = None
    log_dir: Path | None = None
    log_file_name: str = ""

    def __post_init__(self) -> None:
        self._set_data_dir()
        self._set_is_legacy_instance()
        self._set_service_file_path()
        if self.data_dir is not None:
            self.cfg_dir = self.data_dir.joinpath("config")
            self.log_dir = self.data_dir.joinpath("logs")
            self.comms_dir = self.data_dir.joinpath("comms")
            self.sysd_dir = self.data_dir.joinpath("systemd")
            self.gcodes_dir = self.data_dir.joinpath("gcodes")

    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu", "obico", "bambu", "companion"]

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError("Subclasses must implement the create method")

    def remove(self) -> None:
        from utils.fs_utils import run_remove_routines
        from utils.sys_utils import remove_system_service

        try:
            # remove the service file
            if self.service_file_path is not None:
                remove_system_service(self.service_file_path.name)

            # then remove all the log files
            if not self.log_file_name or not self.log_dir or not self.log_dir.exists():
                return

            files = self.log_dir.iterdir()
            logs = [f for f in files if f.name.startswith(self.log_file_name)]
            for log in logs:
                Logger.print_status(f"Remove '{log}'")
                run_remove_routines(log)

        except Exception as e:
            Logger.print_error(f"Error removing service: {e}")
            raise

    def create_folders(self, add_dirs: List[Path] | None = None) -> None:
        dirs: List[Path | None] = [
            self.data_dir,
            self.cfg_dir,
            self.log_dir,
            self.comms_dir,
            self.sysd_dir,
            self.gcodes_dir,
        ]

        if add_dirs:
            dirs.extend(add_dirs)

        for _dir in dirs:
            if _dir is None:
                continue
            _dir.mkdir(exist_ok=True)

    def remove_logfiles(self, log_name: str) -> None:
        from utils.fs_utils import run_remove_routines

        if not self.log_dir or not self.log_dir.exists():
            return

        files = self.log_dir.iterdir()
        logs = [f for f in files if f.name.startswith(log_name)]
        for log in logs:
            Logger.print_status(f"Remove '{log}'")
            run_remove_routines(log)

    def _set_data_dir(self) -> None:
        if self.suffix == "":
            self.data_dir = Path.home().joinpath("printer_data")
        else:
            self.data_dir = Path.home().joinpath(f"printer_{self.suffix}_data")

        if self.service_file_path is not None and self.service_file_path.exists():
            with open(self.service_file_path, "r") as service_file:
                service_content = service_file.read()
                pattern = re.compile("^EnvironmentFile=(.+)(/systemd/.+\.env)")
                match = re.search(pattern, service_content)
                if match:
                    self.data_dir = Path(match.group(1))

    def _set_service_file_path(self) -> None:
        from utils.common import convert_camelcase_to_kebabcase

        name: str = convert_camelcase_to_kebabcase(self.__class__.__name__)
        if self.suffix != "":
            name += f"-{self.suffix}"

        self.service_file_path = SYSTEMD.joinpath(f"{name}.service")

    def _set_is_legacy_instance(self) -> None:
        if (
            self.suffix != ""
            and not self.data_dir_name.startswith("printer_")
            and not self.data_dir_name.endswith("_data")
        ):
            self.is_legacy_instance = True
        else:
            self.is_legacy_instance = False
