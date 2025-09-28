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
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.logger import Logger


class BackupService:
    def __init__(self):
        self._backup_root = Path.home().joinpath("kiauh_backups")

    @property
    def backup_root(self) -> Path:
        return self._backup_root

    def backup_file(
        self,
        source_path: Path,
        target_path: Optional[Path | str] = None,
        target_name: Optional[str] = None,
    ) -> bool:
        source_path = Path(source_path)

        Logger.print_status(f"Creating backup of {source_path} ...")

        if not source_path.exists():
            Logger.print_info(
                f"File '{source_path}' does not exist! Skipping backup..."
            )
            return False

        if not source_path.is_file():
            Logger.print_info(f"'{source_path}' is not a file! Skipping backup...")
            return False

        try:
            self._backup_root.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = (
                target_name or f"{source_path.stem}_{timestamp}{source_path.suffix}"
            )
            if target_path is not None:
                backup_path = self._backup_root.joinpath(target_path, filename)
            else:
                backup_path = self._backup_root.joinpath(filename)

            backup_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_path)

            Logger.print_ok(
                f"Successfully backed up '{source_path}' to '{backup_path}'"
            )
            return True

        except Exception as e:
            Logger.print_error(f"Failed to backup '{source_path}': {e}")
            return False

    def backup_directory(
        self,
        source_path: Path,
        backup_name: str,
        target_path: Optional[Path | str] = None,
    ) -> Optional[Path]:
        source_path = Path(source_path)

        Logger.print_status(f"Creating backup of {source_path} ...")

        if not source_path.exists():
            Logger.print_info(
                f"Directory '{source_path}' does not exist! Skipping backup..."
            )
            return None

        if not source_path.is_dir():
            Logger.print_info(f"'{source_path}' is not a directory! Skipping backup...")
            return None

        try:
            self._backup_root.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_dir_name = f"{backup_name}_{timestamp}"

            if target_path is not None:
                backup_path = self._backup_root.joinpath(target_path, backup_dir_name)
            else:
                backup_path = self._backup_root.joinpath(backup_dir_name)

            shutil.copytree(source_path, backup_path)

            Logger.print_ok(
                f"Successfully backed up '{source_path}' to '{backup_path}'"
            )
            return backup_path

        except Exception as e:
            Logger.print_error(f"Failed to backup directory '{source_path}': {e}")
            return None
