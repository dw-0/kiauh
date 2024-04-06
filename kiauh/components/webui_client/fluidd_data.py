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

from components.webui_client.base_data import (
    BaseWebClientConfig,
    WebClientConfigType,
    WebClientType,
    BaseWebClient,
)
from core.backup_manager import BACKUP_ROOT_DIR
from utils.git_utils import get_latest_unstable_tag


@dataclass(frozen=True)
class FluiddConfigWeb(BaseWebClientConfig):
    client_config: WebClientConfigType = WebClientConfigType.FLUIDD
    name: str = client_config.value
    display_name: str = name.title()
    config_dir: Path = Path.home().joinpath("fluidd-config")
    config_filename: str = "fluidd.cfg"
    config_section: str = f"include {config_filename}"
    backup_dir: Path = BACKUP_ROOT_DIR.joinpath("fluidd-config-backups")
    repo_url: str = "https://github.com/fluidd-core/fluidd-config.git"


@dataclass(frozen=True)
class FluiddData(BaseWebClient):
    BASE_DL_URL = "https://github.com/fluidd-core/fluidd/releases"

    client: WebClientType = WebClientType.FLUIDD
    name: str = client.value
    display_name: str = name.capitalize()
    client_dir: Path = Path.home().joinpath("fluidd")
    backup_dir: Path = BACKUP_ROOT_DIR.joinpath("fluidd-backups")
    repo_path: str = "fluidd-core/fluidd"

    @property
    def stable_url(self) -> str:
        return f"{self.BASE_DL_URL}/latest/download/fluidd.zip"

    @property
    def unstable_url(self) -> str:
        try:
            unstable_tag = get_latest_unstable_tag(self.repo_path)
            if unstable_tag != "":
                return f"{self.BASE_DL_URL}/download/{unstable_tag}/fluidd.zip"
            else:
                raise Exception
        except Exception:
            return self.stable_url

    @property
    def client_config(self) -> BaseWebClientConfig:
        return FluiddConfigWeb()
