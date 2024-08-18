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

from core.constants import (
    NGINX_CONFD,
    NGINX_SITES_AVAILABLE,
    NGINX_SITES_ENABLED,
)
from core.decorators import deprecated
from core.logger import Logger
from utils import MODULE_PATH


def check_file_exist(file_path: Path, sudo=False) -> bool:
    """
    Helper function for checking the existence of a file |
    :param file_path: the absolute path of the file to check
    :param sudo: use sudo if required
    :return: True, if file exists, otherwise False
    """
    if sudo:
        try:
            command = ["sudo", "find", file_path.as_posix()]
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
        cmd = ["ln", "-sf", source.as_posix(), target.as_posix()]
        if sudo:
            cmd.insert(0, "sudo")
        run(cmd, stderr=PIPE, check=True)
    except CalledProcessError as e:
        Logger.print_error(f"Failed to create symlink: {e}")
        raise


def remove_with_sudo(file: Path) -> None:
    try:
        cmd = ["sudo", "rm", "-rf", file.as_posix()]
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


def run_remove_routines(file: Path) -> None:
    try:
        if not file.exists():
            Logger.print_info(f"File '{file}' does not exist. Skipped ...")
            return

        if file.is_dir():
            shutil.rmtree(file)
        elif file.is_file():
            file.unlink()
        else:
            raise OSError(f"File '{file}' is neither a file nor a directory!")
        Logger.print_ok("Successfully removed!")
    except OSError as e:
        Logger.print_error(f"Unable to delete '{file}':\n{e}")
        try:
            Logger.print_info("Trying to remove with sudo ...")
            remove_with_sudo(file)
            Logger.print_ok("Successfully removed!")
        except CalledProcessError as e:
            Logger.print_error(f"Error deleting '{file}' with sudo:\n{e}")
            Logger.print_error("Remove this directory manually!")


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


def generate_nginx_cfg_from_template(name: str, template_src: Path, **kwargs) -> None:
    """
    Creates an NGINX config from a template file and
    replaces all placeholders passed as kwargs. A placeholder must be defined
    in the template file as %{placeholder}%.
    :param name: name of the config to create
    :param template_src: the path to the template file
    :return: None
    """
    tmp = Path.home().joinpath(f"{name}.tmp")
    shutil.copy(template_src, tmp)
    with open(tmp, "r+") as f:
        content = f.read()

        for key, value in kwargs.items():
            content = content.replace(f"%{key}%", str(value))

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


def create_nginx_cfg(
    display_name: str,
    cfg_name: str,
    template_src: Path,
    **kwargs,
) -> None:
    from utils.sys_utils import set_nginx_permissions

    try:
        Logger.print_status(f"Creating NGINX config for {display_name} ...")

        source = NGINX_SITES_AVAILABLE.joinpath(cfg_name)
        target = NGINX_SITES_ENABLED.joinpath(cfg_name)
        remove_file(Path("/etc/nginx/sites-enabled/default"), True)
        generate_nginx_cfg_from_template(cfg_name, template_src=template_src, **kwargs)
        create_symlink(source, target, True)
        set_nginx_permissions()

        Logger.print_ok(f"NGINX config for {display_name} successfully created.")
    except Exception:
        Logger.print_error(f"Creating NGINX config for {display_name} failed!")
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
        if not config.is_file():
            continue

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
