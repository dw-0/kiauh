# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class WebClientType(Enum):
    MAINSAIL: str = "mainsail"
    FLUIDD: str = "fluidd"


class WebClientConfigType(Enum):
    MAINSAIL: str = "mainsail-config"
    FLUIDD: str = "fluidd-config"


@dataclass()
class BaseWebClient(ABC):
    """Base class for webclient data"""

    client: WebClientType
    name: str
    display_name: str
    client_dir: Path
    config_file: Path
    backup_dir: Path
    repo_path: str
    download_url: str
    nginx_config: Path
    nginx_access_log: Path
    nginx_error_log: Path
    client_config: BaseWebClientConfig


@dataclass()
class BaseWebClientConfig(ABC):
    """Base class for webclient config data"""

    client_config: WebClientConfigType
    name: str
    display_name: str
    config_filename: str
    config_dir: Path
    backup_dir: Path
    repo_url: str
    config_section: str
