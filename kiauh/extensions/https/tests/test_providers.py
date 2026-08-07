# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import pytest
from extensions.https.providers import (
    PROVIDERS,
    CredField,
    DnsProvider,
    build_certbot_command,
    build_credentials_content,
)

SHORT_FLAGS = {"-d", "-m", "-n"}


def test_ships_expected_providers():
    assert set(PROVIDERS) >= {"cloudflare", "digitalocean", "linode"}


@pytest.mark.parametrize("key", list(PROVIDERS))
def test_every_provider_is_wellformed(key):
    provider = PROVIDERS[key]
    assert provider.key == key
    assert provider.display_name
    assert provider.plugin_package.startswith("python3-certbot-dns-")
    assert provider.plugin_flag.startswith("--dns-")
    assert provider.credentials_fields
    assert provider.default_propagation > 0


def test_build_certbot_command_cloudflare():
    cmd = build_certbot_command(
        PROVIDERS["cloudflare"],
        fqdn="printer.example.com",
        email="me@example.com",
        propagation_seconds=30,
        credentials_path="/root/.secrets/cloudflare.ini",
    )
    assert cmd[:3] == ["sudo", "certbot", "certonly"]
    assert "--dns-cloudflare" in cmd
    assert "--dns-cloudflare-credentials" in cmd
    assert "/root/.secrets/cloudflare.ini" in cmd
    assert "--dns-cloudflare-propagation-seconds" in cmd
    assert "30" in cmd
    assert cmd[cmd.index("--domain") + 1] == "printer.example.com"
    assert cmd[cmd.index("--email") + 1] == "me@example.com"
    assert "--non-interactive" in cmd
    assert "--agree-tos" in cmd
    assert "--keep-until-expiring" in cmd


@pytest.mark.parametrize("key", list(PROVIDERS))
def test_build_certbot_command_opts_out_of_eff_email(key):
    # running non-interactively, certbot must not be left to decide on the EFF
    # mailing-list subscription; --no-eff-email makes the opt-out explicit
    cmd = build_certbot_command(
        PROVIDERS[key], "p.example.com", "me@example.com", 30, "/x/creds.ini"
    )
    assert "--no-eff-email" in cmd


def test_build_certbot_command_keeps_cert_by_default():
    cmd = build_certbot_command(
        PROVIDERS["cloudflare"], "p.example.com", "me@example.com", 30, "/x/cf.ini"
    )
    assert "--keep-until-expiring" in cmd
    assert "--force-renewal" not in cmd


def test_build_certbot_command_force_renewal_swaps_keep_flag():
    # replacing credentials must validate the new token via a real renewal
    cmd = build_certbot_command(
        PROVIDERS["cloudflare"],
        "p.example.com",
        "me@example.com",
        30,
        "/x/cf.ini",
        force_renewal=True,
    )
    assert "--force-renewal" in cmd
    assert "--keep-until-expiring" not in cmd


def test_build_certbot_command_uses_only_long_flags():
    cmd = build_certbot_command(
        PROVIDERS["linode"], "p.example.com", "me@example.com", 120, "/x/linode.ini"
    )
    assert SHORT_FLAGS.isdisjoint(cmd)


def test_build_certbot_command_omits_optional_flags_when_provider_has_none():
    # a future env/IAM provider with no credentials/propagation flags must
    # still produce a valid command
    provider = DnsProvider(
        key="envprov",
        display_name="EnvProvider",
        plugin_package="python3-certbot-dns-envprov",
        plugin_flag="--dns-envprov",
        credentials_fields=[CredField(ini_key="x", prompt="x")],
        credentials_flag=None,
        propagation_flag=None,
        credentials_filename=None,
    )
    cmd = build_certbot_command(provider, "p.example.com", "me@example.com", 30, None)
    assert "--dns-envprov" in cmd
    assert not any(c.endswith("-credentials") for c in cmd)
    assert not any(c.endswith("-propagation-seconds") for c in cmd)
    assert "--domain" in cmd


def test_build_certbot_command_never_contains_a_secret_value():
    # the token lives only in the credentials file; the argv references the
    # file path, never the secret itself
    cmd = build_certbot_command(
        PROVIDERS["cloudflare"], "p.example.com", "me@example.com", 30, "/x/cf.ini"
    )
    assert "supersecrettoken" not in " ".join(cmd)


def test_build_credentials_content_single_field():
    body = build_credentials_content(
        PROVIDERS["cloudflare"], {"dns_cloudflare_api_token": "supersecrettoken"}
    )
    assert body == "dns_cloudflare_api_token = supersecrettoken\n"


def test_build_credentials_content_multi_field_linode():
    body = build_credentials_content(
        PROVIDERS["linode"],
        {"dns_linode_key": "abc123", "dns_linode_version": "4"},
    )
    assert body == "dns_linode_key = abc123\ndns_linode_version = 4\n"


def test_build_credentials_content_trims_whitespace():
    body = build_credentials_content(
        PROVIDERS["cloudflare"], {"dns_cloudflare_api_token": "  padded-token  "}
    )
    assert body == "dns_cloudflare_api_token = padded-token\n"
