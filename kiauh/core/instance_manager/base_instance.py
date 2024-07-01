# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from utils.constants import CURRENT_USER, SYSTEMD
from utils.logger import Logger


class BaseInstance(ABC):
    @classmethod
    def blacklist(cls) -> List[str]:
        return []

    def __init__(
        self,
        suffix: str,
        instance_type: BaseInstance,
    ):
        self._instance_type = instance_type
        self._suffix = suffix
        self._user = CURRENT_USER
        self._data_dir_name = self.get_data_dir_name_from_suffix()
        self._data_dir = Path.home().joinpath(f"{self._data_dir_name}_data")
        self._cfg_dir = self.data_dir.joinpath("config")
        self._log_dir = self.data_dir.joinpath("logs")
        self._comms_dir = self.data_dir.joinpath("comms")
        self._sysd_dir = self.data_dir.joinpath("systemd")
        self._gcodes_dir = self.data_dir.joinpath("gcodes")

    @property
    def instance_type(self) -> BaseInstance:
        return self._instance_type

    @instance_type.setter
    def instance_type(self, value: BaseInstance) -> None:
        self._instance_type = value

    @property
    def suffix(self) -> str:
        return self._suffix

    @suffix.setter
    def suffix(self, value: str) -> None:
        self._suffix = value

    @property
    def user(self) -> str:
        return self._user

    @user.setter
    def user(self, value: str) -> None:
        self._user = value

    @property
    def data_dir_name(self) -> str:
        return self._data_dir_name

    @data_dir_name.setter
    def data_dir_name(self, value: str) -> None:
        self._data_dir_name = value

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: Path) -> None:
        self._data_dir = value

    @property
    def cfg_dir(self) -> Path:
        return self._cfg_dir

    @cfg_dir.setter
    def cfg_dir(self, value: Path) -> None:
        self._cfg_dir = value

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value: Path) -> None:
        self._log_dir = value

    @property
    def comms_dir(self) -> Path:
        return self._comms_dir

    @comms_dir.setter
    def comms_dir(self, value: Path) -> None:
        self._comms_dir = value

    @property
    def sysd_dir(self) -> Path:
        return self._sysd_dir

    @sysd_dir.setter
    def sysd_dir(self, value: Path) -> None:
        self._sysd_dir = value

    @property
    def gcodes_dir(self) -> Path:
        return self._gcodes_dir

    @gcodes_dir.setter
    def gcodes_dir(self, value: Path) -> None:
        self._gcodes_dir = value

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError("Subclasses must implement the create method")

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError("Subclasses must implement the delete method")

    def create_folders(self, add_dirs: Optional[List[Path]] = None) -> None:
        dirs = [
            self.data_dir,
            self.cfg_dir,
            self.log_dir,
            self.comms_dir,
            self.sysd_dir,
        ]

        if add_dirs:
            dirs.extend(add_dirs)

        for _dir in dirs:
            _dir.mkdir(exist_ok=True)

    def get_service_file_name(self, extension: bool = False) -> str:
        from utils.common import convert_camelcase_to_kebabcase

        name = convert_camelcase_to_kebabcase(self.__class__.__name__)
        if self.suffix != "":
            name += f"-{self.suffix}"

        return name if not extension else f"{name}.service"

    def get_service_file_path(self) -> Path:
        return SYSTEMD.joinpath(self.get_service_file_name(extension=True))

    def get_data_dir_name_from_suffix(self) -> str:
        if self._suffix == "":
            return "printer"
        elif self._suffix.isdigit():
            return f"printer_{self._suffix}"
        else:
            return self._suffix

    def delete_logfiles(self, log_name: str) -> None:
        from utils.fs_utils import run_remove_routines

        files = self.log_dir.iterdir()
        logs = [f for f in files if f.name.startswith(log_name)]
        for log in logs:
            Logger.print_status(f"Remove '{log}'")
            run_remove_routines(log)
