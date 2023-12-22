#!/usr/bin/env python3
# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

from kiauh.utils import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED, MODULE_PATH, NGINX_CONFD
from kiauh.utils.logger import Logger


def check_file_exist(file_path: Path) -> bool:
    """
    Helper function for checking the existence of a file where
    elevated permissions are required |
    :param file_path: the absolute path of the file to check
    :return: True if file exists, otherwise False
    """
    try:
        command = ["sudo", "find", file_path]
        subprocess.check_output(command, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def create_directory(_dir: Path) -> None:
    """
    Helper function for creating a directory or skipping if it already exists |
    :param _dir: the directory to create
    :return: None
    """
    try:
        if not os.path.isdir(_dir):
            os.makedirs(_dir, exist_ok=True)
            Logger.print_ok(f"Created directory: {_dir}")
    except OSError as e:
        Logger.print_error(f"Error creating folder: {e}")
        raise


def remove_file(file_path: Path, sudo=False) -> None:
    try:
        command = f"{'sudo ' if sudo else ''}rm -f {file_path}"
        subprocess.run(command, stderr=subprocess.PIPE, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        log = f"Cannot remove file {file_path}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise

def unzip(file: str, target_dir: str) -> None:
    """
    Helper function to unzip a zip-archive into a target directory |
    :param file: the zip-file to unzip
    :param target_dir: the target directory to extract the files into
    :return: None
    """
    with ZipFile(file, "r") as _zip:
        _zip.extractall(target_dir)


def create_upstream_nginx_cfg() -> None:
    """
    Creates an upstream.conf in /etc/nginx/conf.d
    :return: None
    """
    source = os.path.join(MODULE_PATH, "res", "upstreams.conf")
    target = os.path.join(NGINX_CONFD, "upstreams.conf")
    try:
        command = ["sudo", "cp", source, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def create_common_vars_nginx_cfg() -> None:
    """
    Creates a common_vars.conf in /etc/nginx/conf.d
    :return: None
    """
    source = os.path.join(MODULE_PATH, "res", "common_vars.conf")
    target = os.path.join(NGINX_CONFD, "common_vars.conf")
    try:
        command = ["sudo", "cp", source, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create upstreams.conf: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def create_nginx_cfg(name: str, port: int, root_dir: str) -> None:
    """
    Creates an NGINX config from a template file and replaces all placeholders
    :param name: name of the config to create
    :param port: listen port
    :param root_dir: directory of the static files
    :return: None
    """
    tmp = f"{Path.home()}/{name}.tmp"
    shutil.copy(os.path.join(MODULE_PATH, "res", "nginx_cfg"), tmp)
    with open(tmp, "r+") as f:
        content = f.read()
        content = content.replace("%NAME%", name)
        content = content.replace("%PORT%", str(port))
        content = content.replace("%ROOT_DIR%", root_dir)
        f.seek(0)
        f.write(content)
        f.truncate()

    target = os.path.join(NGINX_SITES_AVAILABLE, name)
    try:
        command = ["sudo", "mv", tmp, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create '{target}': {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def delete_default_nginx_cfg() -> None:
    """
    Deletes a default NGINX config
    :return: None
    """
    default_cfg = Path("/etc/nginx/sites-enabled/default")
    if not check_file_exist(default_cfg):
        return

    try:
        command = ["sudo", "rm", default_cfg]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to delete '{default_cfg}': {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def enable_nginx_cfg(name: str) -> None:
    """
    Helper method to enable an NGINX config |
    :param name: name of the config to enable
    :return: None
    """
    source = os.path.join(NGINX_SITES_AVAILABLE, name)
    target = os.path.join(NGINX_SITES_ENABLED, name)
    if check_file_exist(Path(target)):
        return

    try:
        command = ["sudo", "ln", "-s", source, target]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        log = f"Unable to create symlink: {e.stderr.decode()}"
        Logger.print_error(log)
        raise
