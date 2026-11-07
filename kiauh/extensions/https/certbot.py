# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
Thin, side-effecting wrappers around certbot, apt and the credentials/renewal
files. Each function shells out via the same patterns the rest of KIAUH uses
(sudo + subprocess.run) and is kept small so it can be mocked in tests. The
DNS provider secret only ever flows into the credentials file through tee's
stdin - never as a command argument, a log line, or KIAUH config.
"""

from __future__ import annotations

from pathlib import Path
from subprocess import DEVNULL, PIPE, run
from typing import Dict, List, Optional, Tuple

from core.logger import Logger
from extensions.https import LE_LIVE_DIR, RENEWAL_HOOK_DIR, SECRETS_DIR
from extensions.https.providers import (
    DnsProvider,
    build_certbot_command,
    build_credentials_content,
)
from utils.sys_utils import check_package_install, install_system_packages

RENEW_HOOK_NAME = "kiauh-reload-nginx.sh"
RENEW_HOOK_CONTENT = "#!/bin/sh\nsystemctl reload nginx\n"
# certbot writes its full (root-only) diagnostic log here; point users at it
# rather than dumping certbot's stderr, which we never capture.
LETSENCRYPT_LOG = "/var/log/letsencrypt/letsencrypt.log"


def _sudo(args: List[str]) -> None:
    """Run `sudo <args>` and raise CalledProcessError on failure."""
    run(["sudo", *args], stderr=PIPE, check=True)


def _sudo_write(target: Path, content: str) -> None:
    """
    Write `content` to a root-owned file via `sudo tee`. The content is passed
    through stdin (never as an argument) and tee's stdout is discarded so a
    secret can never be echoed back to the terminal.
    """
    run(
        ["sudo", "tee", str(target)],
        input=content.encode(),
        stdout=DEVNULL,
        stderr=PIPE,
        check=True,
    )


def cert_paths(fqdn: str) -> Tuple[Path, Path]:
    """Return the (fullchain.pem, privkey.pem) paths certbot uses for `fqdn`."""
    live = LE_LIVE_DIR.joinpath(fqdn)
    return live.joinpath("fullchain.pem"), live.joinpath("privkey.pem")


def ensure_certbot(provider: DnsProvider) -> None:
    """Install certbot and the provider's DNS plugin if they are not present."""
    missing = check_package_install({"certbot", provider.plugin_package})
    if not missing:
        return
    Logger.print_status(f"Installing certbot packages: {', '.join(missing)} ...")
    install_system_packages(missing)


def credentials_file(fqdn: str) -> Path:
    """Return the per-certificate credentials file path for ``fqdn``."""
    return SECRETS_DIR.joinpath(f"{fqdn}.ini")


def write_credentials(provider: DnsProvider, values: Dict[str, str], fqdn: str) -> Path:
    """
    Write the provider credentials to a root-owned 0600 file under SECRETS_DIR
    and return its path. The directory is created and locked to 0700 first.

    The file is named per certificate (``<fqdn>.ini``), not per provider, so
    issuing or re-issuing one certificate never overwrites - and a failed run
    never deletes - the credentials another certificate's renewal depends on.

    :raises ValueError: if the provider has no credentials file (env/IAM auth)
    """
    if not provider.credentials_filename:
        raise ValueError(f"Provider '{provider.key}' does not use a credentials file.")

    target: Path = credentials_file(fqdn)
    content = build_credentials_content(provider, values)

    Logger.print_status(f"Writing DNS credentials to {target} ...")
    _sudo(["mkdir", "-p", str(SECRETS_DIR)])
    _sudo(["chmod", "700", str(SECRETS_DIR)])
    _sudo_write(target, content)
    _sudo(["chmod", "600", str(target)])
    return target


def remove_credentials(credentials_path: Path) -> None:
    """
    Remove a credentials file written by write_credentials. Idempotent
    (``rm -f``); used to clean up the token after a failed, aborted issuance so
    a secret-bearing file is not left behind for an operation that never
    completed.
    """
    run(["sudo", "rm", "-f", str(credentials_path)], stderr=PIPE, check=True)


def credentials_exist(fqdn: str) -> bool:
    """
    Return True if a credentials file for ``fqdn`` already exists. The check
    goes through sudo because the file lives in a 0700 directory the non-root
    caller cannot stat directly. Used to reuse the working credentials of a
    retained certificate on re-enable rather than overwrite them unvalidated.
    """
    path = credentials_file(fqdn)
    return run(["sudo", "test", "-f", str(path)], stderr=PIPE).returncode == 0


def credentials_match_provider(fqdn: str, provider: DnsProvider) -> bool:
    """
    Return True if the saved credentials file for ``fqdn`` looks compatible with
    ``provider`` - i.e. it contains the provider's first expected ini key. The
    file is a DNS-plugin-specific INI, so reusing one provider's file with
    another's plugin would fail; this guards against offering such a reuse.

    Checked via ``sudo grep`` on the key NAME (``-q``, no output) so the secret
    value is never read out of the root-owned file.
    """
    if not provider.credentials_fields:
        return True
    key = provider.credentials_fields[0].ini_key
    path = credentials_file(fqdn)
    return (
        run(["sudo", "grep", "-q", "--", key, str(path)], stderr=PIPE).returncode == 0
    )


def backup_credentials(fqdn: str) -> Path:
    """
    Copy the existing credentials file for ``fqdn`` aside as a root-owned
    ``.bak`` and return the backup path, so a failed replacement can restore the
    credentials a retained certificate still renews with. The caller must ensure
    the file exists first (see ``credentials_exist``).
    """
    path = credentials_file(fqdn)
    backup = path.with_name(path.name + ".bak")
    run(["sudo", "cp", "-p", str(path), str(backup)], stderr=PIPE, check=True)
    return backup


def restore_credentials(backup: Path, fqdn: str) -> None:
    """Move a credentials backup back into place (root-owned)."""
    run(
        ["sudo", "mv", str(backup), str(credentials_file(fqdn))],
        stderr=PIPE,
        check=True,
    )


def discard_credentials_backup(backup: Path) -> None:
    """Remove a credentials backup file. Idempotent (``rm -f``)."""
    run(["sudo", "rm", "-f", str(backup)], stderr=PIPE, check=True)


def run_certbot(
    provider: DnsProvider,
    fqdn: str,
    email: str,
    propagation_seconds: int,
    credentials_path: Optional[Path],
    force_renewal: bool = False,
) -> None:
    """
    Run `certbot certonly` for a DNS-01 issuance. certbot's progress is shown
    live (its output is not captured, so a secret cannot leak through it).

    With ``force_renewal`` certbot performs a real DNS challenge rather than
    keeping an unexpired certificate - used when replacing credentials so the
    new token is validated instead of silently accepted.

    :raises CalledProcessError: on failure - the caller MUST NOT touch nginx
        unless this returns successfully
    """
    cred = str(credentials_path) if credentials_path is not None else None
    cmd = build_certbot_command(
        provider, fqdn, email, propagation_seconds, cred, force_renewal=force_renewal
    )
    Logger.print_status(
        f"Requesting certificate for {fqdn} via {provider.display_name} DNS-01 ..."
    )
    run(cmd, check=True)


def install_renew_hook() -> None:
    """
    Install a certbot deploy hook that reloads nginx after a successful
    renewal. Idempotent (overwrites) and applies to every certificate; deploy
    hooks run only when a certificate is actually renewed.
    """
    target = RENEWAL_HOOK_DIR.joinpath(RENEW_HOOK_NAME)
    Logger.print_status("Installing nginx reload hook for certificate renewal ...")
    _sudo(["mkdir", "-p", str(RENEWAL_HOOK_DIR)])
    _sudo_write(target, RENEW_HOOK_CONTENT)
    _sudo(["chmod", "0755", str(target)])
