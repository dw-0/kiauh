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
from enum import Enum
from pathlib import Path


class WebClientType(Enum):
    MAINSAIL: str = "mainsail"
    FLUIDD: str = "fluidd"


class WebClientConfigType(Enum):
    MAINSAIL: str = "mainsail-config"
    FLUIDD: str = "fluidd-config"


class BaseWebClient(ABC):
    """Base class for webclient data"""

    @property
    @abstractmethod
    def client(self) -> WebClientType:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def client_dir(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def backup_dir(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def repo_path(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def stable_url(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def unstable_url(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def client_config(self) -> BaseWebClientConfig:
        raise NotImplementedError


class BaseWebClientConfig(ABC):
    """Base class for webclient config data"""

    @property
    @abstractmethod
    def client_config(self) -> WebClientConfigType:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def display_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def config_filename(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def config_dir(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def backup_dir(self) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def repo_url(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def config_section(self) -> str:
        raise NotImplementedError
