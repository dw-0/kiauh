# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
Privileged nginx site operations used to apply an HTTPS rewrite transactionally.

These wrap sudo + subprocess so the orchestration can back up the current
site, write the new one, validate it with `nginx -t`, and either reload or
restore the backup - never leaving nginx with a config it cannot load.
"""

from __future__ import annotations

from pathlib import Path
from subprocess import DEVNULL, PIPE, run

from core.logger import Logger
from utils.sys_utils import cmd_sysctl_service

BACKUP_SUFFIX = ".kiauh.bak"


def backup_site(site: Path) -> Path:
    """Copy the (root-owned) nginx site to a sibling backup and return it."""
    backup: Path = site.parent.joinpath(site.name + BACKUP_SUFFIX)
    run(["sudo", "cp", str(site), str(backup)], stderr=PIPE, check=True)
    return backup


def discard_backup(backup: Path) -> None:
    """
    Remove a site backup created by backup_site. Idempotent (``rm -f``) so it
    is safe to call even if a previous run already cleaned it up. Leaving the
    backup behind would litter the nginx config directory with a stale site.
    """
    run(["sudo", "rm", "-f", str(backup)], stderr=PIPE, check=True)


def write_site(site: Path, content: str) -> None:
    """Write `content` to the root-owned nginx site via `sudo tee`."""
    run(
        ["sudo", "tee", str(site)],
        input=content.encode(),
        stdout=DEVNULL,
        stderr=PIPE,
        check=True,
    )


def restore_site(backup: Path, site: Path) -> None:
    """Restore a previously created backup over the live nginx site."""
    run(["sudo", "cp", str(backup), str(site)], stderr=PIPE, check=True)


def nginx_config_test() -> bool:
    """
    Return True if `nginx -t` reports the current configuration is valid.
    On failure the nginx error (which names the offending line) is logged so
    a rejected rewrite is diagnosable instead of silently swallowed.
    """
    result = run(["sudo", "nginx", "-t"], stdout=PIPE, stderr=PIPE)
    if result.returncode != 0 and result.stderr:
        Logger.print_error(result.stderr.decode(errors="replace").strip(), False)
    return result.returncode == 0


def reload_nginx() -> None:
    """Gracefully reload nginx so it picks up the new site configuration."""
    cmd_sysctl_service("nginx", "reload")
