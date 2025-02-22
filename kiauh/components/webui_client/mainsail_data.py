# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
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
    BaseWebClient,
    BaseWebClientConfig,
    WebClientConfigType,
    WebClientType,
)
from core.backup_manager import BACKUP_ROOT_DIR
from core.constants import NGINX_SITES_AVAILABLE


@dataclass()
class MainsailConfigWeb(BaseWebClientConfig):
    client_config: WebClientConfigType = WebClientConfigType.MAINSAIL
    name: str = client_config.value
    display_name: str = name.title()
    config_dir: Path = Path.home().joinpath("mainsail-config")
    config_filename: str = "mainsail.cfg"
    config_section: str = f"include {config_filename}"
    backup_dir: Path = BACKUP_ROOT_DIR.joinpath("mainsail-config-backups")
    repo_url: str = "https://github.com/mainsail-crew/mainsail-config.git"


@dataclass()
class MainsailData(BaseWebClient):
    BASE_DL_URL: str = "https://github.com/mainsail-crew/mainsail/releases"

    client: WebClientType = WebClientType.MAINSAIL
    name: str = WebClientType.MAINSAIL.value
    display_name: str = name.capitalize()
    client_dir: Path = Path.home().joinpath("mainsail")
    config_file: Path = client_dir.joinpath("config.json")
    backup_dir: Path = BACKUP_ROOT_DIR.joinpath("mainsail-backups")
    repo_path: str = "mainsail-crew/mainsail"
    nginx_config: Path = NGINX_SITES_AVAILABLE.joinpath("mainsail")
    nginx_access_log: Path = Path("/var/log/nginx/mainsail-access.log")
    nginx_error_log: Path = Path("/var/log/nginx/mainsail-error.log")
    client_config: BaseWebClientConfig = None
    download_url: str | None = None

    def __post_init__(self):
        from components.webui_client.client_utils import get_download_url

        self.client_config = MainsailConfigWeb()
        self.download_url = get_download_url(self.BASE_DL_URL, self)
