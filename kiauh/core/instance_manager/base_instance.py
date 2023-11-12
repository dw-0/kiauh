#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Union, Optional, Type, TypeVar

from kiauh.utils.constants import SYSTEMD, CURRENT_USER

B = TypeVar(name="B", bound="BaseInstance", covariant=True)


class BaseInstance(ABC):
    @classmethod
    def blacklist(cls) -> List[str]:
        return []

    def __init__(
        self,
        suffix: Optional[str],
        instance_type: B = B,
    ):
        self._instance_type = instance_type
        self._suffix = suffix
        self._user = CURRENT_USER
        self._data_dir_name = self.get_data_dir_from_suffix()
        self._data_dir = f"{Path.home()}/{self._data_dir_name}_data"
        self._cfg_dir = f"{self.data_dir}/config"
        self._log_dir = f"{self.data_dir}/logs"
        self._comms_dir = f"{self.data_dir}/comms"
        self._sysd_dir = f"{self.data_dir}/systemd"

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
    def suffix(self, value: Union[str, None]) -> None:
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
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: str):
        self._data_dir = value

    @property
    def cfg_dir(self):
        return self._cfg_dir

    @cfg_dir.setter
    def cfg_dir(self, value: str):
        self._cfg_dir = value

    @property
    def log_dir(self):
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value: str):
        self._log_dir = value

    @property
    def comms_dir(self):
        return self._comms_dir

    @comms_dir.setter
    def comms_dir(self, value: str):
        self._comms_dir = value

    @property
    def sysd_dir(self):
        return self._sysd_dir

    @sysd_dir.setter
    def sysd_dir(self, value: str):
        self._sysd_dir = value

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError("Subclasses must implement the create method")

    @abstractmethod
    def delete(self, del_remnants: bool) -> None:
        raise NotImplementedError("Subclasses must implement the delete method")

    def get_service_file_name(self, extension: bool = False) -> str:
        name = f"{self.__class__.__name__.lower()}"
        if self.suffix is not None:
            name += f"-{self.suffix}"

        return name if not extension else f"{name}.service"

    def get_service_file_path(self) -> str:
        return f"{SYSTEMD}/{self.get_service_file_name(extension=True)}"

    def get_data_dir_from_suffix(self) -> str:
        if self._suffix is None:
            return "printer"
        elif self._suffix.isdigit():
            return f"printer_{self._suffix}"
        else:
            return self._suffix
