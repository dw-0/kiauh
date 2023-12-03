#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
from pathlib import Path

from kiauh.utils.common import get_current_date
from kiauh.utils.constants import KIAUH_BACKUP_DIR
from kiauh.utils.logger import Logger


# noinspection PyMethodMayBeStatic
class BackupManager:
    def __init__(
        self, backup_name: str, source: Path, backup_dir: Path = KIAUH_BACKUP_DIR
    ):
        self._backup_name = backup_name
        self._source = source
        self._backup_dir = backup_dir

    @property
    def backup_name(self) -> str:
        return self._backup_name

    @backup_name.setter
    def backup_name(self, value: str):
        self._backup_name = value

    @property
    def source(self) -> Path:
        return self._source

    @source.setter
    def source(self, value: Path):
        self._source = value

    @property
    def backup_dir(self) -> Path:
        return self._backup_dir

    @backup_dir.setter
    def backup_dir(self, value: Path):
        self._backup_dir = value

    def backup(self) -> None:
        if self._source is None or not Path(self._source).exists():
            raise OSError

        try:
            log = f"Creating backup of {self.backup_name} in {self.backup_dir} ..."
            Logger.print_status(log)
            date = get_current_date()
            dest = Path(
                f"{self.backup_dir}/{self.backup_name}/{date.get('date')}-{date.get('time')}"
            )
            shutil.copytree(src=self.source, dst=dest)
        except OSError as e:
            Logger.print_error(f"Unable to backup source directory. Not exist.\n{e}")
            return

        Logger.print_ok("Backup successfull!")
