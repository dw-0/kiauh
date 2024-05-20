#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import re
import shutil
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, check_output, run
from typing import List
from zipfile import ZipFile

from components.klipper.klipper import Klipper
from utils import (
    MODULE_PATH,
    NGINX_CONFD,
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
)
from utils.decorators import deprecated
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
            check_output(command, stderr=DEVNULL)
            return True
        except CalledProcessError:
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
        run(cmd, stderr=PIPE, check=True)
    except CalledProcessError as e:
        Logger.print_error(f"Failed to create symlink: {e}")
        raise


def remove_with_sudo(file_path: Path) -> None:
    try:
        cmd = ["sudo", "rm", "-f", file_path]
        run(cmd, stderr=PIPE, check=True)
    except CalledProcessError as e:
        Logger.print_error(f"Failed to remove file: {e}")
        raise


@deprecated(info="Use remove_with_sudo instead", replaced_by=remove_with_sudo)
def remove_file(file_path: Path, sudo=False) -> None:
    try:
        cmd = f"{'sudo ' if sudo else ''}rm -f {file_path}"
        run(cmd, stderr=PIPE, check=True, shell=True)
    except CalledProcessError as e:
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
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
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
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
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
        run(command, stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Unable to create '{target}': {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def read_ports_from_nginx_configs() -> List[int]:
    """
    Helper function to iterate over all NGINX configs and read all ports defined for listen
    :return: A sorted list of listen ports
    """
    if not NGINX_SITES_ENABLED.exists():
        return []

    port_list = []
    for config in NGINX_SITES_ENABLED.iterdir():
        with open(config, "r") as cfg:
            lines = cfg.readlines()

        for line in lines:
            line = line.replace("default_server", "")
            line = re.sub(r"[;:\[\]]", "", line.strip())
            if line.startswith("listen") and line.split()[-1] not in port_list:
                port_list.append(line.split()[-1])

    ports_to_ints_list = [int(port) for port in port_list]
    return sorted(ports_to_ints_list, key=lambda x: int(x))


def is_valid_port(port: int, ports_in_use: List[int]) -> bool:
    return port not in ports_in_use


def get_next_free_port(ports_in_use: List[int]) -> int:
    valid_ports = set(range(80, 7125))
    used_ports = set(map(int, ports_in_use))

    return min(valid_ports - used_ports)


def remove_nginx_config(name: str) -> None:
    Logger.print_status(f"Removing NGINX config for {name.capitalize()} ...")
    try:
        remove_file(NGINX_SITES_AVAILABLE.joinpath(name), True)
        remove_file(NGINX_SITES_ENABLED.joinpath(name), True)

    except CalledProcessError as e:
        log = f"Unable to remove NGINX config '{name}':\n{e.stderr.decode()}"
        Logger.print_error(log)


def remove_nginx_logs(name: str, instances: List[Klipper]) -> None:
    Logger.print_status(f"Removing NGINX logs for {name.capitalize()} ...")
    try:
        remove_file(Path(f"/var/log/nginx/{name}-access.log"), True)
        remove_file(Path(f"/var/log/nginx/{name}-error.log"), True)

        if not instances:
            return

        for instance in instances:
            remove_file(instance.log_dir.joinpath(f"{name}-access.log"))
            remove_file(instance.log_dir.joinpath(f"{name}-error.log"))

    except (OSError, CalledProcessError) as e:
        Logger.print_error(f"Unable to remove NGINX logs:\n{e}")
