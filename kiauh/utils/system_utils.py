#!/usr/bin/env python

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
import sys
import time
from pathlib import Path
from typing import List

from kiauh.utils.constants import COLOR_RED, RESET_FORMAT
from kiauh.utils.input_utils import get_confirm
from kiauh.utils.logger import Logger


def kill(opt_err_msg=None) -> None:
    """
    Kill the application.

    Parameters
    ----------
    opt_err_msg : str
        optional, additional error message to display

    Returns
    ----------
    None
    """

    if opt_err_msg:
        Logger.print_error(opt_err_msg)
    Logger.print_error("A critical error has occured. KIAUH was terminated.")
    sys.exit(1)


def clone_repo(target_dir: Path, url: str, branch: str) -> None:
    Logger.print_info(f"Cloning repository from {url}")
    if not target_dir.exists():
        try:
            command = ["git", "clone", f"{url}"]
            subprocess.run(command, check=True)

            command = ["git", "checkout", f"{branch}"]
            subprocess.run(command, cwd=target_dir, check=True)

            Logger.print_ok("Clone successfull!")
        except subprocess.CalledProcessError as e:
            print("Error cloning repository:", e.output.decode())
    else:
        overwrite_target = get_confirm("Target directory already exists. Overwrite?")
        if overwrite_target:
            try:
                shutil.rmtree(target_dir)
                clone_repo(target_dir, url, branch)
            except OSError as e:
                print("Error removing existing repository:", e.strerror)
        else:
            print("Skipping re-clone of repository ...")


def parse_packages_from_file(source_file) -> List[str]:
    packages = []
    print("Reading dependencies...")
    with open(source_file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("PKGLIST="):
                line = line.replace('"', "")
                line = line.replace("PKGLIST=", "")
                line = line.replace("${PKGLIST}", "")
                packages.extend(line.split())
    return packages


def create_python_venv(target: Path) -> None:
    Logger.print_info("Set up Python virtual environment ...")
    if not target.exists():
        try:
            command = ["python3", "-m", "venv", f"{target}"]
            result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0 or result.stderr:
                print(f"{COLOR_RED}{result.stderr}{RESET_FORMAT}")
                Logger.print_error("Setup of virtualenv failed!")
                return

            Logger.print_ok("Setup of virtualenv successfull!")
        except subprocess.CalledProcessError as e:
            print("Error setting up virtualenv:", e.output.decode())
    else:
        overwrite_venv = get_confirm("Virtualenv already exists. Re-create?")
        if overwrite_venv:
            try:
                shutil.rmtree(target)
                create_python_venv(target)
            except OSError as e:
                Logger.print_error(
                    f"Error removing existing virtualenv: {e.strerror}", False
                )
        else:
            print("Skipping re-creation of virtualenv ...")


def update_python_pip(target: Path) -> None:
    Logger.print_info("Updating pip ...")
    try:
        command = [f"{target}/bin/pip", "install", "-U", "pip"]
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating pip failed!")
            return

        Logger.print_ok("Updating pip successfull!")
    except subprocess.CalledProcessError as e:
        print("Error updating pip:", e.output.decode())


def install_python_requirements(target: Path, requirements: Path) -> None:
    update_python_pip(target)
    Logger.print_info("Installing Python requirements ...")
    try:
        command = [f"{target}/bin/pip", "install", "-r", f"{requirements}"]
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Installing Python requirements failed!")
            return

        Logger.print_ok("Installing Python requirements successfull!")
    except subprocess.CalledProcessError as e:
        print("Error installing Python requirements:", e.output.decode())


def update_system_package_lists(silent: bool, rls_info_change=False) -> None:
    cache_mtime = 0
    cache_files = ["/var/lib/apt/periodic/update-success-stamp", "/var/lib/apt/lists"]
    for cache_file in cache_files:
        if Path(cache_file).exists():
            cache_mtime = max(cache_mtime, os.path.getmtime(cache_file))

    update_age = int(time.time() - cache_mtime)
    update_interval = 6 * 3600  # 48hrs

    if update_age <= update_interval:
        return

    if not silent:
        print("Updating package list...")

    try:
        command = ["sudo", "apt-get", "update"]
        if rls_info_change:
            command.append("--allow-releaseinfo-change")

        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating system package list failed!")
            return

        Logger.print_ok("System package list updated successfully!")
    except subprocess.CalledProcessError as e:
        kill(f"Error updating system package list:\n{e.stderr.decode()}")


def install_system_packages(packages: List) -> None:
    try:
        command = ["sudo", "apt-get", "install", "-y"]
        for pkg in packages:
            command.append(pkg)
        subprocess.run(command, stderr=subprocess.PIPE, check=True)

        Logger.print_ok("Packages installed successfully.")
    except subprocess.CalledProcessError as e:
        kill(f"Error installing packages:\n{e.stderr.decode()}")


def create_directory(_dir: Path) -> None:
    try:
        if not os.path.isdir(_dir):
            Logger.print_info(f"Create directory: {_dir}")
            os.makedirs(_dir, exist_ok=True)
            Logger.print_ok("Directory created!")
        else:
            Logger.print_info(f"Directory already exists: {_dir}\nSkip creation ...")
    except OSError as e:
        Logger.print_error(f"Error creating folder: {e}")
        raise


def mask_system_service(service_name: str) -> None:
    try:
        command = ["sudo", "systemctl", "mask", service_name]
        subprocess.run(command, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        Logger.print_error(
            f"Unable to mask system service {service_name}: {e.stderr.decode()}"
        )
        raise
