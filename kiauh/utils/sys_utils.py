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
import select
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen
from typing import List, Literal, Set, Tuple

from core import backends
from core.constants import SYSTEMD
from core.i18n import _tr
from core.logger import Logger
from utils.fs_utils import check_file_exist, remove_with_sudo
from utils.input_utils import get_confirm


def get_current_user() -> str:
    if os.name == "posix":
        import pwd

        return pwd.getpwuid(os.getuid())[0]

    import getpass

    return getpass.getuser()


def get_user_groups() -> List[str]:
    if os.name != "posix":
        return []

    import grp

    return [grp.getgrgid(gid).gr_name for gid in os.getgroups()]


SysCtlServiceAction = Literal[
    "start",
    "stop",
    "restart",
    "reload",
    "enable",
    "disable",
    "mask",
    "unmask",
]
SysCtlManageAction = Literal["daemon-reload", "reset-failed"]


def run(cmd: str | List[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return backends.command_runner.run(cmd, **kwargs)


def check_output(cmd: str | List[str], **kwargs) -> str | bytes:
    return backends.command_runner.check_output(cmd, **kwargs)


def call(cmd: str | List[str], **kwargs) -> int:
    return backends.command_runner.call(cmd, **kwargs)


def popen(cmd: str | List[str], **kwargs) -> Popen:
    return backends.command_runner.popen(cmd, **kwargs)


class VenvCreationFailedException(Exception):
    pass


def kill(opt_err_msg: str = "") -> None:
    if opt_err_msg:
        Logger.print_error(opt_err_msg)
    Logger.print_error(_tr("A critical error has occured. KIAUH was terminated."))
    sys.exit(1)


def check_python_version(major: int, minor: int) -> bool:
    if not (sys.version_info.major >= major and sys.version_info.minor >= minor):
        Logger.print_error(_tr("Versioncheck failed!"))
        Logger.print_error(_tr("Python {}.{} or newer required.").format(major, minor))
        return False
    return True


def parse_packages_from_file(source_file: Path) -> List[str]:
    packages = []
    with open(source_file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("PKGLIST="):
                line = line.replace('"', "")
                line = line.replace("PKGLIST=", "")
                line = line.replace("${PKGLIST}", "")
                packages.extend(line.split())

    return packages


def create_python_venv(
    target: Path,
    force: bool = False,
    allow_access_to_system_site_packages: bool = False,
    use_python_binary: str | None = None,
    interactive: bool = True,
) -> bool:
    Logger.print_status(_tr("Set up Python virtual environment ..."))
    python_binary = use_python_binary if use_python_binary else "/usr/bin/python3"
    cmd = ["virtualenv", "-p", python_binary, target.as_posix()]
    cmd.append(
        "--system-site-packages"
    ) if allow_access_to_system_site_packages else None

    n = 2
    while n > 0:
        if not target.exists():
            try:
                run(cmd, check=True)
                Logger.print_ok(_tr("Setup of virtualenv successful!"))
                return True
            except CalledProcessError as e:
                Logger.print_error(_tr("Error setting up virtualenv:\n{}").format(e))
                return False
        else:
            if n == 1:
                Logger.print_error(_tr("Virtualenv still exists after deletion."))
                return False
            if not force:
                if not interactive:
                    Logger.print_info(
                        _tr("Virtualenv already exists; skipping re-creation ...")
                    )
                    return False
                if not get_confirm(
                    _tr("Virtualenv already exists. Re-create?"), default_choice=False
                ):
                    Logger.print_info(_tr("Skipping re-creation of virtualenv ..."))
                    return False

            try:
                shutil.rmtree(target)
                n -= 1
            except OSError as e:
                log = _tr("Error removing existing virtualenv: {}").format(e.strerror)
                Logger.print_error(log, False)
                return False


def update_python_pip(target: Path) -> None:
    Logger.print_status(_tr("Updating pip ..."))
    try:
        pip_location: Path = target.joinpath("bin/pip")
        pip_exists: bool = check_file_exist(pip_location)

        if not pip_exists:
            raise FileNotFoundError(_tr("Error updating pip! Not found."))

        command = [pip_location.as_posix(), "install", "-U", "pip"]
        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error(_tr("Updating pip failed!"))
            raise RuntimeError(_tr("Updating pip failed!"))

        Logger.print_ok(_tr("Updating pip successful!"))
    except FileNotFoundError as e:
        Logger.print_error(e)
        raise
    except CalledProcessError as e:
        Logger.print_error(_tr("Error updating pip:\n{}").format(e.output.decode()))
        raise


def install_python_requirements(target: Path, requirements: Path) -> None:
    try:
        Logger.print_status(_tr("Installing Python requirements ..."))
        command = [
            target.joinpath("bin/pip").as_posix(),
            "install",
            "-r",
            f"{requirements}",
        ]
        result = run(command, stderr=PIPE, text=True)

        if result.returncode != 0:
            Logger.print_error(f"{result.stderr}", False)
            raise VenvCreationFailedException(_tr("Installing Python requirements failed!"))

        Logger.print_ok(_tr("Installing Python requirements successful!"))

    except Exception as e:
        log = _tr("Error installing Python requirements: {}").format(e)
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def install_python_packages(target: Path, packages: List[str]) -> None:
    try:
        Logger.print_status(_tr("Installing Python requirements ..."))
        command = [
            target.joinpath("bin/pip").as_posix(),
            "install",
        ]
        for pkg in packages:
            command.append(pkg)
        result = run(command, stderr=PIPE, text=True)

        if result.returncode != 0:
            Logger.print_error(f"{result.stderr}", False)
            raise VenvCreationFailedException(_tr("Installing Python requirements failed!"))

        Logger.print_ok(_tr("Installing Python requirements successful!"))

    except Exception as e:
        log = _tr("Error installing Python requirements: {}").format(e)
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def update_system_package_lists(silent: bool, rls_info_change=False) -> None:
    cache_mtime: float = 0
    cache_files: List[Path] = [
        Path("/var/lib/apt/periodic/update-success-stamp"),
        Path("/var/lib/apt/lists"),
    ]
    for cache_file in cache_files:
        if cache_file.exists():
            cache_mtime = max(cache_mtime, os.path.getmtime(cache_file))

    update_age = int(time.time() - cache_mtime)
    update_interval = 6 * 3600

    if update_age <= update_interval:
        return

    if not silent:
        Logger.print_status(_tr("Updating package list..."))

    try:
        command = ["sudo", "apt-get", "update"]
        if rls_info_change:
            command.append("--allow-releaseinfo-change")

        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error(_tr("Updating system package list failed!"))
            raise RuntimeError(_tr("Updating system package list failed!"))

        Logger.print_ok(_tr("System package list update successful!"))
    except CalledProcessError as e:
        Logger.print_error(_tr("Error updating system package list:\n{}").format(e.stderr.decode()))
        raise


def get_upgradable_packages() -> List[str]:
    try:
        command = ["apt", "list", "--upgradable"]
        output: str = check_output(command, stderr=DEVNULL, text=True, encoding="utf-8")
        pkglist: List[str] = []

        for line in output.split("\n"):
            if "/" not in line:
                continue
            pkg = line.split("/")[0]
            pkglist.append(pkg)

        return pkglist
    except CalledProcessError as e:
        raise Exception(_tr("Error reading upgradable packages: {}").format(e))


def check_package_install(packages: Set[str]) -> List[str]:
    not_installed = []
    for package in packages:
        command = ["dpkg-query", "-f'${Status}'", "--show", package]
        result = run(
            command,
            stdout=PIPE,
            stderr=DEVNULL,
            text=True,
        )
        if "installed" not in result.stdout.strip("'").split():
            not_installed.append(package)

    return not_installed


def install_system_packages(packages: List[str]) -> None:
    try:
        command = ["sudo", "apt-get", "install", "-y"]
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)

        Logger.print_ok(_tr("Packages successfully installed."))
    except CalledProcessError as e:
        Logger.print_error(_tr("Error installing packages:\n{}").format(e.stderr.decode()))
        raise


def upgrade_system_packages(packages: List[str]) -> None:
    try:
        command = ["sudo", "apt-get", "upgrade", "-y"]
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)

        Logger.print_ok(_tr("Packages successfully upgraded."))
    except CalledProcessError as e:
        raise Exception(_tr("Error upgrading packages:\n{}").format(e.stderr.decode()))


def get_ipv4_addr() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("192.255.255.255", 1))
        ipv4: str = str(s.getsockname()[0])
        s.close()
        return ipv4
    except Exception:
        s.close()
        return "127.0.0.1"


def download_file(url: str, target: Path, show_progress=True) -> None:
    try:
        if show_progress:
            urllib.request.urlretrieve(url, target, download_progress)
            sys.stdout.write("\n")
        else:
            urllib.request.urlretrieve(url, target)
    except urllib.error.HTTPError as e:
        Logger.print_error(_tr("Download failed! HTTP error occured: {}").format(e))
        raise
    except urllib.error.URLError as e:
        Logger.print_error(_tr("Download failed! URL error occured: {}").format(e))
        raise
    except Exception as e:
        Logger.print_error(_tr("Download failed! An error occured: {}").format(e))
        raise


def download_progress(block_num, block_size, total_size) -> None:
    downloaded = block_num * block_size
    percent = 100 if downloaded >= total_size else downloaded / total_size * 100
    mb = 1024 * 1024
    progress = int(percent / 5)
    remaining = "-" * (20 - progress)
    bar = "#" * progress
    dl = "\r" + _tr("Downloading: [{}{}]{:.2f}% ({:.2f}/{:.2f}MB)").format(
        bar, remaining, percent, downloaded / mb, total_size / mb
    )
    sys.stdout.write(dl)
    sys.stdout.flush()


def set_nginx_permissions() -> None:
    cmd = f"ls -ld {Path.home()} | cut -d' ' -f1"
    homedir_perm = run(cmd, shell=True, stdout=PIPE, text=True)
    permissions = homedir_perm.stdout

    if permissions.count("x") < 3:
        Logger.print_status(_tr("Granting NGINX the required permissions ..."))
        run(["chmod", "og+x", Path.home()])
        Logger.print_ok(_tr("Permissions granted."))


def cmd_sysctl_service(name: str, action: SysCtlServiceAction) -> None:
    try:
        Logger.print_status(_tr("{} {} ...").format(action.capitalize(), name))
        run(["sudo", "systemctl", action, name], stderr=PIPE, check=True)
        Logger.print_ok(_tr("OK!"))
    except CalledProcessError as e:
        log = _tr("Failed to {} {}: {}").format(action, name, e.stderr.decode())
        Logger.print_error(log)
        raise


def cmd_sysctl_manage(action: SysCtlManageAction) -> None:
    try:
        run(["sudo", "systemctl", action], stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = _tr("Failed to run {}: {}").format(action, e.stderr.decode())
        Logger.print_error(log)
        raise


def unit_file_exists(
    name: str, suffix: Literal["service", "timer"], exclude: List[str] | None = None
) -> bool:
    exclude = exclude or []
    pattern = re.compile(f"^{name}(-[0-9a-zA-Z]+)?.{suffix}$")
    service_list = [
        Path(SYSTEMD, service)
        for service in SYSTEMD.iterdir()
        if pattern.search(service.name) and not any(s in service.name for s in exclude)
    ]
    return any(service_list)


def log_process(process: Popen) -> None:
    while True:
        if process.stdout is not None:
            reads = [process.stdout.fileno()]
            ret = select.select(reads, [], [])
            for fd in ret[0]:
                if fd == process.stdout.fileno():
                    line = process.stdout.readline()
                    if line:
                        print(line.strip(), flush=True)
                    else:
                        break

        if process.poll() is not None:
            break


def create_service_file(name: str, content: str) -> None:
    try:
        run(
            ["sudo", "tee", SYSTEMD.joinpath(name)],
            input=content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(_tr("Service file created: {}").format(SYSTEMD.joinpath(name)))
    except CalledProcessError as e:
        Logger.print_error(_tr("Error creating service file: {}").format(e))
        raise


def create_env_file(path: Path, content: str) -> None:
    try:
        with open(path, "w") as env_file:
            env_file.write(content)
        Logger.print_ok(_tr("Env file created: {}").format(path))
    except OSError as e:
        Logger.print_error(_tr("Error creating env file: {}").format(e))
        raise


def remove_system_service(service_name: str) -> None:
    try:
        if not service_name.endswith(".service"):
            raise ValueError(_tr("service_name '{}' must end with '.service'").format(service_name))

        file: Path = SYSTEMD.joinpath(service_name)
        if not file.exists() or not file.is_file():
            Logger.print_info(_tr("Service '{}' does not exist! Skipped ...").format(service_name))
            return

        Logger.print_status(_tr("Removing {} ...").format(service_name))
        cmd_sysctl_service(service_name, "stop")
        cmd_sysctl_service(service_name, "disable")
        remove_with_sudo(file)
        cmd_sysctl_manage("daemon-reload")
        cmd_sysctl_manage("reset-failed")
        Logger.print_ok(_tr("{} successfully removed!").format(service_name))
    except Exception as e:
        Logger.print_error(_tr("Error removing {}: {}").format(service_name, e))
        raise


def get_service_file_path(instance_type: type, suffix: str) -> Path:
    from utils.common import convert_camelcase_to_kebabcase

    if not isinstance(instance_type, type):
        raise ValueError("instance_type must be a class")

    name: str = convert_camelcase_to_kebabcase(instance_type.__name__)
    if suffix != "":
        name += f"-{suffix}"

    file_path: Path = SYSTEMD.joinpath(f"{name}.service")

    return file_path


def get_distro_info() -> Tuple[str, str]:
    distro_info: str = check_output(["cat", "/etc/os-release"]).decode().strip()

    if not distro_info:
        raise ValueError(_tr("Error reading distro info!"))

    distro_id: str = ""
    distro_id_like: str = ""
    distro_version: str = ""

    for line in distro_info.split("\n"):
        if line.startswith("ID="):
            distro_id = line.split("=")[1].strip('"').strip()
        if line.startswith("ID_LIKE="):
            distro_id_like = line.split("=")[1].strip('"').strip()
        if line.startswith("VERSION_ID="):
            distro_version = line.split("=")[1].strip('"').strip()

    if distro_id == "raspbian":
        distro_id = distro_id_like

    if not distro_id:
        raise ValueError(_tr("Error reading distro id!"))
    if not distro_version:
        raise ValueError(_tr("Error reading distro version!"))

    return distro_id.lower(), distro_version


def get_system_timezone() -> str:
    timezone = "UTC"
    try:
        with open("/etc/timezone", "r") as f:
            timezone = f.read().strip()
    except FileNotFoundError:
        try:
            result = run(
                ["timedatectl", "show", "--property=Timezone"],
                capture_output=True,
                text=True,
                check=True,
            )
            timezone = result.stdout.strip().split("=")[1]
        except CalledProcessError:
            try:
                result = run(
                    ["readlink", "-f", "/etc/localtime"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                timezone = result.stdout.strip().split("zoneinfo/")[1]
            except (CalledProcessError, IndexError):
                Logger.print_warn(_tr("Could not determine system timezone, using UTC"))
    return timezone
