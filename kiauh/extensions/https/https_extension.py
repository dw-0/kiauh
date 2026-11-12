# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError
from typing import Dict, List, Optional

from components.webui_client.base_data import BaseWebClient
from components.webui_client.client_utils import (
    get_existing_clients,
    get_nginx_config_list,
    get_nginx_listen_port,
)
from core.constants import NGINX_SITES_ENABLED
from core.logger import DialogType, Logger
from core.settings.kiauh_settings import KiauhSettings
from extensions.base_extension import BaseExtension
from extensions.https import EMAIL_REGEX, FQDN_REGEX
from extensions.https.certbot import (
    LETSENCRYPT_LOG,
    backup_credentials,
    cert_paths,
    credentials_exist,
    credentials_file,
    credentials_match_provider,
    discard_credentials_backup,
    ensure_certbot,
    install_renew_hook,
    remove_credentials,
    restore_credentials,
    run_certbot,
    write_credentials,
)
from extensions.https.nginx_https import (
    AlreadyHttpsError,
    build_http_config,
    build_https_config,
    extract_fqdn,
    extract_redirect_port,
)
from extensions.https.nginx_ops import (
    backup_site,
    discard_backup,
    nginx_config_test,
    reload_nginx,
    restore_site,
    write_site,
)
from extensions.https.providers import PROVIDERS, DnsProvider
from utils.input_utils import (
    get_confirm,
    get_secret_input,
    get_selection_input,
    get_string_input,
)
from utils.nginx_utils import config_enables_https, listen_ports
from utils.sys_utils import get_distro_info

# certbot is packaged for Debian/Ubuntu and their derivatives (apt). get_distro_info
# returns the raw distro ID (it only remaps raspbian -> debian), so accept the
# common Debian/Ubuntu-derived IDs explicitly. A fully robust check would consult
# ID_LIKE from /etc/os-release, which get_distro_info does not expose today.
SUPPORTED_DISTRO_IDS = {
    "debian",
    "ubuntu",
    "raspbian",
    "armbian",
    "linuxmint",
    "pop",
    "neon",
    "zorin",
    "elementary",
    "devuan",
}
HTTPS_PORT = 443


# noinspection PyMethodMayBeStatic
class HttpsExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        if not self._distro_supported():
            return

        client = self._select_client()
        if client is None:
            return

        site: Path = client.nginx_config
        current = self._read_site(site)
        if current is None:
            return

        # The client dir can exist while its sites-enabled symlink was removed;
        # rewriting the unloaded sites-available file would pass nginx -t yet
        # leave HTTPS unserved. Require the site to be enabled first.
        if not NGINX_SITES_ENABLED.joinpath(client.name).exists():
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    f"The nginx site for {client.display_name} is not enabled.",
                    "Enable it (symlink in sites-enabled) before enabling HTTPS.",
                ],
            )
            return

        if config_enables_https(current):
            Logger.print_dialog(
                DialogType.INFO,
                [f"HTTPS is already enabled for {client.display_name}."],
            )
            return

        if self._port_443_in_use():
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Port 443 is already in use by another nginx site.",
                    "Disable HTTPS there or remove the conflict first.",
                ],
            )
            return

        provider = self._select_provider()
        # certbot canonicalizes the lineage to lowercase, so normalize here too:
        # otherwise cert_paths() for "Printer.Example.com" points at a directory
        # certbot never created and nginx -t fails after a successful issuance.
        fqdn = get_string_input(
            "Printer FQDN (e.g. printer.example.com)", regex=FQDN_REGEX
        ).lower()

        # Build the rewritten config now, before any package install or
        # certificate issuance. A site we cannot rewrite (malformed, no server
        # block) must fail here - never after a certificate has been issued.
        # The redirect block keeps the port the site is currently served on, so
        # enabling and later disabling HTTPS round-trips to the same port.
        redirect_port = get_nginx_listen_port(site)
        if redirect_port is None:
            # Guessing a default here would silently move the site to a wrong
            # port and break the round-trip on disable; abort instead.
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    f"Could not determine the listen port from {site}.",
                    "The site was left unchanged.",
                ],
            )
            return
        new_config = self._build_https_config(current, fqdn, redirect_port)
        if new_config is None:
            return

        email = get_string_input("Let's Encrypt contact email", regex=EMAIL_REGEX)
        propagation = provider.default_propagation

        # Prefer reusing the credentials of a certificate kept from a previous
        # enable: re-issuing a still-valid cert is a no-op (--keep-until-expiring)
        # that never validates a freshly typed token, so overwriting the working
        # file could silently break renewal. Only offer reuse when the saved file
        # actually matches the selected provider (its INI is plugin-specific);
        # declining, or a provider change, falls through to writing new ones.
        creds_existed = credentials_exist(fqdn)
        reuse_credentials = bool(
            creds_existed
            and credentials_match_provider(fqdn, provider)
            and get_confirm(
                f"Saved credentials for {fqdn} found. Reuse them?",
                default_choice=True,
            )
        )
        values: Dict[str, str] = (
            {} if reuse_credentials else self._prompt_credentials(provider)
        )

        self._print_summary(
            client, provider, fqdn, reusing_credentials=reuse_credentials
        )
        if not get_confirm("Continue?", default_choice=True):
            return

        try:
            ensure_certbot(provider)
        except CalledProcessError:
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Could not install certbot or the DNS plugin.",
                    "Check the network and apt, then try again.",
                    "nginx was left unchanged.",
                ],
            )
            return

        # Replacing existing credentials: back the working file up first so a
        # failed issuance can restore it. If the backup cannot be made, abort
        # rather than overwrite an unrecoverable working file.
        replacing = creds_existed and not reuse_credentials
        creds_backup: Optional[Path] = None
        if replacing:
            try:
                creds_backup = backup_credentials(fqdn)
            except CalledProcessError:
                Logger.print_dialog(
                    DialogType.ERROR,
                    [
                        "Could not back up the existing DNS credentials.",
                        "Aborting so the working credentials are not overwritten.",
                        "nginx was left unchanged.",
                    ],
                )
                return

        # Write the token (unless reusing) and issue the certificate. Treated as
        # one unit: until run_certbot succeeds no certificate references these
        # credentials, so a failure here can safely undo the credentials change.
        # Replacing credentials forces a real renewal so the new token is
        # validated, not silently kept by --keep-until-expiring.
        try:
            creds_path = (
                credentials_file(fqdn)
                if reuse_credentials
                else write_credentials(provider, values, fqdn)
            )
            run_certbot(
                provider, fqdn, email, propagation, creds_path, force_renewal=replacing
            )
        except CalledProcessError:
            self._undo_credentials(reuse_credentials, creds_existed, creds_backup, fqdn)
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Failed to obtain the certificate.",
                    "Check the DNS provider token (scope and validity) and that "
                    "sudo and apt are available.",
                    f"Full details: {LETSENCRYPT_LOG} (root only).",
                    "nginx was left unchanged.",
                ],
            )
            return

        # The certificate now exists and its renewal config references creds_path,
        # so the credentials must stay from here on - drop the backup.
        if creds_backup is not None:
            try:
                discard_credentials_backup(creds_backup)
            except CalledProcessError:
                pass

        # Installing the auto-reload hook is non-fatal: the certificate is issued
        # and HTTPS will work; the (idempotent) hook can be added on a re-run.
        try:
            install_renew_hook()
        except CalledProcessError:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "The certificate was issued, but installing the nginx "
                    "auto-reload hook for renewals failed.",
                    "HTTPS will still be enabled; re-run 'Enable HTTPS' later to "
                    "add the hook.",
                ],
            )

        if not self._apply_nginx_config(site, new_config):
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            [
                f"HTTPS enabled for {client.display_name}!",
                f"Open it now on: https://{fqdn}",
                "\n\n",
                "Disable HTTPS before using 'Reconfigure Listen Port'.",
                "If a cross-origin client is blocked after the switch, add "
                f"'*://{fqdn}' to cors_domains in moonraker.conf.",
            ],
            center_content=True,
        )

    def remove_extension(self, **kwargs) -> None:
        client = self._select_client()
        if client is None:
            return

        site: Path = client.nginx_config
        current = self._read_site(site)
        if current is None:
            return

        if not config_enables_https(current):
            Logger.print_dialog(
                DialogType.INFO,
                [f"HTTPS is not enabled for {client.display_name}."],
            )
            return

        fqdn = extract_fqdn(current)
        # restore the port the site was actually on (recorded in the redirect
        # block). Fall back to KIAUH settings if it cannot be read, or if it
        # comes back as 443 - a site configured outside this extension may not
        # have our redirect/TLS layout, and rebuilding plain HTTP on 443 would
        # be wrong.
        port = extract_redirect_port(current)
        if port is None or port == HTTPS_PORT:
            port = int(KiauhSettings().get(client.name, "port"))

        # reverse the install transform instead of regenerating from the stock
        # template, so any customizations carried into the TLS block survive
        http_config = build_http_config(current, port)

        Logger.print_status(
            f"Restoring plain HTTP config for {client.display_name} ..."
        )
        if not self._apply_nginx_config(site, http_config):
            return

        cleanup = [
            f"HTTPS disabled for {client.display_name}; it now serves plain HTTP.",
            "The certificate and DNS credentials were kept. To remove them:",
        ]
        if fqdn is not None:
            cleanup.append(f"  sudo certbot delete --cert-name {fqdn}")
            cleanup.append(f"  sudo rm /root/.secrets/{fqdn}.ini")
        else:
            cleanup.append("  sudo rm /root/.secrets/<fqdn>.ini")
        Logger.print_dialog(DialogType.ATTENTION, cleanup)

    # --------------------------------------------------------------------- #
    # helpers
    # --------------------------------------------------------------------- #
    def _port_443_in_use(self) -> bool:
        """
        True if any enabled nginx site already has an active listen on port 443
        (TLS or plain). Scans every listen directive of every enabled config -
        not just the last listen per file - so a 443 directive followed by
        another listen, or a non-TLS ``listen 443;``, is still detected.

        Limitation: this only inspects nginx's own enabled sites. A non-nginx
        daemon holding port 443 (Caddy, Apache, ...) is not seen here, and since
        a reload can succeed without the socket actually binding, the install
        could report success while HTTPS is not live. Detecting that reliably
        needs OS-level socket inspection, which is out of scope for this helper.
        """
        for cfg in get_nginx_config_list():
            try:
                if HTTPS_PORT in listen_ports(cfg.read_text()):
                    return True
            except OSError:
                continue
        return False

    def _distro_supported(self) -> bool:
        try:
            distro_id, _ = get_distro_info()
        except (ValueError, OSError, CalledProcessError):
            # get_distro_info shells out via `cat /etc/os-release`; a missing
            # file makes it exit non-zero (CalledProcessError), which is not an
            # OSError - treat any lookup failure as "unsupported", not a crash.
            distro_id = ""
        if distro_id in SUPPORTED_DISTRO_IDS:
            return True
        Logger.print_dialog(
            DialogType.ERROR,
            ["This feature requires a Debian-based system (apt + certbot)."],
        )
        return False

    def _select_client(self) -> Optional[BaseWebClient]:
        clients: List[BaseWebClient] = get_existing_clients()
        if not clients:
            Logger.print_dialog(
                DialogType.ERROR,
                ["No Mainsail or Fluidd installation was found."],
            )
            return None
        if len(clients) == 1:
            return clients[0]

        options = {str(i): c for i, c in enumerate(clients, start=1)}
        Logger.print_dialog(
            DialogType.INFO,
            ["Multiple clients found. Select the one to enable HTTPS for:"]
            + [f"{i}) {c.display_name}" for i, c in options.items()],
        )
        choice = get_selection_input("Select client", list(options.keys()))
        return options[choice]

    def _select_provider(self) -> DnsProvider:
        options = {str(i): key for i, key in enumerate(PROVIDERS, start=1)}
        Logger.print_dialog(
            DialogType.INFO,
            ["Select your DNS provider (its API hosts the DNS-01 challenge):"]
            + [f"{i}) {PROVIDERS[key].display_name}" for i, key in options.items()],
        )
        choice = get_selection_input("Select DNS provider", list(options.keys()))
        return PROVIDERS[options[choice]]

    def _prompt_credentials(self, provider: DnsProvider) -> Dict[str, str]:
        values: Dict[str, str] = {}
        for field in provider.credentials_fields:
            if field.secret:
                values[field.ini_key] = get_secret_input(field.prompt)
            else:
                # non-secret fields (zone ids, account names, API versions) may
                # contain '-', '_', '.' or '/', so do not restrict to alnum
                values[field.ini_key] = get_string_input(
                    field.prompt,
                    allow_special_chars=True,
                    default=field.default,
                )
        return values

    def _undo_credentials(
        self,
        reuse: bool,
        existed: bool,
        backup: Optional[Path],
        fqdn: str,
    ) -> None:
        """
        Roll back the credentials change after a FAILED issuance, best-effort so
        a failing cleanup never masks the real error.

        * reuse: nothing was changed, nothing to undo.
        * a backup exists (we replaced a working file): restore it, so the
          retained certificate keeps renewing with its known-good credentials.
        * first-time write (no prior file): remove the token we wrote.
        * replaced a file we could not back up: leave the new file - it is the
          only one left, so deleting it would strand the retained certificate.
        """
        try:
            if reuse:
                return
            if backup is not None:
                restore_credentials(backup, fqdn)
            elif not existed:
                remove_credentials(credentials_file(fqdn))
        except CalledProcessError:
            pass

    def _print_summary(
        self,
        client: BaseWebClient,
        provider: DnsProvider,
        fqdn: str,
        reusing_credentials: bool = False,
    ) -> None:
        lines = [
            "About to request a certificate and enable HTTPS:",
            f"● Client:    {client.display_name}",
            f"● Domain:    {fqdn}",
            f"● Provider:  {provider.display_name}",
            "\n\n",
        ]
        if reusing_credentials:
            lines.append(
                f"Existing credentials for {fqdn} are reused; no token is needed."
            )
        else:
            cred_file = (
                f"{fqdn}.ini" if provider.credentials_filename else "(environment)"
            )
            lines.append(
                f"The API token is stored only in /root/.secrets/{cred_file} "
                "(chmod 600) and never in KIAUH config or git."
            )
        Logger.print_dialog(DialogType.WARNING, lines)

    def _read_site(self, site: Path) -> Optional[str]:
        try:
            return site.read_text()
        except OSError:
            Logger.print_dialog(
                DialogType.ERROR,
                [f"Could not read the nginx site at {site}."],
            )
            return None

    def _build_https_config(
        self, current: str, fqdn: str, redirect_port: int
    ) -> Optional[str]:
        """
        Build the rewritten HTTPS config from the current site, or return None
        (after a clean error dialog) if the site cannot be rewritten. Pure - no
        I/O - so it is safe to call before any certificate is issued.
        """
        full, key = cert_paths(fqdn)
        try:
            config: str = build_https_config(
                current, fqdn, str(full), str(key), redirect_port=redirect_port
            )
            return config
        except (ValueError, AlreadyHttpsError):
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Could not rewrite the existing nginx site for HTTPS.",
                    "The site was left unchanged.",
                ],
            )
            return None

    def _apply_nginx_config(self, site: Path, new_config: str) -> bool:
        """
        Apply a rewritten nginx site transactionally (used for both enabling and
        disabling HTTPS): back up, write, validate, then reload - or restore the
        backup if nginx -t fails or any privileged step errors. Returns True only
        when the new config is live and valid.
        """
        try:
            backup = backup_site(site)
        except CalledProcessError:
            # the backup itself failed; nothing was written, so leave the live
            # site as-is rather than crash or restore an unrelated stale backup.
            Logger.print_dialog(
                DialogType.ERROR,
                ["Could not back up the nginx site; it was left unchanged."],
            )
            return False

        try:
            write_site(site, new_config)
            if not nginx_config_test():
                Logger.print_error("nginx rejected the new config; reverting ...")
                restore_site(backup, site)
                reload_nginx()
                discard_backup(backup)
                Logger.print_dialog(
                    DialogType.ERROR,
                    [
                        "The generated config failed nginx -t. Reverted to the "
                        "previous site."
                    ],
                )
                return False
            reload_nginx()
        except CalledProcessError:
            # a privileged step after the backup (write/test/reload/restore)
            # shells out with check=True; on failure restore THIS transaction's
            # backup - not whatever .bak happens to be on disk - and surface one
            # clean error rather than crash or leave a half-applied config.
            self._revert_failed_apply(backup, site)
            return False

        # the new config is live and validated. Dropping the backup is best-
        # effort cleanup: a failing 'rm' must NOT roll back the change just
        # committed, so its error is swallowed here, not raised into the revert.
        try:
            discard_backup(backup)
        except CalledProcessError:
            pass
        return True

    def _revert_failed_apply(self, backup: Path, site: Path) -> None:
        """
        Restore from the backup taken by THIS apply call. The backup is dropped
        ONLY after the restore succeeds, so a failed restore keeps the only
        recovery copy instead of leaving a half-applied config with no backup.
        """
        try:
            restore_site(backup, site)
        except CalledProcessError:
            # the restore itself failed - keep the backup as the only recovery
            # copy and say so honestly rather than claim a clean rollback.
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Failed to apply the nginx config and could not restore the "
                    "previous site automatically.",
                    f"A backup of the previous site is kept at {backup}.",
                ],
            )
            return

        # the previous site is back on disk; reload it and drop the now-redundant
        # backup, both best-effort so a secondary failure is not fatal.
        try:
            reload_nginx()
        except CalledProcessError:
            pass
        try:
            discard_backup(backup)
        except CalledProcessError:
            pass
        Logger.print_dialog(
            DialogType.ERROR,
            ["Failed to apply the nginx config; the previous site was restored."],
        )
