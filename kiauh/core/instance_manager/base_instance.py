# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from utils.fs_utils import get_data_dir

SUFFIX_BLACKLIST: List[str] = ["None", "mcu", "obico", "bambu", "companion"]


@dataclass(repr=True)
class BaseInstance:
    instance_type: type
    suffix: str
    log_file_name: str | None = None
    data_dir: Path = field(init=False)
    base_folders: List[Path] = field(init=False)
    cfg_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    gcodes_dir: Path = field(init=False)
    comms_dir: Path = field(init=False)
    sysd_dir: Path = field(init=False)
    is_legacy_instance: bool = field(init=False)

    def __post_init__(self):
        self.data_dir = get_data_dir(self.instance_type, self.suffix)
        # the following attributes require the data_dir to be set
        self.cfg_dir = self.data_dir.joinpath("config")
        self.log_dir = self.data_dir.joinpath("logs")
        self.gcodes_dir = self.data_dir.joinpath("gcodes")
        self.comms_dir = self.data_dir.joinpath("comms")
        self.sysd_dir = self.data_dir.joinpath("systemd")
        self.is_legacy_instance = self._set_is_legacy_instance()
        self.base_folders = [
            self.data_dir,
            self.cfg_dir,
            self.log_dir,
            self.gcodes_dir,
            self.comms_dir,
            self.sysd_dir,
        ]

    def _set_is_legacy_instance(self) -> bool:
        legacy_pattern = r"^(?!printer)(.+)_data"
        match = re.search(legacy_pattern, self.data_dir.name)

        return True if (match and self.suffix != "") else False
