# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch

import pytest
from extensions.https import LE_LIVE_DIR, RENEWAL_HOOK_DIR, SECRETS_DIR
from extensions.https.certbot import (
    backup_credentials,
    cert_paths,
    credentials_exist,
    credentials_match_provider,
    discard_credentials_backup,
    ensure_certbot,
    install_renew_hook,
    remove_credentials,
    restore_credentials,
    run_certbot,
    write_credentials,
)
from extensions.https.providers import PROVIDERS

TOKEN = "supersecret-cloudflare-token"


def _argv_list(mock_run):
    """All positional command lists passed to the mocked run()."""
    return [call.args[0] for call in mock_run.call_args_list]


def _flat_argv(mock_run):
    return [tok for argv in _argv_list(mock_run) for tok in argv]


# --------------------------------------------------------------------------- #
# cert_paths
# --------------------------------------------------------------------------- #
def test_cert_paths():
    full, key = cert_paths("printer.example.com")
    assert full == LE_LIVE_DIR.joinpath("printer.example.com", "fullchain.pem")
    assert key == LE_LIVE_DIR.joinpath("printer.example.com", "privkey.pem")


# --------------------------------------------------------------------------- #
# ensure_certbot
# --------------------------------------------------------------------------- #
def test_ensure_certbot_installs_missing():
    missing = ["certbot", "python3-certbot-dns-cloudflare"]
    with patch("extensions.https.certbot.check_package_install", return_value=missing):
        with patch("extensions.https.certbot.install_system_packages") as install:
            ensure_certbot(PROVIDERS["cloudflare"])
    install.assert_called_once()
    assert "certbot" in install.call_args.args[0]


def test_ensure_certbot_skips_when_present():
    with patch("extensions.https.certbot.check_package_install", return_value=[]):
        with patch("extensions.https.certbot.install_system_packages") as install:
            ensure_certbot(PROVIDERS["cloudflare"])
    install.assert_not_called()


# --------------------------------------------------------------------------- #
# write_credentials
# --------------------------------------------------------------------------- #
def test_write_credentials_uses_sudo_tee_and_locks_down_perms():
    with patch("extensions.https.certbot.run") as mock_run:
        target = write_credentials(
            PROVIDERS["cloudflare"],
            {"dns_cloudflare_api_token": TOKEN},
            "printer.example.com",
        )

    # the credentials file is named per certificate, not per provider
    assert target == SECRETS_DIR.joinpath("printer.example.com.ini")
    argvs = _argv_list(mock_run)
    # the secrets dir is created and locked to 700
    assert ["sudo", "mkdir", "-p", str(SECRETS_DIR)] in argvs
    assert ["sudo", "chmod", "700", str(SECRETS_DIR)] in argvs
    # the file is written via `sudo tee` and locked to 600
    tee = [a for a in argvs if a[:2] == ["sudo", "tee"]]
    assert tee == [["sudo", "tee", str(target)]]
    assert ["sudo", "chmod", "600", str(target)] in argvs


def test_write_credentials_passes_secret_via_stdin_only():
    with patch("extensions.https.certbot.run") as mock_run:
        write_credentials(
            PROVIDERS["cloudflare"],
            {"dns_cloudflare_api_token": TOKEN},
            "printer.example.com",
        )

    # the token reaches tee only through input=, never as a command argument
    assert TOKEN not in _flat_argv(mock_run)
    tee_call = next(
        c for c in mock_run.call_args_list if c.args[0][:2] == ["sudo", "tee"]
    )
    assert TOKEN.encode() in tee_call.kwargs["input"]


def test_write_credentials_never_logs_secret():
    creds = {"dns_cloudflare_api_token": TOKEN}
    with patch("extensions.https.certbot.run"):
        with patch("extensions.https.certbot.Logger") as logger:
            write_credentials(PROVIDERS["cloudflare"], creds, "printer.example.com")

    logged = " ".join(str(arg) for call in logger.method_calls for arg in call.args)
    assert TOKEN not in logged


def test_remove_credentials_uses_sudo_rm():
    with patch("extensions.https.certbot.run") as mock_run:
        remove_credentials(Path("/root/.secrets/cloudflare.ini"))
    assert mock_run.call_args.args[0] == [
        "sudo",
        "rm",
        "-f",
        "/root/.secrets/cloudflare.ini",
    ]


def test_write_credentials_requires_a_credentials_file():
    provider = PROVIDERS["cloudflare"].__class__(
        key="envprov",
        display_name="EnvProvider",
        plugin_package="python3-certbot-dns-envprov",
        plugin_flag="--dns-envprov",
        credentials_fields=PROVIDERS["cloudflare"].credentials_fields,
        credentials_filename=None,
    )
    with patch("extensions.https.certbot.run"):
        with pytest.raises(ValueError):
            write_credentials(
                provider, {"dns_cloudflare_api_token": TOKEN}, "printer.example.com"
            )


def test_credentials_exist_true_when_present():
    with patch("extensions.https.certbot.run") as mock_run:
        mock_run.return_value.returncode = 0  # `sudo test -f` -> found
        assert credentials_exist("printer.example.com") is True
    assert mock_run.call_args.args[0] == [
        "sudo",
        "test",
        "-f",
        str(SECRETS_DIR.joinpath("printer.example.com.ini")),
    ]


def test_credentials_exist_false_when_absent():
    with patch("extensions.https.certbot.run") as mock_run:
        mock_run.return_value.returncode = 1  # `sudo test -f` -> not found
        assert credentials_exist("printer.example.com") is False


def test_credentials_match_provider_true_when_key_present():
    with patch("extensions.https.certbot.run") as mock_run:
        mock_run.return_value.returncode = 0  # grep found the provider's key
        assert (
            credentials_match_provider("printer.example.com", PROVIDERS["cloudflare"])
            is True
        )
    argv = mock_run.call_args.args[0]
    assert argv[:3] == ["sudo", "grep", "-q"]
    # grep matches on the key NAME, never the secret value
    assert "dns_cloudflare_api_token" in argv
    assert str(SECRETS_DIR.joinpath("printer.example.com.ini")) in argv


def test_credentials_match_provider_false_when_key_absent():
    with patch("extensions.https.certbot.run") as mock_run:
        mock_run.return_value.returncode = 1  # a different provider's file
        assert (
            credentials_match_provider("printer.example.com", PROVIDERS["linode"])
            is False
        )


def test_backup_credentials_copies_to_bak():
    with patch("extensions.https.certbot.run") as mock_run:
        result = backup_credentials("printer.example.com")
    assert result == SECRETS_DIR.joinpath("printer.example.com.ini.bak")
    assert mock_run.call_args.args[0] == [
        "sudo",
        "cp",
        "-p",
        str(SECRETS_DIR.joinpath("printer.example.com.ini")),
        str(SECRETS_DIR.joinpath("printer.example.com.ini.bak")),
    ]


def test_restore_credentials_moves_backup_into_place():
    backup = SECRETS_DIR.joinpath("printer.example.com.ini.bak")
    with patch("extensions.https.certbot.run") as mock_run:
        restore_credentials(backup, "printer.example.com")
    assert mock_run.call_args.args[0] == [
        "sudo",
        "mv",
        str(backup),
        str(SECRETS_DIR.joinpath("printer.example.com.ini")),
    ]


def test_discard_credentials_backup_uses_rm():
    backup = SECRETS_DIR.joinpath("printer.example.com.ini.bak")
    with patch("extensions.https.certbot.run") as mock_run:
        discard_credentials_backup(backup)
    assert mock_run.call_args.args[0] == ["sudo", "rm", "-f", str(backup)]


def test_write_credentials_path_is_per_certificate():
    # two certificates with the same provider must not share a credentials file,
    # so issuing/removing one never clobbers another's renewal credentials
    with patch("extensions.https.certbot.run"):
        a = write_credentials(
            PROVIDERS["cloudflare"],
            {"dns_cloudflare_api_token": TOKEN},
            "a.example.com",
        )
        b = write_credentials(
            PROVIDERS["cloudflare"],
            {"dns_cloudflare_api_token": TOKEN},
            "b.example.com",
        )
    assert a == SECRETS_DIR.joinpath("a.example.com.ini")
    assert b == SECRETS_DIR.joinpath("b.example.com.ini")
    assert a != b


# --------------------------------------------------------------------------- #
# run_certbot
# --------------------------------------------------------------------------- #
def test_run_certbot_builds_expected_argv():
    with patch("extensions.https.certbot.run") as mock_run:
        run_certbot(
            PROVIDERS["cloudflare"],
            fqdn="printer.example.com",
            email="me@example.com",
            propagation_seconds=30,
            credentials_path=Path("/root/.secrets/cloudflare.ini"),
        )
    argv = mock_run.call_args.args[0]
    assert argv[:3] == ["sudo", "certbot", "certonly"]
    assert "--dns-cloudflare" in argv
    assert argv[argv.index("--domain") + 1] == "printer.example.com"
    assert "--non-interactive" in argv


def test_run_certbot_propagates_failure_without_touching_nginx():
    with patch(
        "extensions.https.certbot.run",
        side_effect=CalledProcessError(1, "certbot"),
    ) as mock_run:
        with pytest.raises(CalledProcessError):
            run_certbot(
                PROVIDERS["cloudflare"],
                "printer.example.com",
                "me@example.com",
                30,
                Path("/root/.secrets/cloudflare.ini"),
            )
    # only certbot was invoked; nothing reloaded nginx
    assert all("nginx" not in tok for tok in _flat_argv(mock_run))


# --------------------------------------------------------------------------- #
# install_renew_hook
# --------------------------------------------------------------------------- #
def test_install_renew_hook_writes_executable_reload_script():
    with patch("extensions.https.certbot.run") as mock_run:
        install_renew_hook()
    argvs = _argv_list(mock_run)
    assert ["sudo", "mkdir", "-p", str(RENEWAL_HOOK_DIR)] in argvs
    tee_call = next(
        c for c in mock_run.call_args_list if c.args[0][:2] == ["sudo", "tee"]
    )
    written = tee_call.kwargs["input"].decode()
    assert "systemctl reload nginx" in written
    target = tee_call.args[0][2]
    assert ["sudo", "chmod", "0755", target] in argvs
