#!/usr/bin/env python3
# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from utils import (
    NGINX_SITES_AVAILABLE,
    MODULE_PATH,
    NGINX_CONFD,
)
from utils.logger import Logger


def check_file_exist(file_path: Path, sudo=False) -> bool:
    """
    Helper function for checking the existence of a file |
    :param file_path: the absolute path of the file to check
    :param sudo: use sudo if required
    :return: True, if file exists, otherwise False
    """
    if sudo:
        try:
            command = ["sudo", "find", file_path]
            subprocess.check_output(command, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    else:
        if file_path.exists():
            return True
        else:
            return False


def create_symlink(source: Path, target: Path, sudo=False) -> None:
    try:
        cmd = ["ln", "-sf", source, target]
        if sudo:
            cmd.insert(0, "sudo")
        subprocess.run(cmd, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        Logger.print_error(f"Failed to create symlink: {e}")
        raise


def remove_file(file_path: Path, sudo=False) -> None:
    try:
        cmd = f"{'sudo ' if sudo else ''}rm -f {file_path}"
        subprocess.run(cmd, stderr=subprocess.PIPE, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        log = f"Cannot remove file {file_path}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def unzip(filepath: Path, target_dir: Path) -> None:
    """
    Helper function to unzip a zip-archive into a target directory |
    :param filepath: the path to the zip-file to unzip
    :param target_dir: the target directory to extract the files into
    :return: None
    """
    with ZipFile(filepath, "r") as _zip:
        _zip.extractall(target_dir)


def copy_upstream_nginx_cfg() -> None:
    """
    Creates an upstream.conf in /etc/nginx/conf.d
    :return: None
    """
    source = MODULE_PATH.joinpath("assets/upstreams.conf")
    target = NGINX_CONFD.joinpath("upstreams.conf")
    try:
        command = ["sudo", "cp", source, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def copy_common_vars_nginx_cfg() -> None:
    """
    Creates a common_vars.conf in /etc/nginx/conf.d
    :return: None
    """
    source = MODULE_PATH.joinpath("assets/common_vars.conf")
    target = NGINX_CONFD.joinpath("common_vars.conf")
    try:
        command = ["sudo", "cp", source, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def create_nginx_cfg(name: str, port: int, root_dir: Path) -> None:
    """
    Creates an NGINX config from a template file and replaces all placeholders
    :param name: name of the config to create
    :param port: listen port
    :param root_dir: directory of the static files
    :return: None
    """
    tmp = Path.home().joinpath(f"{name}.tmp")
    shutil.copy(MODULE_PATH.joinpath("assets/nginx_cfg"), tmp)
    with open(tmp, "r+") as f:
        content = f.read()
        content = content.replace("%NAME%", name)
        content = content.replace("%PORT%", str(port))
        content = content.replace("%ROOT_DIR%", str(root_dir))
        f.seek(0)
        f.write(content)
        f.truncate()

    target = NGINX_SITES_AVAILABLE.joinpath(name)
    try:
        command = ["sudo", "mv", tmp, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create '{target}': {e.stderr.decode()}"
        Logger.print_error(log)
        raise
