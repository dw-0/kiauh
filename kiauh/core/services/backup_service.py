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
from typing import List, Optional

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.logger import Logger
from utils.instance_utils import get_instances


class BackupService:
    def __init__(self):
        self._backup_root = Path.home().joinpath("kiauh_backups")

    @property
    def backup_root(self) -> Path:
        return self._backup_root

    @property
    def timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    ################################################
    # GENERIC BACKUP METHODS
    ################################################

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

            filename = (
                target_name
                or f"{source_path.stem}_{self.timestamp}{source_path.suffix}"
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

            backup_dir_name = f"{backup_name}_{self.timestamp}"

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

    ################################################
    # SPECIFIC BACKUP METHODS
    ################################################

    def backup_printer_cfg(self):
        klipper_instances: List[Klipper] = get_instances(Klipper)
        for instance in klipper_instances:
            target_path: Path = self._backup_root.joinpath(
                instance.data_dir.name, f"config_{self.timestamp}"
            )
            self.backup_file(
                source_path=instance.cfg_file,
                target_path=target_path,
                target_name=instance.cfg_file.name,
            )

    def backup_moonraker_conf(self):
        moonraker_instances: List[Moonraker] = get_instances(Moonraker)
        for instance in moonraker_instances:
            target_path: Path = self._backup_root.joinpath(
                instance.data_dir.name, f"config_{self.timestamp}"
            )
            self.backup_file(
                source_path=instance.cfg_file,
                target_path=target_path,
                target_name=instance.cfg_file.name,
            )

    def backup_printer_config_dir(self) -> None:
        instances: List[Klipper] = get_instances(Klipper)
        if not instances:
            # fallback: search for printer data directories in the user's home directory
            Logger.print_info("No Klipper instances found via systemd services.")
            Logger.print_info(
                "Attempting to find printer data directories in home directory..."
            )

            home_dir = Path.home()
            printer_data_dirs = []

            for pattern in ["printer_data", "printer_*_data"]:
                for data_dir in home_dir.glob(pattern):
                    if data_dir.is_dir():
                        printer_data_dirs.append(data_dir)

            if not printer_data_dirs:
                Logger.print_info("Unable to find directory to backup!")
                Logger.print_info(
                    "No printer data directories found in home directory."
                )
                return

            for data_dir in printer_data_dirs:
                self.backup_directory(
                    source_path=data_dir.joinpath("config"),
                    target_path=data_dir.name,
                    backup_name="config",
                )

            return

        for instance in instances:
            self.backup_directory(
                source_path=instance.base.cfg_dir,
                target_path=f"{instance.data_dir.name}",
                backup_name="config",
            )
