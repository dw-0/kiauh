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
from typing import List, Optional


class BaseInstance(ABC):
    @classmethod
    def blacklist(cls) -> List[str]:
        return []

    def __init__(
        self,
        prefix: Optional[str],
        name: Optional[str],
        user: Optional[str],
        data_dir_name: Optional[str],
    ):
        self._prefix = prefix
        self._name = name
        self._user = user
        self._data_dir_name = data_dir_name
        self.data_dir = f"{Path.home()}/{self._data_dir_name}_data"
        self.cfg_dir = f"{self.data_dir}/config"
        self.log_dir = f"{self.data_dir}/logs"
        self.comms_dir = f"{self.data_dir}/comms"
        self.sysd_dir = f"{self.data_dir}/systemd"

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value) -> None:
        self._prefix = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value) -> None:
        self._name = value

    @property
    def user(self) -> str:
        return self._user

    @user.setter
    def user(self, value) -> None:
        self._user = value

    @property
    def data_dir_name(self) -> str:
        return self._data_dir_name

    @data_dir_name.setter
    def data_dir_name(self, value) -> None:
        self._data_dir_name = value

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError("Subclasses must implement the create method")

    @abstractmethod
    def delete(self, del_remnants: bool) -> None:
        raise NotImplementedError("Subclasses must implement the delete method")

    @abstractmethod
    def get_service_file_name(self) -> str:
        raise NotImplementedError(
            "Subclasses must implement the get_service_file_name method"
        )
