#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Type, TypeVar

from utils.constants import SYSTEMD, CURRENT_USER

B = TypeVar(name="B", bound="BaseInstance", covariant=True)


class BaseInstance(ABC):
    @classmethod
    def blacklist(cls) -> List[str]:
        return []

    def __init__(
        self,
        suffix: str,
        instance_type: B = B,
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
    def instance_type(self) -> Type["BaseInstance"]:
        return self._instance_type

    @instance_type.setter
    def instance_type(self, value: Type["BaseInstance"]) -> None:
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
    def data_dir(self, value: str) -> None:
        self._data_dir = value

    @property
    def cfg_dir(self) -> Path:
        return self._cfg_dir

    @cfg_dir.setter
    def cfg_dir(self, value: str) -> None:
        self._cfg_dir = value

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value: str) -> None:
        self._log_dir = value

    @property
    def comms_dir(self) -> Path:
        return self._comms_dir

    @comms_dir.setter
    def comms_dir(self, value: str) -> None:
        self._comms_dir = value

    @property
    def sysd_dir(self) -> Path:
        return self._sysd_dir

    @sysd_dir.setter
    def sysd_dir(self, value: str) -> None:
        self._sysd_dir = value

    @property
    def gcodes_dir(self) -> Path:
        return self._gcodes_dir

    @gcodes_dir.setter
    def gcodes_dir(self, value: str) -> None:
        self._gcodes_dir = value

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError("Subclasses must implement the create method")

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError("Subclasses must implement the delete method")

    def create_folders(self, add_dirs: List[Path] = None) -> None:
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
        name = f"{self.__class__.__name__.lower()}"
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
