#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from typing import Literal, TypedDict, Set

from core.backup_manager import BACKUP_ROOT_DIR

MODULE_PATH = Path(__file__).resolve().parent

###########
# MAINSAIL
###########
MAINSAIL_DIR = Path.home().joinpath("mainsail")
MAINSAIL_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("mainsail-backups")
MAINSAIL_CONFIG_DIR = Path.home().joinpath("mainsail-config")
MAINSAIL_CONFIG_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("mainsail-config-backups")
MAINSAIL_CONFIG_REPO_URL = "https://github.com/mainsail-crew/mainsail-config.git"
MAINSAIL_CONFIG_JSON = MAINSAIL_DIR.joinpath("config.json")
MAINSAIL_URL = (
    "https://github.com/mainsail-crew/mainsail/releases/latest/download/mainsail.zip"
)
MAINSAIL_PRE_RLS_URL = (
    "https://github.com/mainsail-crew/mainsail/releases/download/%TAG%/mainsail.zip"
)
MAINSAIL_TAGS_URL = "https://api.github.com/repos/mainsail-crew/mainsail/tags"

#########
# FLUIDD
#########
FLUIDD_DIR = Path.home().joinpath("fluidd")
FLUIDD_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("fluidd-backups")
FLUIDD_CONFIG_DIR = Path.home().joinpath("fluidd-config")
FLUIDD_CONFIG_BACKUP_DIR = BACKUP_ROOT_DIR.joinpath("fluidd-config-backups")
FLUIDD_CONFIG_REPO_URL = "https://github.com/fluidd-core/fluidd-config.git"
FLUIDD_URL = "https://github.com/fluidd-core/fluidd/releases/latest/download/fluidd.zip"
FLUIDD_PRE_RLS_URL = (
    "https://github.com/fluidd-core/fluidd/releases/download/%TAG%/fluidd.zip"
)
FLUIDD_TAGS_URL = "https://api.github.com/repos/fluidd-core/fluidd/tags"

ClientName = Literal["mainsail", "fluidd"]
ClientConfigName = Literal["mainsail-config", "fluidd-config"]


class ClientData(TypedDict):
    name: ClientName
    display_name: str
    dir: Path
    backup_dir: Path
    url: str
    pre_release_url: str
    tags_url: str
    remote_mode: bool  # required only for Mainsail
    mr_conf_repo: str
    mr_conf_path: str
    client_config: "ClientConfigData"


class ClientConfigData(TypedDict):
    name: ClientConfigName
    display_name: str
    cfg_filename: str
    dir: Path
    backup_dir: Path
    url: str
    printer_cfg_section: str
    mr_conf_path: str
    mr_conf_origin: str
