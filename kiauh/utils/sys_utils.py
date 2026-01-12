# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import copy
import json
import os
import re
import select
import shutil
import socket
import stat
import sys
import time
import urllib.error
import urllib.request
from itertools import chain, combinations
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, Popen, check_output, run
from typing import Dict, List, Literal, OrderedDict, Set, Tuple

from core.constants import SYSTEMD
from core.logger import Logger
from core import emit_cast
from itertools import permutations
from typing import NamedTuple
from utils.fs_utils import check_file_exist, remove_with_sudo
from utils.input_utils import get_confirm

distro_cmd_changes = None
distro_cmd_changes_type = None
key_of_permutation = None
SCRIPT_DIR_VALUES = [  # values that resolve to directory of shell script
    '"$(dirname "$(readlink -f "${0}")")"',
    '"$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P)"',
]
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


def which(command: str):
    """
    Get the path to the command, or None if not in PATH. This is
    redundant with shutil.which but is backward-compatible with earlier
    version of Python.
    :param command: The command to find.
    :return: Full path to command, or None if not present.
    """
    PATH = os.environ.get('PATH')
    if PATH is None:
        print("Warning: No PATH variable, can't detect {}")
        return None
    exe_dirs = PATH.split(os.pathsep)  # such as ":" (separate multiple)
    # ^ Do *not* use os.path.sep, that is the slash.
    for exe_dir in exe_dirs:
        exe_dir = exe_dir.strip()
        try_path = os.path.join(exe_dir, command)
        if not os.path.isfile(try_path):
            continue
        if os.access(try_path, os.X_OK):
            return try_path
    return None


# The values in *PACKAGE_MANAGERS dicts group by package type,
#   to simplify logic when generating install commands. For
#   example, gcc is installed via
#   "{get_package_installer()} groupinstall 'Development Tools'"
#   as long as the package type is "rpm", whether it is yum or dnf.
SUPPORTED_PACKAGE_TYPE_OF_INSTALLER = {
    "apt-get": "deb",
    "apt": "deb",
    "dnf": "rpm",
    "yum": "rpm",
    "apk": "alpine",  # alpine to distinguish it from Android
}
PACKAGE_TYPE_OF_INSTALLER = {  # All known package types.
    "pacman": "arch",  # Move to list above after fully supported
    "brew": "brew",
    "macports": "macports",
    # Not-implemented ones listed are here
    # but SUPPORTED_PACKAGE_TYPES are added via update below.
}
PACKAGE_TYPE_OF_INSTALLER.update(SUPPORTED_PACKAGE_TYPE_OF_INSTALLER)

PACKAGE_GROUPS = {
    "rpm": {
        "Development Tools": ["gcc", "g++", "glibc-devel", "dpkg"],
    }
}
_DISTROS = None
_DEFAULT_DISTROS = None

_distros_meta_state = None
_distro_meta_is_default = True
_last_distros_meta_path = None
_distros_meta_scope = None

alpine_nginx_script = """
# kiauh workaround for nginx on Alpine-based Linux distros:
sudo mkdir -p /etc/nginx/sites-enabled
sudo mkdir -p /etc/nginx/sites-available
echo "# See /etc/nginx/httpd.d instead" | sudo tee /etc/nginx/sites-available/nothing_goes_here.md
if [ ! -f "/etc/nginx/sites-enabled/nothing_goes_here.md" ]; then
    if [ -L "/etc/nginx/sites-enabled/nothing_goes_here.md" ]; then
        # not a file but is a symlink, so must be a bad symlink.
        rm /etc/nginx/sites-enabled/nothing_goes_here.md
    fi
    sudo ln -s /etc/nginx/sites-available/nothing_goes_here.md /etc/nginx/sites-enabled/nothing_goes_here.md
fi
sudo mkdir -p /etc/nginx/http.d
if [ ! -f "/etc/nginx/http.d/00-fluidd.conf" ]; then
    if [ -L "/etc/nginx/http.d/00-fluidd.conf" ]; then
        # not a file but is a symlink, so must be a bad symlink.
        rm /etc/nginx/http.d/00-fluidd.conf
    fi
    sudo ln -s /etc/nginx/sites-available/fluidd /etc/nginx/http.d/00-fluidd.conf
    # ^ must end in conf for the sake of postmarketOS default nginx.conf.
fi
if [ -f "/etc/http.d/default.conf" ]; then
    >&2 echo "Warning: default site /etc/nginx/httpd.d/default.conf is present. This may interfere with /etc/nginx/httpd.d/00-fluid.conf"
fi
doas nft add rule inet filter input iifname {"lo","wlan0","eth0","en*"} tcp dport 80 counter accept
doas nft add rule inet filter input tcp dport 80 counter drop
doas mkdir -p /etc/nftables.d && echo 'add rule inet filter input tcp dport 80 accept comment "Fluidd"' | doas tee /etc/nftables.d/10-fluidd.nft
 >/dev/null

sudo apk add -q dhclient
sudo mkdir -p /etc/NetworkManager/conf.d
echo "[main]" | sudo tee /etc/NetworkManager/conf.d/dhcp-client.conf
echo "dhcp=dhclient" | sudo tee -a /etc/NetworkManager/conf.d/dhcp-client.conf
echo "[connection]" | sudo tee /etc/NetworkManager/conf.d/disable-powersave.conf
echo "wifi.powersave=2" | sudo tee -a /etc/NetworkManager/conf.d/disable-powersave.conf
sudo systemctl restart NetworkManager
cat <<END
# Manual steps are required for CLI-based connection (Skip this if KlipperScreen's Network panel can add a connection not disrupted by low power state):
sudo nmcli connection add type wifi con-name "MyWifi" ifname wlan0 ssid "YOUR_SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "YOUR_PASSWORD"
sudo nmcli connection modify MyWifi connection.permissions ""
sudo nmcli connection up MyWifi
# Install ip command (`ip -json -det address` such as used by Klipper [KlipperScreen?], instead of limited BusyBox version)
sudo apk add -q iproute2
END

"""


class VenvCreationFailedException(Exception):
    pass


def supported_package_type(package_t: str) -> bool:
    """
    Check whether the package type is supported.
    Some functions may support additional package types, but this is
    "fail fast" to avoid repetitive or less explicit checks, as well as
    to indicate that the API for the type is complete.

    :param package_t: Package type such as returned by
        get_package_type_of(get_package_installer()) but
        the caller should cache get_package_installer().
    :return: Whether the package type is supported by kiauh.
    """
    return package_t in SUPPORTED_PACKAGE_TYPE_OF_INSTALLER.values()


def get_package_installer() -> str:
    """
    Get the name of this platform's package manager if possible.
    :return: Name of the distro's installer executable.
    """
    PATH = os.environ.get('PATH')
    if PATH is None:
        # Same early return as which, but prevent multiple
        #   warnings when problem is PATH not missing program.
        print("Warning: No PATH variable, can't detect {}")
        return None
    for mgr_name in PACKAGE_TYPE_OF_INSTALLER:
        command = which(mgr_name)
        if command is not None:
            return mgr_name  # return name not path, see docstring
    return None


def get_distros_meta_path(path=None, scope="repo"):
    """Get the path to the distros.json file with metadata for adapting
    to different distros.

    :param path: Optional path to distros.json file, defaults to config
        dir (see scope).
    :param scope: Optional scope for where to save:
        "user" for ~/.config/kiauh, "repo" for
        <repo root>/kiauh/static/, defaults to "repo"
    :raises NotImplementedError: If scope is not implemented.
    :return: The path to distros.json
    """
    if path is None:
        if scope == "user":
            conf_dir = os.path.expanduser("~/.config/kiauh")
        elif scope == "repo":
            utils_dir = os.path.dirname(os.path.abspath(__file__))
            module_dir = os.path.dirname(utils_dir)
            assert os.path.isfile(os.path.join(
                module_dir,
                "main.py"
            )), "module_dir detection failed--tried to look for main.py in {}".format(module_dir)
            conf_dir = os.path.join(
                module_dir,
                "static"
            )
        else:
            raise NotImplementedError("scope={}".format(scope))
        path = os.path.join(conf_dir, "distros.json")
    return path


def namedtuple_to_dict(var: NamedTuple) -> dict:
    d = {}
    for k in var._fields:
        d[k] = getattr(var, k)
    return d


def compare_dict(dict1, dict2, verbose=False, depth=0) -> bool:
    """
    Compare two keyed iterables regardless of type
    (such as dict, OrderedDict, or namedtuple).

    :param dict1: Any keyed iterable with items().
    :param dict2: Any keyed iterable with items().
    :return: Whether the keyed iterables match.
    """
    assert dict1 is not None
    assert dict2 is not None
    if hasattr(dict1, '_fields'):
        dict1 = namedtuple_to_dict(dict1)
    if hasattr(dict2, '_fields'):
        dict2 = namedtuple_to_dict(dict2)
    for k, v in dict1.items():
        if k not in dict2:
            return False
        if hasattr(v, '_fields'):
            v = namedtuple_to_dict(v)
        if not hasattr(v, 'items'):
            # leaf, so compare directly.
            if v != dict2[k]:
                if verbose:
                    print("[compare_dict] "+depth*"  "+"{} {} != {}"
                          .format(k, v, dict2[k]),
                          file=sys.stderr)
                return False
            continue
        if k not in dict2:
            return False
        if v is None:
            if dict2[k] is None:
                continue
            else:
                return False
        elif dict2[k] is None:
            if v is None:
                continue
            else:
                return False
        if not compare_dict(v, dict2[k], depth=depth+1):
            return False
    # Check for any that were not in dict1:
    for k, v in dict2.items():
        if k not in dict1:
            return False
    return True


def save_distros_meta(path=None) -> str:
    """Save the distros metadata such as per-distro package names.

    :param path: Optional path (Leave this None for recommended
        automatic system/user scope detection), defaults to
        get_distros_meta_path()
    :return: The file path that was saved (global _distros_meta_scope is
        also set if path is None)
    """
    global _distros_meta_state
    global _last_distros_meta_path
    global _distro_meta_is_default
    global _distros_meta_scope
    first_use = _distros_meta_state is None
    scope = _distros_meta_scope
    assert _DISTROS is not None, \
        "save_distros_meta cannot be used before load_distros_meta (_DISTROS is None)"
    if path is None:
        user_path = get_distros_meta_path(path=path, scope="user")
        path = get_distros_meta_path(path=path)
        scope = "repo"
        if not os.path.isfile(user_path):
            if not compare_dict(_DISTROS, _DEFAULT_DISTROS):
                # If differs from default save to user as override.
                scope = "user"
        if scope == "user":
            path = user_path
    dest_dir = os.path.dirname(path)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    print("Saving {}...".format(repr(path)))
    path = Path(path)
    if hasattr(path, 'with_suffix'):  # pathlib.Path
        tmp = path.with_suffix(".tmp")
    else:
        tmp = path + ".tmp"  # prevent corrupt file on json exception.
    with open(tmp, 'w') as stream:
        if compare_dict(_DISTROS, _DEFAULT_DISTROS):
            json.dump(_DISTROS, stream, indent=2, sort_keys=True)
        else:
            json.dump(_DISTROS, stream, indent=2)
        _distros_meta_scope = scope
    # _distro_meta_is_default = compare_dict(_DISTROS, _DEFAULT_DISTROS)
    _distro_meta_is_default = first_use
    if os.path.isfile(path):
        os.remove(path)
    shutil.move(tmp, path)
    _distros_meta_state = "saved"
    _last_distros_meta_path = path
    return path


def get_distros_metadata():
    global _DISTROS
    if _DISTROS is None:
        load_distros_meta()
    return _DISTROS


def load_distros_meta(path=None) -> str:
    """Load distros metadata such as equivalent package names.

    :param path: Where to load from (leave alone recommended automatic
        system/user scope detection), defaults to
        get_distros_meta_path().
    :return: The file path that was loaded (global _distros_meta_scope is
        also set if path is None)
    """
    global _distros_meta_state
    global _last_distros_meta_path
    global _distro_meta_is_default
    global _distros_meta_scope
    global _DISTROS
    global _DEFAULT_DISTROS
    scope = None
    if path is None:
        user_path = get_distros_meta_path(path=path, scope="user")
        path = get_distros_meta_path(path=path)
        if os.path.isfile(user_path):
            scope = "user"
        else:
            scope = "repo"
    if os.path.isfile(path):
        with open(path, 'r') as stream:
            distros = json.load(stream, object_pairs_hook=OrderedDict)
            renames = distros.get('deb_to_other')
            _distros_meta_scope = scope
        if renames is None:
            print("Warning: No deb_to_other section in {}."
                    " Rename the file to create the default file."
                    .format(path))

        _DISTROS = distros
        if _DEFAULT_DISTROS is None:
            if _distros_meta_scope == "repo":
                _DEFAULT_DISTROS = copy.deepcopy(_DISTROS)
            else:
                with open(get_distros_meta_path(scope="repo"), 'r') as stream:
                    _DEFAULT_DISTROS = json.load(
                        stream, object_pairs_hook=OrderedDict
                    )

        _distro_meta_is_default = compare_dict(_DISTROS, _DEFAULT_DISTROS)
        _distros_meta_state = "loaded"
        _last_distros_meta_path = path
        return path
    return None


def get_package_renames(path=None, package_type=None):
    if _distros_meta_state is None:
        load_distros_meta(path=path)
    if package_type is None:
        installer = get_package_installer()
        package_type = get_package_type_of(installer)
    return _DISTROS['deb_to_other'].get(package_type)


def translate_deb_package_name(dep: str, package_type: str) -> str:
    """
    Get this platform's non-deb name for the deb package.
    :param dep: The package name using deb (Debian) conventions.
    :param package_type: The package type using kiauh conventions
        such as returned by get_package_type_of.
    :return: Name given the well-known _DISTROS['deb_to_other'] or naming
        convention, otherwise the original dep string.
        Original list of package_type is "deb".
    """
    if package_type == "deb":
        return dep
    if _distros_meta_state is None:
        if not load_distros_meta():
            save_distros_meta()
    if package_type is None:
        raise ValueError("Expected str package_type, got None")
    assert (package_type not in PACKAGE_TYPE_OF_INSTALLER) or (package_type in _DISTROS['deb_to_other']), \
        "Expected package type, got installer."
    distro_renames = get_package_renames(package_type=package_type)
    if not distro_renames:
        return dep
    new_dep = distro_renames.get(dep)
    if not new_dep:
        # NOTE: all listed here must be in translations even if empty dict,
        #   so that early return doesn't occur above.
        if package_type == "alpine":
            if dep.startswith("python3-") and (dep != "python3-dev"):
                # All *except* python3-devel are shortened.
                return "py3-" + dep[8:]
            # May not be exact, but usually is (commented since not for
            #   many such as libffi-dev):
            # if dep.startswith("lib") and dep.endswith("-dev"):
            #     return dep[3:]  # Remove "lib" to meet naming convention.
        elif package_type == "arch":
            if dep.startswith("python3-"):
                return "python-" + dep[8:]  # Remove "3" to meet naming convention.
        elif package_type == "rpm":
            # May not be exact, but usually is:
            if dep.endswith("-dev"):
                return dep + "el"  # rpm naming convention for dev lib is *-devel
        return dep
    return new_dep


def translate_deb_package_names(deps: List[str], package_type: str) -> List[str]:
    """
    Get this platform's non-deb name for each deb package.
    The order is preserved for loose usage such as when there
    are pipes or other syntax after the packages.
    :param dep: The package names using deb (Debian) conventions.
    :param package_type: The package type using kiauh conventions
        such as returned by get_package_type_of.
    :return: Each name given the well-known _DISTROS['deb_to_other'] or naming
        convention, otherwise the original dep string.
        Original name if package_type is "deb"
    """
    if package_type == "deb":
        return deps
    new_deps = []
    for dep in deps:
        new_dep = translate_deb_package_name(
            dep,
            package_type=package_type,
        )
        if new_dep:
            if new_dep not in new_deps:
                new_deps.append(new_dep)
        if package_type == "alpine":
            if new_dep == "nginx":
                # Help with the transition from
                #   systemd.
                if "nginx-systemd" not in new_deps:
                    new_deps.append("nginx-systemd")
    return new_deps


def get_package_type_of(installer: str) -> str:
    """
    Get the package type for the given distro's installer.
    :param installer: The distro's package install command.
    :return: Package type which can be used as a key in
        translate_deb_package_name or certain constant dicts in this
        submodule.
    """
    return PACKAGE_TYPE_OF_INSTALLER[installer] if installer else None


def get_install_command(**kwargs) -> List[str]:
    """
    Get the full command and arg list.
    :param installer: Optional installer binary name
        for the distro such as "apt" (Set this to a
        stored value of get_package_installer() to
        reduce calls to that).
    :return: full command that should be placed before package name(s)
        to run an install as detected.
    """
    if "installer" in kwargs:
        installer = kwargs["installer"]
    else:
        installer = get_package_installer()
    pkg_t = get_package_type_of(installer)
    if not pkg_t:
        print("get_install_command is not implemented for {}"
              .format(get_installer_description(installer)),
              file=sys.stderr)
        return None
    command = ["sudo", installer]
    if pkg_t == "deb":
        command += ["install", "-y"]
    elif pkg_t == "alpine":
        command += ["add", "--quiet"]
    elif pkg_t == "rpm":
        command += ["install", "-y"]
    else:
        raise NotImplementedError(
            "Should have detected {} not in {} and returned"
            " before getting this far."
            .format(pkg_t, SUPPORTED_PACKAGE_TYPE_OF_INSTALLER.values()))
    return command


def get_installer_description(installer: str) -> str:
    """
    Get a description of the installer.
    :param installer: The installer binary name
        for the distro such as "apt".
    :return: Human-readable description of the distro's installer, or
        "Unknown" etc if unknown. Also gives the location of the distro
        metadata file, "default" if default data was used.
    """
    if installer is None:
        return "Unknown OS package system"
    pkg_t = get_package_type_of(installer)
    assert pkg_t is not None, \
        "Missing value for PACKAGE_TYPE_OF_INSTALLER[{}]".format(installer)
    # _distros_meta_state
    if _distro_meta_is_default:
        data_msg = "<default>"
    else:
        data_msg = _last_distros_meta_path
    return ("{} via {} (distro metadata: {})"
            .format(pkg_t, installer, data_msg))


def kill(opt_err_msg: str = "") -> None:
    """
    Kills the application |
    :param opt_err_msg: an optional, additional error message
    :return: None
    """

    if opt_err_msg:
        Logger.print_error(opt_err_msg)
    Logger.print_error("A critical error has occurred. KIAUH was terminated.")
    sys.exit(1)


def check_python_version(major: int, minor: int) -> bool:
    """
    Checks the python version and returns True if it's at least the given version
    :param major: the major version to check
    :param minor: the minor version to check
    :return: bool
    """
    if not (sys.version_info.major >= major and sys.version_info.minor >= minor):
        Logger.print_error("Version check failed!")
        Logger.print_error(f"Python {major}.{minor} or newer required.")
        return False
    return True


def parse_packages_from_file(source_file: Path) -> List[str]:
    """
    Read the package names from bash scripts, when defined like:
    PKGLIST="package1 package2 package3" |
    :param source_file: path of the sourcefile to read from
    :return: A list of package names
    """

    packages = []
    with open(source_file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("PKGLIST="):
                print("Parsing '{}'".format(line))
                line = line.replace('"', "")
                line = line.replace("PKGLIST=", "")
                line = line.replace("${PKGLIST}", "")
                packages.extend(line.split())

    return packages


def create_python_venv(
    target: Path,
    force: bool = False,
    allow_access_to_system_site_packages: bool = False,
    use_python_binary: str | None = None
) -> bool:
    """
    Create a python 3 virtualenv at the provided target destination.
    Returns True if the virtualenv was created successfully.
    Returns False if the virtualenv already exists, recreation was declined or creation failed.
    :param target: Path where to create the virtualenv at
    :param force: Force recreation of the virtualenv
    :param allow_access_to_system_site_packages: give the virtual environment access to the system site-packages dir
    :param use_python_binary: allows to override default python binary
    :return: bool
    """
    Logger.print_status("Set up Python virtual environment ...")
    # If binary override is not set, we use default defined here
    python_binary = use_python_binary if use_python_binary else "/usr/bin/python3"
    cmd = ["virtualenv", "-p", python_binary, target.as_posix()]
    cmd.append(
        "--system-site-packages"
    ) if allow_access_to_system_site_packages else None

    n = 2
    while(n > 0):
        if not target.exists():
            try:
                run(cmd, check=True)
                Logger.print_ok("Setup of virtualenv successful!")
                return True
            except CalledProcessError as e:
                Logger.print_error(f"Error setting up virtualenv:\n{e}")
                return False
        else:
            if n == 1:
                # This case should never happen, 
                # but the function should still behave correctly
                Logger.print_error("Virtualenv still exists after deletion.")
                return False                            
            if not force and not get_confirm(
                "Virtualenv already exists. Re-create?", default_choice=False
            ):
                Logger.print_info("Skipping re-creation of virtualenv ...")
                return False

            try:
                shutil.rmtree(target)
                n -= 1
            except OSError as e:
                log = f"Error removing existing virtualenv: {e.strerror}"
                Logger.print_error(log, False)
                return False


def update_python_pip(target: Path) -> None:
    """
    Updates pip in the provided target destination |
    :param target: Path of the virtualenv
    :return: None
    """
    Logger.print_status("Updating pip ...")
    try:
        pip_location: Path = target.joinpath("bin/pip")
        pip_exists: bool = check_file_exist(pip_location)

        if not pip_exists:
            raise FileNotFoundError("Error updating pip! Not found.")

        command = [pip_location.as_posix(), "install", "-U", "pip"]
        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating pip failed!")
            return

        Logger.print_ok("Updating pip successful!")
    except FileNotFoundError as e:
        Logger.print_error(e)
        raise
    except CalledProcessError as e:
        Logger.print_error(f"Error updating pip:\n{e.output.decode()}")
        raise


def install_python_requirements(target: Path, requirements: Path) -> None:
    """
    Installs the python packages based on a provided requirements.txt |
    :param target: Path of the virtualenv
    :param requirements: Path to the requirements.txt file
    :return: None
    """
    try:
        Logger.print_status("Installing Python requirements ...")
        command = [
            target.joinpath("bin/pip").as_posix(),
            "install",
            "-r",
            f"{requirements}",
        ]
        result = run(command, stderr=PIPE, text=True)

        if result.returncode != 0:
            Logger.print_error(f"{result.stderr}", False)
            raise VenvCreationFailedException("Installing Python requirements failed!")

        Logger.print_ok("Installing Python requirements successful!")

    except Exception as e:
        log = f"Error installing Python requirements: {e}"
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def install_python_packages(target: Path, packages: List[str]) -> None:
    """
    Installs the python packages based on a provided packages list |
    :param target: Path of the virtualenv
    :param packages: str list of required packages
    :return: None
    """
    try:
        Logger.print_status("Installing Python requirements ...")
        command = [
            target.joinpath("bin/pip").as_posix(),
            "install",
        ]
        for pkg in packages:
            command.append(pkg)
        result = run(command, stderr=PIPE, text=True)

        if result.returncode != 0:
            Logger.print_error(f"{result.stderr}", False)
            raise VenvCreationFailedException("Installing Python requirements failed!")

        Logger.print_ok("Installing Python requirements successful!")

    except Exception as e:
        log = f"Error installing Python requirements: {e}"
        Logger.print_error(log)
        raise VenvCreationFailedException(log)


def update_system_package_lists(silent: bool, rls_info_change=False, dry_run: bool = False) -> List[str]:
    """
    Updates the systems package list |
    :param silent: Log info to the console or not
    :param rls_info_change: Flag for "--allow-releaseinfo-change"
    :param dry_run: Just return the command (list).
    :return: The full command to refresh the package kit, or [] if N/A
        for this distro.
    """
    installer = get_package_installer()
    package_t = get_package_type_of(installer)
    command = []
    cache_mtime: float = 0
    cache_files: List[Path] = []
    if package_t == "deb":
        command = ["sudo", installer, "update"]
        cache_files += [
            Path("/var/lib/apt/periodic/update-success-stamp"),
            Path("/var/lib/apt/lists"),
        ]
    elif package_t == "alpine":
        command = ["sudo", installer, "update"]
        try_dir = "/var/cache/apk"
        if os.path.isdir(try_dir):
            cache_files.append(try_dir)
    if dry_run:
        return command
    if not command:
        # Any other OS doesn't need manual updating (normally)
        return command
    for cache_file in cache_files:
        if cache_file.exists():
            cache_mtime = max(cache_mtime, os.path.getmtime(cache_file))

    update_age = int(time.time() - cache_mtime)
    update_interval = 6 * 3600  # 48hrs

    if update_age <= update_interval:
        return command

    if not silent:
        Logger.print_status("Updating package list...")

    try:
        command = ["sudo", "apt-get", "update"]
        if rls_info_change:
            command.append("--allow-releaseinfo-change")

        result = run(command, stderr=PIPE, text=True)
        if result.returncode != 0 or result.stderr:
            Logger.print_error(f"{result.stderr}", False)
            Logger.print_error("Updating system package list failed!")
            return

        Logger.print_ok("System package list update successful!")
    except CalledProcessError as e:
        Logger.print_error(f"Error updating system package list:\n{e.stderr.decode()}")
        raise


def get_global_deps() -> List[str]:
    global_deps = ["git", "wget", "curl", "unzip", "dfu-util", "python3-virtualenv"]
    installer = get_package_installer()
    pkg_t = get_package_type_of(installer)
    global _DISTROS
    if _DISTROS is None:
        load_distros_meta()
    if pkg_t in "deb":
        pass  # ok already
    elif pkg_t in _DISTROS['deb_to_other']:
        global_deps = translate_deb_package_names(global_deps, pkg_t)
    else:
        raise NotImplementedError(
            "_DISTROS['deb_to_other'] (in global_deps) is not implemented for {}"
            .format(get_installer_description(installer)))
    return global_deps



def get_upgradable_packages() -> List[str]:
    """
    Reads all system packages that can be upgraded.
    :return: A list of package names available for upgrade
    """
    try:
        installer = get_package_installer()
        pkg_t = get_package_type_of(installer)
        if pkg_t in ("deb", "alpine"):
            command = [installer, "list", "--upgradable"]
        elif pkg_t == "rpm":
            command = [installer, "check-update"]
        else:
            print("Error: get_upgradeable_packages is not implemented"
                  " for {}. Can't check upgradeable."
                  .format(get_installer_description(installer)))
            return  # degrade gracefully (not fatal)
        output: str = check_output(command, stderr=DEVNULL, text=True, encoding="utf-8")
        pkglist = []
        for line in output.split("\n"):
            if "/" not in line:
                continue
            pkg = line.split("/")[0]
            pkglist.append(pkg)
        return pkglist
    except CalledProcessError as e:
        raise Exception(f"Error reading upgradable packages: {e}")


def check_package_install(packages: Set[str]) -> List[str]:
    """
    Checks the system for installed packages |
    :param packages: List of strings of package names
    :return: A list containing the names of packages that are not installed
    """
    not_installed = []
    installer = get_package_installer()
    pkg_t = get_package_type_of(installer)
    if not supported_package_type(pkg_t):
        print("Error: check_package_install is not implemented for {}. Can't check whether"
              " installed {}.".format(get_installer_description(installer), packages),
              file=sys.stderr)
        return not_installed
    all_installed = None
    list_command = None
    if pkg_t == "alpine":
        list_command = ["apk", "info"]
    elif pkg_t == "rpm":
        list_command = ["rpm", "-qa", "--qf", "'%{NAME}\\n'"]
    if list_command:
        sys.stderr.write("Listing packages...")
        sys.stderr.flush()
        result = run(
            list_command,
            stdout=PIPE,
            stderr=DEVNULL,
            text=True,
        )
        all_installed = [s.strip() for s in result.stdout.split("\n")]
        print("OK", file=sys.stderr)

    for package in packages:
        if all_installed is not None:
            if package not in all_installed:
                not_installed.append(package)
        elif pkg_t == "deb":
            command = ["dpkg-query", "-f'${Status}'", "--show", package]
            result = run(
                command,
                stdout=PIPE,
                stderr=DEVNULL,
                text=True,
            )
            if "installed" not in result.stdout.strip("'").split():
                not_installed.append(package)
        else:
            raise NotImplementedError(
                "Should have detected {} not in {} and returned"
                " before getting this far."
                .format(pkg_t, SUPPORTED_PACKAGE_TYPE_OF_INSTALLER.values()))

    return not_installed


def install_system_packages(packages: List[str]) -> None:
    """
    Installs a list of system packages |
    :param packages: List of system package names
    :return: None
    """
    installer = get_package_installer()
    pkg_t = get_package_type_of(installer)
    if not supported_package_type(pkg_t):
        error = ("Error: install_system_package is not implemented for {}. Can't install"
                 " {}.".format(get_installer_description(installer), packages))
        print(error, file=sys.stderr)
        return  # Degrade gracefully (Do not block kiauh:
        #   Maybe the user installed a package from source).
    try:
        command = get_install_command()
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)
        Logger.print_ok("Packages successfully installed.")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing packages:\n{e.stderr.decode()}")
        raise


def install_system_package_group(group: str) -> None:
    assert isinstance(str, group), \
        'expected str for group, got {}'.format(emit_cast(group))
    installer = get_package_installer()
    package_t = get_package_type_of(installer)
    command = ["sudo", installer]
    if package_t == "rpm":
        command += ["groupinstall", "-y", group]
    else:
        raise NotImplementedError(
            "No group install command is implemented for {}."
            .format(package_t))
    try:
        run(command, stderr=PIPE, check=True)
        Logger.print_ok("Package group successfully installed.")
    except CalledProcessError as e:
        Logger.print_error(f"Error installing '{group}' package group:\n{e.stderr.decode()}")
        raise

DEB_RELOADS = ["apt-get update", "apt update"]  # TODO: use deb_to_other_subcommands_any_args
_reload_command = None
# DEB_INSTALLS = ["apt install -y", "apt-get install -y",
#                 "apt install", "apt-get install"]  # Use deb_to_other_install_commands_any_order
PACKAGE_BASH_VARS = ["XSERVER", "CAGE", "PYGOBJECT", "MISC", "OPTIONAL"]
PACKAGE_BASH_VARS += ["PKGLIST"]  # Crowsnest

SUDOS = ["sudo", "doas", "runas"]


def get_reload_command(echo_if_none: bool=False) -> List[str]:
    """
    Get distro's package list cache reload command.
    :echo_if_none: If there is no reload command for the
        distro, return an echo command instead of [].
    :return: The command as a list of command + args,
        otherwise [] if not applicable to the distro
        (unless echo_if_none, then is an echo command).
    """
    global _reload_command
    if _reload_command is None:
        _reload_command = update_system_package_lists(silent=True, dry_run=True)
        if _reload_command is None:
            _reload_command = []
    if not _reload_command and echo_if_none:
        return ["echo", "Skipping package list reload"]
        # ^ has to be an actual command in case script
        #   checks for a return code, so echo (return 0 (ok) always
        #   for distro that doesn't require package list cache reload).
    return _reload_command


def split_shell_command(line: str, command: str, comment_delimiter: str="#",
                        statement_delimiter: str=";") -> List[str]:
    """Split a command into replaceable parts.

    :param line: Any shell script command/line.
    :param command: Any command to look for.
    :param comment_delimiter: Optional start of comment, defaults to
        "#".
    :param statement_delimiter: Optional starts of a new statement on
        the same line, defaults to ";".
    :return: List of: left (anything before command, such as sudo or
        doas unless also is in command--See SUDO for list of detected
        ones), found_command (same as command, but If command is None,
        left will contain everything and other parts will be ""),
        more_args_str (anything before pre_comment, or everything right
        of command if no comment, pre_comment (whitespace before
        comment, which may be a statement starting with
        statement_delimiter), comment.
    """
    left = None
    found_command = None
    more_args_str = ""
    pre_comment = ""
    comment = ""
    start = line.find(command)
    if start > -1:
        left = line[:start]
        pre_comment = ""
        comment = ""
        command_end = start + len(command)
        found_command = line[start:command_end]  # same as command, here for explicitness & testing
        # got_sudo = None
        left_sudo_idx = -1
        command_sudo_idx = -1
        for try_sudo in SUDOS:
            if left.rstrip().endswith(try_sudo):
                left_sudo_idx = left.rfind(try_sudo)
                # got_sudo = try_sudo
                break
        for try_sudo in SUDOS:
            if command.lstrip().startswith(try_sudo):
                command_sudo_idx = command.find(try_sudo)
                break
        if (left_sudo_idx > -1) and (command_sudo_idx > -1):
            left = (
                left[:left_sudo_idx]  # all before command except got_sudo
                # + left[left_sudo_idx+len(got_sudo):]  # Capture
                #   whitespace (commented since we are counting on
                #   whitespace so keeping this part would just mess up
                #   the indent level)
            )

        comment_i = line.find(comment_delimiter, command_end)
        more_args_end = len(line)
        statement_i = line.find(statement_delimiter, command_end)
        if comment_i > -1:
            if (statement_i > -1) and (statement_i < comment_i):
                more_args_end = statement_i
                pre_comment_len = len(line[:statement_i]) - len(line[:statement_i].rstrip())
                # ^ first capture whitespace to avoid breaking syntax
                pre_comment_len += comment_i - statement_i
            else:
                more_args_end = comment_i
                pre_comment_len = len(line[:comment_i]) - len(line[:comment_i].rstrip())
            pre_comment = line[comment_i-pre_comment_len:comment_i]
            comment = line[comment_i:]
        elif statement_i > -1:
            more_args_end = statement_i
            pre_comment = line[statement_i:]
        more_args_str = line[command_end:more_args_end].rstrip()
    if left is None:
        left = line
    return left, found_command, more_args_str, pre_comment, comment


def translate_script_line(line: str, script_path: str=None,
                          line_num: int=None,
                          installer: str=None,
                          add_alpine_nginx_script: bool=True,
                          variables: Dict[str, str] = None,
                          new_suffix: str=".kiauh-translated.sh") -> str:
    """
    Translate one line of a shell script.
    :param script_path: Optional path to script (Required if the script
        calls another script, so the other script can be found).
    :param line_num: Optional line number in script (for tracing)
    :param installer: Optional installer binary name such as "apt" for
        the distro (Set this to avoid multiple calls to
        get_install_command() by storing its return elsewhere).
    :param add_alpine_nginx_script: Optional workarounds for
        alpine linux nginx may be added to the script.
    :param variables: Optional collection where script variables can be
        used or added.
    :param new_suffix: Optional extension for translating called scripts
        automatically (Set to "" if other programs such as make need to
        access the scripts, so the original with be overwritten!)
    :return: The line, with package names translated (or same if deb),
        with any trailing newline removed if present.
        If it is a bash var, the package names will be enclosed
        in double quotes regardless of whether they were before
        (previous single or double quotes are stripped first).
    """
    if variables is None:
        variables = {}  # In this case it is a dummy since not
        #  preserved, but non-None reduces conditional code below.
    global distro_cmd_changes
    global distro_cmd_changes_type
    global key_of_permutation
    reload_str = " ".join(get_reload_command(echo_if_none=True))
    distros = get_distros_metadata()
    if installer is None:
        installer = get_package_installer()
    # new_install = get_install_command(installer=installer)
    # install_str = " ".join(new_install)
    package_type = get_package_type_of(installer)
    if package_type == "deb":
        # Current OS is deb-based so *skip translation completely*.
        return line.rstrip()
    line = line.rstrip()
    tab_len = len(line) - len(line.lstrip())
    tab = line[:tab_len]
    # ^ split_shell_command should handle tab (as part of pre_command),
    #   but get it here for explicitness.
    line = line.lstrip()
    initial_parts = line.strip().split()  # NOTE: "" splits to []!
    if initial_parts and initial_parts[0] == "check_dep":
        # bash function such as from core.sh in crowsnest
        if initial_parts[1].startswith('"'):
            assert initial_parts[1].endswith('"')
        return tab + initial_parts[0] + ' "{}"'.format(
            translate_deb_package_name(initial_parts[1].strip('"'),
                                       package_type))
    if distro_cmd_changes_type != package_type:
        distro_cmd_changes = None
    if distro_cmd_changes is None:
        distro_cmd_changes_type = package_type
        distro_cmd_changes = OrderedDict()
        key_of_permutation = {}
        for cmd_key in ['deb_to_other_install_commands_any_order',
                        'deb_to_other_subcommands_any_args']:
            assert cmd_key in distros, \
                '{} is missing from settings'.format(cmd_key)
            assert package_type in distros[cmd_key], \
                '{}[{}] is missing from settings'.format(cmd_key, package_type)
            # Sort from largest to smallest to avoid rewriting a command
            #   partially (Make sure "apt install -y" is detected before
            #   "apt install"):
            if cmd_key.endswith('_any_args'):
                # Add all subsets (permutations are done later)
                long_keys = distros[cmd_key][package_type].keys()
                keys = []
                for long_key in long_keys:
                    args_idx = None
                    parts = long_key.split()
                    for try_idx in range(len(parts)):
                        if parts[try_idx].startswith("-"):
                            args_idx = try_idx
                            break
                    if args_idx is not None:
                        args_l = list(parts[args_idx:])
                        for subset in chain.from_iterable(combinations(args_l, r) for r in range(1, len(args_l) + 1)):
                            generated_key = " ".join(parts[:args_idx]+list(subset))
                            keys.append(generated_key)
                            key_of_permutation[generated_key] = long_key
                        generated_key = " ".join(parts[:args_idx])
                        keys.append(generated_key)
                        key_of_permutation[generated_key] = long_key
                    else:
                        keys.append(long_key)
            else:
                # Add command and args (all permutations are done later)
                keys = distros[cmd_key][package_type].keys()
            keys = sorted(keys, key=len, reverse=True)
            for this_deb_cmd in keys:
                this_cmd_key = key_of_permutation.get(this_deb_cmd)
                if this_cmd_key is None:
                    this_cmd_key = this_deb_cmd
                this_new_cmd = distros[cmd_key][package_type][this_cmd_key]
                this_cmd_parts = this_deb_cmd.strip().split()
                other_cmd = "apt"
                if this_cmd_parts[0] == "apt":
                    other_cmd = "apt-get"
                for this_bin in (this_cmd_parts[0], other_cmd):
                    reorder_idx = 1
                    if len(this_cmd_parts) < 2:
                        reorder_idx = len(this_cmd_parts)  # no args to reorder
                    # elif not this_cmd_parts[1].startswith("-"):
                    #     # such as 'install'--reorder only options after it
                    #     reorder_idx = 2
                    # ^ -q can come before 'update', so even reorder subcommand
                    if reorder_idx < len(this_cmd_parts):
                        for perm in permutations(this_cmd_parts[reorder_idx:]):
                            # Insert permuted part back into the list
                            resulting_list = (
                                [this_bin] + this_cmd_parts[1:reorder_idx] + list(perm))
                            key = " ".join(resulting_list)
                            # this_new_cmd is always the one in distros.json:
                            distro_cmd_changes[key] = this_new_cmd
                    else:
                        resulting_list = [this_bin] + this_cmd_parts[1:]
                        key = " ".join(resulting_list)
                        distro_cmd_changes[key] = this_new_cmd
        print("Processing replacements: {}".format(json.dumps(distro_cmd_changes, indent=2)))

    for old_install, install_str in distro_cmd_changes.items():
        pre_command, command, more_args_str, pre_comment, comment = split_shell_command(
            line,
            old_install,
        )
        if command:
            pre_packages_len = len(more_args_str) - len(more_args_str.lstrip())
            pre_packages = more_args_str[:pre_packages_len]
            old_packages = more_args_str.strip().split()
            packages = translate_deb_package_names(
                old_packages,
                package_type,
            )
            # This is done in split_shell_command but
            #   in this case it may still have sudo
            #   since DEB_COMMANDS entries don't start
            #   with sudo so the double isn't detected
            #   (the double is in the new command, not
            #   the old command).
            pre_sudo_idx = -1
            # got_sudo = None
            for try_sudo in SUDOS:
                if pre_command.rstrip().endswith(try_sudo):
                    pre_sudo_idx = pre_command.rfind(try_sudo)
                    # got_sudo = try_sudo
            new_sudo_idx = -1
            for try_sudo in SUDOS:
                if install_str.lstrip().startswith(try_sudo):
                    new_sudo_idx = install_str.find(try_sudo)
            if (pre_sudo_idx > -1) and (new_sudo_idx > -1):
                # remove redundant got_sudo command
                pre_command = (
                    pre_command[:pre_sudo_idx]  # all before command except got_sudo
                    # + pre_command[pre_sudo_idx+len(got_sudo):]  # Capture
                    #   whitespace (commented since we are counting on
                    #   whitespace so keeping this part would just mess up
                    #   the indent level)
                )

            line = "{}{}{}{}{}{}{}".format(
                tab,
                pre_command,
                install_str,  # replaces command
                pre_packages,
                " ".join(packages),  # replaces more_args_str
                pre_comment,
                comment,
            )
            return line

    for old_reload in DEB_RELOADS:
        start = line.find(old_reload)
        if start > -1:
            cmd_end = start + len(old_reload)
            line = tab + line[:start] + reload_str + "  # " + line[cmd_end:]
            return line

    for var_name, value in variables.items():
        placeholders = ['${' + var_name + '}', '$' + var_name]
        for placeholder in placeholders:
            name_idx = line.find(placeholder)
            if name_idx < 0:
                continue
            sub_idx = name_idx + len(placeholder)
            # Characters that typically terminate a path in config/strings
            terminators = ' \t,"\''

            # Find the earliest occurrence of any terminator in the remaining string
            end_idx = len(line)  # default: goes to end of line
            for char in terminators:
                pos = line.find(char, sub_idx)
                if pos != -1 and pos < end_idx:
                    end_idx = pos

            sub = line[sub_idx:end_idx]
            if sub.startswith("/"):
                sub = sub[1:]
            try_path = os.path.join(value, sub)
            if os.path.isfile(try_path):
                new_path = try_path + new_suffix
                translate_script_file(
                    try_path,
                    new_path,
                    add_alpine_nginx_script=add_alpine_nginx_script,
                    installer=installer,
                )
                # ^ Generates new_path & makes it executable
                return tab + line[:end_idx] + new_suffix + line[end_idx:]
            else:
                Logger.print_warn(
                    "{} is not a file, so commands won't be translated"
                    " to {} if it is a called script."
                    .format(try_path, package_type))

    op_idx = line.find("=")
    if op_idx > -1:
        left = line[:op_idx].rstrip()
        var_name = left.strip()
        right = line[op_idx+1:].strip()
        if right in SCRIPT_DIR_VALUES:
            if script_path:
                variables[var_name] = os.path.dirname(script_path)
                Logger.print_info(
                    "Detected {}={}"
                    .format(var_name, variables[var_name]))
                return tab + line
            else:
                Logger.print_warn(
                    "There is no script_path, so can't resolve {}"
                    .format(repr(right)))
        if var_name in PACKAGE_BASH_VARS:
            packages_end = len(right)
            comment_i = right.find("#")
            comment = ""
            if comment_i > -1:
                packages_end = comment_i
                comment = right[comment_i:]
                right = right[:comment_i]
            right = right.strip()
            if right.startswith('"') and right.endswith('"'):
                right = right[1:-1]
            elif right.startswith("'") and right.endswith("'"):
                right = right[1:-1]
            old_packages = right.split()
            packages = translate_deb_package_names(old_packages, package_type)
            line = '{}{}="{}"{}'.format(
                tab,
                left,
                " ".join(packages),
                comment
            )
            return line
    return tab + line


def get_edit_comment(installer: str) -> str:
    return (
        "# translated from deb-based distro to {} by kiauh."
        " Initial translation code contributed by Poikilos at Hierosoft."
        .format(get_installer_description(installer)))


def translate_script(old_lines: List[str], add_alpine_nginx_script: bool=True,
                     installer: str=None, script_path: str=None,
                     variables: Dict[str, str]=None,
                     new_suffix: str=".kiauh-translated.sh") -> List[str]:

    """Translate a shell script's apt or apt-get commands to the given distro.
    See translate_script_line for details.

    :param old_lines: Shell script lines (any language with apt or
        apt-get commands)
    :param add_alpine_nginx_script: Optional add alpine_nginx_script if
        line contains both installer and "nginx" but only *if"
        package_type == "alpine" also, defaults to True
    :param installer: Optional installer executable name for the
        distro such as "apt", defaults to detected by looking for known
        installers in PATH
    :param script_path: Optional script being read (for tracing),
        defaults to None
    :param new_suffix: Optional extension for translating called scripts
        automatically (Set to "" if other programs such as make need to
        access the scripts, so the original with be overwritten!)
    :return: The translated script.
    """
    line_num = 0
    if installer is None:
        installer = get_package_installer()
    package_type = get_package_type_of(installer)
    command = get_install_command(installer=installer)
    lines = []
    if variables is None:
        variables = {}
    for line in old_lines:
        line_num += 1  # start at 1.
        if line_num == 2:
            lines.append(get_edit_comment(installer))
            # Macros and/or defines can go here if necessary.
        line = translate_script_line(
            line,
            installer=installer,
            script_path=script_path,
            line_num=line_num,
            add_alpine_nginx_script=add_alpine_nginx_script,
            variables=variables,
            new_suffix=new_suffix,
        )
        if package_type == "alpine":
            if ("nginx" in line) and (installer in line):
                # Put the fix on a separate line so it doesn't block
                #   the previous line if the workaround fails:
                extra_line = (" ".join(command) + "nginx-systemd")
                lines.append(extra_line)
                del extra_line
                if add_alpine_nginx_script:
                    for extra_line in alpine_nginx_script.split("\n"):
                        lines.append(extra_line)
                    add_alpine_nginx_script = False
        lines.append(line)
    return lines


def translate_script_file(file1: str, file2: str, add_alpine_nginx_script: bool=True,
                          installer: str=None, new_suffix: str=".kiauh-translated.sh") -> None:
    """Translate file to file. See translate_script for options and other details.
    """
    if hasattr(file2, 'with_suffix'):  # pathlib.Path
        tmp = file2.with_suffix(".tmp")
    else:
        tmp = file2 + ".tmp"  # prevent corrupt file on json exception.
    print("Creating translated {}".format(repr(file2)))
    variables = {}
    with open(file1, "r") as ins:
        with open(tmp, "w") as outs:
            old_lines = ins.readlines()
            new_lines = translate_script(
                old_lines,
                add_alpine_nginx_script=add_alpine_nginx_script,
                installer=installer,
                script_path=file1,
                variables=variables,
                new_suffix=new_suffix,
            )
            for line in new_lines:
                outs.write(line+"\n")
    if os.path.isfile(file2):
        os.remove(file2)
    shutil.move(tmp, file2)
    path = Path(file2)  # cast str to Path
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    # or:
    # Path(file2).chmod(0o755)


def upgrade_system_packages(packages: List[str]) -> None:
    """
    Updates a list of system packages |
    :param packages: List of system package names
    :return: None
    """
    installer = get_package_installer()
    pkg_t = get_package_type_of(installer)
    if not supported_package_type(pkg_t):
        error = ("Error: upgrade_system_packages is not implemented for {}. Can't install"
                 " {}.".format(get_installer_description(installer), packages))
        print(error, file=sys.stderr)
        return  # degrade gracefully (not fatal)
    try:
        command = ["sudo", installer]
        if pkg_t in ("deb", "rpm"):
            # ^ Same for all of these package managers
            command += ["upgrade", "-y"]
        elif pkg_t == "alpine":
            command += ["upgrade", "--quiet"]
        else:
            raise NotImplementedError(
                "Should have detected {} not in {} and returned"
                " before getting this far."
                .format(pkg_t, SUPPORTED_PACKAGE_TYPE_OF_INSTALLER.values()))
        for pkg in packages:
            command.append(pkg)
        run(command, stderr=PIPE, check=True)

        Logger.print_ok("Packages successfully upgraded.")
    except CalledProcessError as e:
        raise Exception(f"Error upgrading packages:\n{e.stderr.decode()}")


# this feels hacky and not quite right, but for now it works
# see: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ipv4_addr() -> str:
    """
    Helper function that returns the IPv4 of the current machine
    by opening a socket and sending a package to an arbitrary IP. |
    :return: Local IPv4 of the current machine
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(("192.255.255.255", 1))
        ipv4: str = str(s.getsockname()[0])
        s.close()
        return ipv4
    except Exception:
        s.close()
        return "127.0.0.1"


def download_file(url: str, target: Path, show_progress=True) -> None:
    """
    Helper method for downloading files from a provided URL |
    :param url: the url to the file
    :param target: the target path incl filename
    :param show_progress: show download progress or not
    :return: None
    """
    try:
        if show_progress:
            urllib.request.urlretrieve(url, target, download_progress)
            sys.stdout.write("\n")
        else:
            urllib.request.urlretrieve(url, target)
    except urllib.error.HTTPError as e:
        Logger.print_error(f"Download failed! HTTP error occurred: {e}")
        raise
    except urllib.error.URLError as e:
        Logger.print_error(f"Download failed! URL error occurred: {e}")
        raise
    except Exception as e:
        Logger.print_error(f"Download failed! An error occurred: {e}")
        raise


def download_progress(block_num, block_size, total_size) -> None:
    """
    Reporthook method for urllib.request.urlretrieve() method call in download_file() |
    :param block_num:
    :param block_size:
    :param total_size: total filesize in bytes
    :return: None
    """
    downloaded = block_num * block_size
    percent = 100 if downloaded >= total_size else downloaded / total_size * 100
    mb = 1024 * 1024
    progress = int(percent / 5)
    remaining = "-" * (20 - progress)
    dl = f"\rDownloading: [{'#' * progress}{remaining}]{percent:.2f}% ({downloaded / mb:.2f}/{total_size / mb:.2f}MB)"
    sys.stdout.write(dl)
    sys.stdout.flush()


def set_nginx_permissions() -> None:
    """
    Check if permissions of the users home directory
    grant execution rights to group and other and set them if not set.
    Required permissions for NGINX to be able to serve Mainsail/Fluidd.
    This seems to have become necessary with Ubuntu 21+. |
    :return: None
    """
    cmd = f"ls -ld {Path.home()} | cut -d' ' -f1"
    homedir_perm = run(cmd, shell=True, stdout=PIPE, text=True)
    permissions = homedir_perm.stdout

    if permissions.count("x") < 3:
        Logger.print_status("Granting NGINX the required permissions ...")
        run(["chmod", "og+x", Path.home()])
        Logger.print_ok("Permissions granted.")


def cmd_sysctl_service(name: str, action: SysCtlServiceAction) -> None:
    """
    Helper method to execute several actions for a specific systemd service. |
    :param name: the service name
    :param action: Either "start", "stop", "restart" or "disable"
    :return: None
    """
    try:
        Logger.print_status(f"{action.capitalize()} {name} ...")
        run(["sudo", "systemctl", action, name], stderr=PIPE, check=True)
        Logger.print_ok("OK!")
    except CalledProcessError as e:
        log = f"Failed to {action} {name}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def cmd_sysctl_manage(action: SysCtlManageAction) -> None:
    try:
        run(["sudo", "systemctl", action], stderr=PIPE, check=True)
    except CalledProcessError as e:
        log = f"Failed to run {action}: {e.stderr.decode()}"
        Logger.print_error(log)
        raise


def unit_file_exists(
    name: str, suffix: Literal["service", "timer"], exclude: List[str] | None = None
) -> bool:
    """
    Checks if a systemd unit file of the provided suffix exists.
    :param name: the name of the unit file
    :param suffix: suffix of the unit file, either "service" or "timer"
    :param exclude: List of strings of names to exclude
    :return: True if the unit file exists, False otherwise
    """
    exclude = exclude or []
    pattern = re.compile(f"^{name}(-[0-9a-zA-Z]+)?.{suffix}$")
    service_list = [
        Path(SYSTEMD, service)
        for service in SYSTEMD.iterdir()
        if pattern.search(service.name) and not any(s in service.name for s in exclude)
    ]
    return any(service_list)


def log_process(process: Popen) -> None:
    """
    Helper method to print stdout of a process in near realtime to the console.
    :param process: Process to log the output from
    :return: None
    """
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
    """
    Creates a service file at the provided path with the provided content.
    :param name: the name of the service file
    :param content: the content of the service file
    :return: None
    """
    try:
        run(
            ["sudo", "tee", SYSTEMD.joinpath(name)],
            input=content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {SYSTEMD.joinpath(name)}")
    except CalledProcessError as e:
        Logger.print_error(f"Error creating service file: {e}")
        raise


def create_env_file(path: Path, content: str) -> None:
    """
    Creates an env file at the provided path with the provided content.
    :param path: the path of the env file
    :param content: the content of the env file
    :return: None
    """
    try:
        with open(path, "w") as env_file:
            env_file.write(content)
        Logger.print_ok(f"Env file created: {path}")
    except OSError as e:
        Logger.print_error(f"Error creating env file: {e}")
        raise


def remove_system_service(service_name: str) -> None:
    """
    Disables and removes a systemd service
    :param service_name: name of the service unit file - must end with '.service'
    :return: None
    """
    try:
        if not service_name.endswith(".service"):
            raise ValueError(f"service_name '{service_name}' must end with '.service'")

        file: Path = SYSTEMD.joinpath(service_name)
        if not file.exists() or not file.is_file():
            Logger.print_info(f"Service '{service_name}' does not exist! Skipped ...")
            return

        Logger.print_status(f"Removing {service_name} ...")
        cmd_sysctl_service(service_name, "stop")
        cmd_sysctl_service(service_name, "disable")
        remove_with_sudo(file)
        cmd_sysctl_manage("daemon-reload")
        cmd_sysctl_manage("reset-failed")
        Logger.print_ok(f"{service_name} successfully removed!")
    except Exception as e:
        Logger.print_error(f"Error removing {service_name}: {e}")
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
    global _DISTROS
    if _DISTROS is None:
        load_distros_meta()
    distro_info: str = check_output(["cat", "/etc/os-release"]).decode().strip()

    if not distro_info:
        raise ValueError("Error reading distro info!")

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
        raise ValueError("Error reading distro id!")
    if not distro_version:
        raise ValueError("Error reading distro version!")

    return distro_id.lower(), distro_version


def get_system_timezone() -> str:
    timezone = "UTC"
    try:
        with open("/etc/timezone", "r") as f:
            timezone = f.read().strip()
    except FileNotFoundError:
        # fallback to reading timezone from timedatectl
        try:
            result = run(
                ["timedatectl", "show", "--property=Timezone"],
                capture_output=True,
                text=True,
                check=True,
            )
            timezone = result.stdout.strip().split("=")[1]
        except CalledProcessError:
            # fallback if timedatectl fails, try reading from readlink
            try:
                result = run(
                    ["readlink", "-f", "/etc/localtime"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                timezone = result.stdout.strip().split("zoneinfo/")[1]
            except (CalledProcessError, IndexError):
                Logger.print_warn("Could not determine system timezone, using UTC")
    return timezone
