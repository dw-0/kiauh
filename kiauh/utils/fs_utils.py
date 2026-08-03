#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError
from typing import List
from zipfile import ZipFile

from core import backends
from core.i18n import _tr
from core.logger import Logger

# Delegate to the shared backends module so tests can substitute
# command_runner/filesystem from one location instead of patching module globals.


def run(cmd: str | List[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Run a command through the shared command runner."""
    return backends.command_runner.run(cmd, **kwargs)


def check_output(cmd: str | List[str], **kwargs) -> str | bytes:
    """Run a command and return its output through the shared command runner."""
    return backends.command_runner.check_output(cmd, **kwargs)


def call(cmd: str | List[str], **kwargs) -> int:
    """Run a command and return its exit code through the shared command runner."""
    return backends.command_runner.call(cmd, **kwargs)


def check_file_exist(file_path: Path, sudo=False) -> bool:
    """
    Helper function for checking the existence of a file.
    Also works with symlinks (returns False if broken) |
    :param file_path: the absolute path of the file to check
    :param sudo: use sudo if required
    :return: True, if file exists, otherwise False
    """
    if sudo:
        # -L forces find to follow symlinks
        # -maxdepth = 0 avoids losing time if `file_path` is a directory
        command = ["sudo", "find", "-L", file_path.as_posix(), "-maxdepth", "0"]
        try:
            check_output(command, stderr=DEVNULL)
            return True
        except CalledProcessError:
            return False
    else:
        if os.access(file_path, os.F_OK):
            return file_path.exists()
        else:
            return False


def create_symlink(source: Path, target: Path, sudo=False) -> None:
    """
    Helper function to create a symlink from source to target
    If the target file exists, it will be overwritten. |
    :param source: the source file/directory
    :param target: the target file/directory
    :param sudo: use sudo if required
    :return: None
    """
    try:
        # -f forcibly creates/overwrites the symlink
        cmd = ["ln", "-sf", source.as_posix(), target.as_posix()]
        if sudo:
            cmd.insert(0, "sudo")
        run(cmd, stderr=PIPE, check=True)
    except CalledProcessError as e:
        Logger.print_error(_tr("Failed to create symlink: {}").format(e))
        raise


def remove_with_sudo(files: Path | List[Path]) -> bool:
    _files = []
    _removed = []
    if isinstance(files, list):
        _files = files
    else:
        _files.append(files)

    for f in _files:
        try:
            cmd = ["sudo", "find", f.as_posix()]
            if call(cmd, stderr=DEVNULL, stdout=DEVNULL) == 1:
                Logger.print_info(_tr("File '{}' does not exist. Skipped ...").format(f))
                continue
            cmd = ["sudo", "rm", "-rf", f.as_posix()]
            run(cmd, stderr=PIPE, check=True)
            Logger.print_ok(_tr("File '{}' was successfully removed!").format(f))
            _removed.append(f)
        except CalledProcessError as e:
            Logger.print_error(_tr("Error removing file '{}': {}").format(f, e))

    return len(_removed) > 0


def run_remove_routines(file: Path) -> bool:
    try:
        if not backends.filesystem.is_symlink(file) and not backends.filesystem.exists(file):
            Logger.print_info(_tr("File '{}' does not exist. Skipped ...").format(file))
            return False

        if backends.filesystem.is_dir(file):
            backends.filesystem.rmtree(file)
        elif backends.filesystem.is_file(file) or backends.filesystem.is_symlink(file):
            backends.filesystem.unlink(file)
        else:
            Logger.print_error(_tr("File '{}' is neither a file nor a directory!").format(file))
            return False
        Logger.print_ok(_tr("File '{}' was successfully removed!").format(file))
        return True
    except OSError as e:
        Logger.print_error(_tr("Unable to delete '{}':\n{}").format(file, e))
        try:
            Logger.print_info(_tr("Trying to remove with sudo ..."))
            if remove_with_sudo(file):
                Logger.print_ok(_tr("File '{}' was successfully removed!").format(file))
                return True
        except CalledProcessError as e:
            Logger.print_error(_tr("Error deleting '{}' with sudo:\n{}").format(file, e))
            Logger.print_error(_tr("Remove this directory manually!"))
            return False
    # Direct and sudo removal both failed without raising; return a boolean so
    # callers get a predictable result.
    return False


def unzip(filepath: Path, target_dir: Path) -> None:
    """
    Helper function to unzip a zip-archive into a target directory |
    :param filepath: the path to the zip-file to unzip
    :param target_dir: the target directory to extract the files into
    :return: None
    """
    with ZipFile(filepath, "r") as _zip:
        _zip.extractall(target_dir)


def create_folders(dirs: List[Path]) -> None:
    try:
        for _dir in dirs:
            if backends.filesystem.exists(_dir):
                continue
            backends.filesystem.mkdir(_dir, exist_ok=True)
            Logger.print_ok(_tr("Created directory '{}'!").format(_dir))
    except OSError as e:
        Logger.print_error(_tr("Error creating directories: {}").format(e))
        raise


def get_data_dir(instance_type: type, suffix: str) -> Path:
    from utils.sys_utils import get_service_file_path

    # if the service file exists, we read the data dir path from it
    # this also ensures compatibility with pre v6.0.0 instances
    service_file_path: Path = get_service_file_path(instance_type, suffix)
    if service_file_path and service_file_path.exists():
        with open(service_file_path, "r") as service_file:
            lines = service_file.readlines()
            for line in lines:
                pattern = r"^EnvironmentFile=(.+)(/systemd/.+\.env)"
                match = re.search(pattern, line)
                if match:
                    return Path(match.group(1))

    if suffix != "":
        # this is the new data dir naming scheme introduced in v6.0.0
        return Path.home().joinpath(f"printer_{suffix}_data")

    return Path.home().joinpath("printer_data")
