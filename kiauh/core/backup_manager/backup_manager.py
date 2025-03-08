# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from core.backup_manager import BACKUP_ROOT_DIR
from core.logger import Logger
from utils.common import get_current_date


class BackupManagerException(Exception):
    pass


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BackupManager:
    def __init__(self, backup_root_dir: Path = BACKUP_ROOT_DIR):
        self._backup_root_dir: Path = backup_root_dir
        self._ignore_folders: List[str] = []

    @property
    def backup_root_dir(self) -> Path:
        return self._backup_root_dir

    @backup_root_dir.setter
    def backup_root_dir(self, value: Path):
        self._backup_root_dir = value

    @property
    def ignore_folders(self) -> List[str]:
        return self._ignore_folders

    @ignore_folders.setter
    def ignore_folders(self, value: List[str]):
        self._ignore_folders = value

    def backup_file(
        self, file: Path, target: Path | None = None, custom_filename=None
    ) -> bool:
        Logger.print_status(f"Creating backup of {file} ...")

        if not file.exists():
            Logger.print_info("File does not exist! Skipping ...")
            return False

        target = self.backup_root_dir if target is None else target

        if Path(file).is_file():
            date = get_current_date().get("date")
            time = get_current_date().get("time")
            filename = f"{file.stem}-{date}-{time}{file.suffix}"
            filename = custom_filename if custom_filename is not None else filename
            try:
                Path(target).mkdir(exist_ok=True)
                shutil.copyfile(file, target.joinpath(filename))
                Logger.print_ok("Backup successful!")
                return True
            except OSError as e:
                Logger.print_error(f"Unable to backup '{file}':\n{e}")
                return False
        else:
            Logger.print_info(f"File '{file}' not found ...")
            return False

    def backup_directory(
        self, name: str, source: Path, target: Path | None = None
    ) -> Path | None:
        Logger.print_status(f"Creating backup of {name} in {target} ...")

        if source is None or not Path(source).exists():
            Logger.print_info("Source directory does not exist! Skipping ...")
            return None

        target = self.backup_root_dir if target is None else target
        try:
            date = get_current_date().get("date")
            time = get_current_date().get("time")
            backup_target = target.joinpath(f"{name.lower()}-{date}-{time}")
            shutil.copytree(
                source,
                backup_target,
                ignore=self.ignore_folders_func,
                ignore_dangling_symlinks=True,
            )
            Logger.print_ok("Backup successful!")

            return backup_target

        except OSError as e:
            Logger.print_error(f"Unable to backup directory '{source}':\n{e}")
            raise BackupManagerException(f"Unable to backup directory '{source}':\n{e}")

    def ignore_folders_func(self, dirpath, filenames) -> List[str]:
        return (
            [f for f in filenames if f in self._ignore_folders]
            if self._ignore_folders
            else []
        )
