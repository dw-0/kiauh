# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
"""
DNS provider definitions for certbot DNS-01 issuance.

A provider is pure data describing how to drive its certbot plugin: the apt
package, the certbot flags, and the credentials-file fields. The certbot
command and credentials-file body are assembled generically from that data,
so adding a provider is a single dict entry. The credentials/propagation
flags are optional, leaving room for a future env/IAM-based provider (e.g.
Route53) that has no credentials file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CredField:
    """A single line of a certbot DNS plugin credentials (.ini) file."""

    ini_key: str
    prompt: str
    secret: bool = True
    default: Optional[str] = None


@dataclass(frozen=True)
class DnsProvider:
    """How to obtain a DNS-01 certificate through one certbot DNS plugin."""

    key: str
    display_name: str
    plugin_package: str
    plugin_flag: str
    credentials_fields: List[CredField]
    credentials_flag: Optional[str] = None
    propagation_flag: Optional[str] = None
    default_propagation: int = 30
    credentials_filename: Optional[str] = None


PROVIDERS: Dict[str, DnsProvider] = {
    "cloudflare": DnsProvider(
        key="cloudflare",
        display_name="Cloudflare",
        plugin_package="python3-certbot-dns-cloudflare",
        plugin_flag="--dns-cloudflare",
        credentials_flag="--dns-cloudflare-credentials",
        propagation_flag="--dns-cloudflare-propagation-seconds",
        default_propagation=30,
        credentials_filename="cloudflare.ini",
        credentials_fields=[
            CredField(
                ini_key="dns_cloudflare_api_token",
                prompt="Cloudflare API token (Zone:DNS:Edit)",
            ),
        ],
    ),
    "digitalocean": DnsProvider(
        key="digitalocean",
        display_name="DigitalOcean",
        plugin_package="python3-certbot-dns-digitalocean",
        plugin_flag="--dns-digitalocean",
        credentials_flag="--dns-digitalocean-credentials",
        propagation_flag="--dns-digitalocean-propagation-seconds",
        default_propagation=30,
        credentials_filename="digitalocean.ini",
        credentials_fields=[
            CredField(
                ini_key="dns_digitalocean_token",
                prompt="DigitalOcean API token (read & write)",
            ),
        ],
    ),
    "linode": DnsProvider(
        key="linode",
        display_name="Linode",
        plugin_package="python3-certbot-dns-linode",
        plugin_flag="--dns-linode",
        credentials_flag="--dns-linode-credentials",
        propagation_flag="--dns-linode-propagation-seconds",
        # Linode refreshes its DNS every 60s; the plugin default of 120 leaves
        # margin for that update to reach the authoritative servers.
        default_propagation=120,
        credentials_filename="linode.ini",
        credentials_fields=[
            CredField(ini_key="dns_linode_key", prompt="Linode API key"),
            CredField(
                ini_key="dns_linode_version",
                prompt="Linode API version",
                secret=False,
                default="4",
            ),
        ],
    ),
}


def build_certbot_command(
    provider: DnsProvider,
    fqdn: str,
    email: str,
    propagation_seconds: int,
    credentials_path: Optional[str] = None,
    force_renewal: bool = False,
) -> List[str]:
    """
    Assemble the ``certbot certonly`` argv for a DNS-01 issuance.

    The credentials/propagation flags are included only when the provider
    declares them (and, for credentials, a path is given), so a provider
    without a credentials file composes without special-casing. All flags are
    long form on purpose; the secret never appears here - only the path to the
    credentials file does.

    With ``force_renewal`` certbot runs a real DNS challenge instead of keeping
    an unexpired certificate: used when replacing credentials, so the new token
    is actually validated rather than silently accepted by --keep-until-expiring.
    """
    cmd: List[str] = ["sudo", "certbot", "certonly", provider.plugin_flag]
    if provider.credentials_flag and credentials_path:
        cmd += [provider.credentials_flag, credentials_path]
    if provider.propagation_flag:
        cmd += [provider.propagation_flag, str(propagation_seconds)]
    cmd += [
        "--domain",
        fqdn,
        "--non-interactive",
        "--agree-tos",
        "--email",
        email,
        # opt out of the EFF mailing list explicitly: with --non-interactive
        # certbot cannot ask, and we must not silently subscribe the user.
        "--no-eff-email",
        "--force-renewal" if force_renewal else "--keep-until-expiring",
    ]
    return cmd


def build_credentials_content(provider: DnsProvider, values: Dict[str, str]) -> str:
    """
    Render the INI credentials-file body for the provider from a mapping of
    ``ini_key -> value``. Only the provider's declared fields are written.

    Each value is stripped here - this is the single, deliberate point where a
    credential is normalized. ``get_secret_input`` returns the raw input, so
    trimming an accidental trailing newline from a paste happens at write time;
    DNS API tokens never carry significant leading/trailing whitespace.
    """
    lines = [
        f"{f.ini_key} = {values[f.ini_key].strip()}"
        for f in provider.credentials_fields
    ]
    return "\n".join(lines) + "\n"
