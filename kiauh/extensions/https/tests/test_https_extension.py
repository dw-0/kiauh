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
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from extensions.https.certbot import credentials_file
from extensions.https.https_extension import HttpsExtension
from extensions.https.nginx_https import build_https_config
from extensions.https.providers import CredField, DnsProvider
from utils.nginx_utils import config_enables_https

MODULE = "extensions.https.https_extension"
FQDN = "printer.example.com"
FULLCHAIN = f"/etc/letsencrypt/live/{FQDN}/fullchain.pem"
PRIVKEY = f"/etc/letsencrypt/live/{FQDN}/privkey.pem"


@pytest.fixture()
def env(monkeypatch, tmp_path, http_config_text):
    """Patch every privileged seam and return the mocks plus a fake client."""
    site = tmp_path.joinpath("mainsail")
    site.write_text(http_config_text)

    # a fake sites-enabled dir with the client's site present, so the
    # "is the site enabled?" guard passes by default
    sites_enabled = tmp_path.joinpath("sites-enabled")
    sites_enabled.mkdir()
    sites_enabled.joinpath("mainsail").write_text("")
    monkeypatch.setattr(f"{MODULE}.NGINX_SITES_ENABLED", sites_enabled)

    client = SimpleNamespace(
        name="mainsail",
        display_name="Mainsail",
        nginx_config=site,
        client_dir=Path("/home/pi/mainsail"),
    )

    def fake_backup(s: Path) -> Path:
        bak = Path(str(s) + ".kiauh.bak")
        bak.write_text(Path(s).read_text())
        return bak

    def fake_write_site(s: Path, content: str) -> None:
        Path(s).write_text(content)

    def fake_restore(bak: Path, s: Path) -> None:
        Path(s).write_text(Path(bak).read_text())

    def fake_discard(bak: Path) -> None:
        Path(bak).unlink(missing_ok=True)

    mocks = SimpleNamespace(
        site=site,
        sites_enabled=sites_enabled,
        client=client,
        get_distro_info=MagicMock(return_value=("debian", "12")),
        get_existing_clients=MagicMock(return_value=[client]),
        get_nginx_config_list=MagicMock(return_value=[]),
        ensure_certbot=MagicMock(),
        write_credentials=MagicMock(return_value=Path("/root/.secrets/cloudflare.ini")),
        remove_credentials=MagicMock(),
        credentials_exist=MagicMock(return_value=False),
        credentials_match_provider=MagicMock(return_value=True),
        backup_credentials=MagicMock(
            return_value=Path("/root/.secrets/printer.example.com.ini.bak")
        ),
        restore_credentials=MagicMock(),
        discard_credentials_backup=MagicMock(),
        run_certbot=MagicMock(),
        install_renew_hook=MagicMock(),
        cert_paths=MagicMock(return_value=(Path(FULLCHAIN), Path(PRIVKEY))),
        backup_site=MagicMock(side_effect=fake_backup),
        write_site=MagicMock(side_effect=fake_write_site),
        restore_site=MagicMock(side_effect=fake_restore),
        discard_backup=MagicMock(side_effect=fake_discard),
        nginx_config_test=MagicMock(return_value=True),
        reload_nginx=MagicMock(),
        get_string_input=MagicMock(side_effect=[FQDN, "me@example.com"]),
        get_secret_input=MagicMock(return_value="secret-token"),
        get_selection_input=MagicMock(return_value="1"),
        get_confirm=MagicMock(return_value=True),
        settings=MagicMock(),
    )
    mocks.settings.return_value.get.return_value = 80

    monkeypatch.setattr(f"{MODULE}.get_distro_info", mocks.get_distro_info)
    monkeypatch.setattr(f"{MODULE}.get_existing_clients", mocks.get_existing_clients)
    monkeypatch.setattr(f"{MODULE}.get_nginx_config_list", mocks.get_nginx_config_list)
    monkeypatch.setattr(f"{MODULE}.ensure_certbot", mocks.ensure_certbot)
    monkeypatch.setattr(f"{MODULE}.write_credentials", mocks.write_credentials)
    monkeypatch.setattr(f"{MODULE}.remove_credentials", mocks.remove_credentials)
    monkeypatch.setattr(f"{MODULE}.credentials_exist", mocks.credentials_exist)
    monkeypatch.setattr(
        f"{MODULE}.credentials_match_provider", mocks.credentials_match_provider
    )
    monkeypatch.setattr(f"{MODULE}.backup_credentials", mocks.backup_credentials)
    monkeypatch.setattr(f"{MODULE}.restore_credentials", mocks.restore_credentials)
    monkeypatch.setattr(
        f"{MODULE}.discard_credentials_backup", mocks.discard_credentials_backup
    )
    monkeypatch.setattr(f"{MODULE}.run_certbot", mocks.run_certbot)
    monkeypatch.setattr(f"{MODULE}.install_renew_hook", mocks.install_renew_hook)
    monkeypatch.setattr(f"{MODULE}.cert_paths", mocks.cert_paths)
    monkeypatch.setattr(f"{MODULE}.backup_site", mocks.backup_site)
    monkeypatch.setattr(f"{MODULE}.write_site", mocks.write_site)
    monkeypatch.setattr(f"{MODULE}.restore_site", mocks.restore_site)
    monkeypatch.setattr(f"{MODULE}.discard_backup", mocks.discard_backup)
    monkeypatch.setattr(f"{MODULE}.nginx_config_test", mocks.nginx_config_test)
    monkeypatch.setattr(f"{MODULE}.reload_nginx", mocks.reload_nginx)
    monkeypatch.setattr(f"{MODULE}.get_string_input", mocks.get_string_input)
    monkeypatch.setattr(f"{MODULE}.get_secret_input", mocks.get_secret_input)
    monkeypatch.setattr(f"{MODULE}.get_selection_input", mocks.get_selection_input)
    monkeypatch.setattr(f"{MODULE}.get_confirm", mocks.get_confirm)
    monkeypatch.setattr(f"{MODULE}.KiauhSettings", mocks.settings)
    return mocks


def _https_fixture(http_config_text: str) -> str:
    result: str = build_https_config(http_config_text, FQDN, FULLCHAIN, PRIVKEY)
    return result


# --------------------------------------------------------------------------- #
# install_extension
# --------------------------------------------------------------------------- #
def test_install_happy_path_writes_https_config(env):
    HttpsExtension({}).install_extension()

    written = env.site.read_text()
    assert config_enables_https(written)
    assert f"return 301 https://{FQDN}$request_uri;" in written
    assert f"ssl_certificate {FULLCHAIN};" in written
    env.run_certbot.assert_called_once()
    env.install_renew_hook.assert_called_once()
    env.reload_nginx.assert_called_once()
    # the backup is cleaned up once the new config is live
    env.discard_backup.assert_called_once()
    assert not Path(str(env.site) + ".kiauh.bak").exists()


def test_install_aborts_on_malformed_site_before_issuing_cert(env):
    # a site with no parseable server block must fail BEFORE certbot runs
    env.site.write_text("this is not a valid nginx site\n")
    HttpsExtension({}).install_extension()

    env.ensure_certbot.assert_not_called()
    env.run_certbot.assert_not_called()
    env.backup_site.assert_not_called()
    assert env.site.read_text() == "this is not a valid nginx site\n"


def test_install_aborts_when_no_client(env, http_config_text):
    env.get_existing_clients.return_value = []
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_aborts_on_unsupported_distro(env, http_config_text):
    env.get_distro_info.return_value = ("arch", "")
    HttpsExtension({}).install_extension()

    env.get_existing_clients.assert_not_called()
    env.run_certbot.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_skips_when_already_https(env, http_config_text):
    env.site.write_text(_https_fixture(http_config_text))
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_not_called()


def test_install_lowercases_the_fqdn(env):
    # certbot canonicalizes to lowercase; an uppercase FQDN would otherwise
    # yield a cert path that does not exist and fail nginx -t after issuance
    env.get_string_input.side_effect = ["Printer.Example.COM", "me@example.com"]
    HttpsExtension({}).install_extension()

    written = env.site.read_text()
    assert "printer.example.com" in written
    assert "Printer.Example.COM" not in written


def test_install_aborts_when_site_not_enabled(env, http_config_text):
    # the sites-enabled symlink was removed; rewriting the unloaded site would
    # falsely report success, so installation must abort before issuing a cert
    env.sites_enabled.joinpath("mainsail").unlink()
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_not_called()
    env.backup_site.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_aborts_on_443_conflict(env, http_config_text, tmp_path):
    # another enabled site already listens on 443, even though it is not the
    # last listen in its file - the scan must still see it
    other = tmp_path.joinpath("other")
    other.write_text("server {\n    listen 443 ssl;\n    listen 9000;\n}\n")
    env.get_nginx_config_list.return_value = [other]
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_reuses_existing_credentials_on_reenable(env):
    # re-enabling a cert kept from a previous enable must reuse the working
    # credentials (not prompt for or overwrite them) and run certbot against the
    # existing file - overwriting could break renewal of the still-valid cert
    env.credentials_exist.return_value = True

    HttpsExtension({}).install_extension()

    env.get_secret_input.assert_not_called()  # no token prompt on re-enable
    env.write_credentials.assert_not_called()  # the working file is left as-is
    env.run_certbot.assert_called_once()
    assert env.run_certbot.call_args.args[4] == credentials_file(FQDN)


def test_install_replaces_credentials_when_user_declines_reuse(env):
    # if the saved token was rotated or the provider changed, declining reuse
    # must prompt for and write fresh credentials (not a dead end)
    env.credentials_exist.return_value = True
    env.get_confirm.side_effect = [False, True]  # don't reuse, then continue

    HttpsExtension({}).install_extension()

    env.get_secret_input.assert_called()  # prompted for a new token
    env.write_credentials.assert_called_once()  # fresh credentials written
    env.run_certbot.assert_called_once()


def test_install_does_not_offer_reuse_for_mismatched_provider(env):
    # saved credentials belong to a different DNS provider; reuse must not be
    # offered and the user is prompted for credentials for the new provider
    env.credentials_exist.return_value = True
    env.credentials_match_provider.return_value = False

    HttpsExtension({}).install_extension()

    env.get_secret_input.assert_called()  # prompted for new credentials
    env.write_credentials.assert_called_once()
    # the reuse question is never asked - only the final "Continue?"
    assert env.get_confirm.call_count == 1


def test_install_forces_renewal_when_replacing_credentials(env):
    # replacing credentials must force a real renewal so the new token is
    # validated, not silently kept by --keep-until-expiring
    env.credentials_exist.return_value = True
    env.get_confirm.side_effect = [False, True]  # don't reuse (replace), continue

    HttpsExtension({}).install_extension()

    assert env.run_certbot.call_args.kwargs.get("force_renewal") is True


def test_install_aborts_when_backup_fails_on_replace(env, http_config_text):
    # if the working credentials cannot be backed up, abort rather than
    # overwrite an unrecoverable file
    env.credentials_exist.return_value = True
    env.get_confirm.side_effect = [False, True]  # replace
    env.backup_credentials.side_effect = CalledProcessError(1, "cp")

    HttpsExtension({}).install_extension()

    env.write_credentials.assert_not_called()
    env.run_certbot.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_replace_failure_restores_existing_credentials(env):
    # declining reuse to replace credentials, then a failed issuance, must
    # restore the previous working file - the retained cert renews with it
    backup = Path("/root/.secrets/printer.example.com.ini.bak")
    env.credentials_exist.return_value = True
    env.backup_credentials.return_value = backup
    env.get_confirm.side_effect = [False, True]  # don't reuse, then continue
    env.run_certbot.side_effect = CalledProcessError(1, "certbot")

    HttpsExtension({}).install_extension()  # must not raise

    env.restore_credentials.assert_called_once_with(backup, FQDN)
    env.remove_credentials.assert_not_called()


def test_install_reenable_failure_does_not_touch_existing_credentials(env):
    # a failed re-enable must NOT remove the existing credentials - they belong
    # to a certificate that is still renewing
    env.credentials_exist.return_value = True
    env.run_certbot.side_effect = CalledProcessError(1, "certbot")

    HttpsExtension({}).install_extension()  # must not raise

    env.remove_credentials.assert_not_called()
    env.write_credentials.assert_not_called()


def test_install_leaves_nginx_untouched_when_cert_fails(env, http_config_text):
    env.run_certbot.side_effect = CalledProcessError(1, "certbot")
    HttpsExtension({}).install_extension()

    env.backup_site.assert_not_called()
    env.write_site.assert_not_called()
    env.reload_nginx.assert_not_called()
    # the token file written before issuance is cleaned up on the aborted path,
    # via the FQDN's deterministic path (covers a partial write that never
    # returned a path)
    env.remove_credentials.assert_called_once_with(credentials_file(FQDN))
    assert env.site.read_text() == http_config_text


def test_install_survives_credentials_write_failure(env, http_config_text):
    # the first sudo after confirmation (writing the token) can fail on an
    # expired/declined sudo password; the menu must not crash and nginx and
    # certbot must be left untouched
    env.write_credentials.side_effect = CalledProcessError(1, "tee")
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_not_called()
    env.install_renew_hook.assert_not_called()
    env.backup_site.assert_not_called()
    env.write_site.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_keeps_going_when_renew_hook_fails(env):
    # the cert is issued but the (non-fatal) renewal hook fails; the credentials
    # the issued cert renews with must be kept and HTTPS still applied
    env.install_renew_hook.side_effect = CalledProcessError(1, "tee")
    HttpsExtension({}).install_extension()

    env.run_certbot.assert_called_once()
    env.remove_credentials.assert_not_called()  # the issued cert references them
    env.write_site.assert_called_once()  # HTTPS is still applied
    assert config_enables_https(env.site.read_text())


def test_install_aborts_cleanly_when_certbot_install_fails(env, http_config_text):
    env.ensure_certbot.side_effect = CalledProcessError(1, "apt-get")
    HttpsExtension({}).install_extension()

    # apt failure must not crash the menu, write credentials or touch nginx
    env.write_credentials.assert_not_called()
    env.run_certbot.assert_not_called()
    env.backup_site.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_redirect_block_keeps_current_http_port(env, http_config_text):
    custom = http_config_text.replace("listen 80;", "listen 8080;").replace(
        "listen [::]:80;", "listen [::]:8080;"
    )
    env.site.write_text(custom)
    HttpsExtension({}).install_extension()

    redirect_block = env.site.read_text().split("listen 443 ssl")[0]
    assert "listen 8080;" in redirect_block
    assert "listen 80;" not in redirect_block


def test_install_rolls_back_when_nginx_test_fails(env, http_config_text):
    env.nginx_config_test.return_value = False
    HttpsExtension({}).install_extension()

    env.restore_site.assert_called_once()
    # the site is back to the original plain-HTTP config
    assert env.site.read_text() == http_config_text
    assert not config_enables_https(env.site.read_text())
    # the backup is discarded even on the rollback path
    env.discard_backup.assert_called_once()
    assert not Path(str(env.site) + ".kiauh.bak").exists()


def test_install_aborts_when_listen_port_unknown(env, http_config_text, monkeypatch):
    # an unreadable listen port means a non-standard site; guessing port 80
    # would break the HTTP<->HTTPS round-trip, so installation must abort
    monkeypatch.setattr(f"{MODULE}.get_nginx_listen_port", MagicMock(return_value=None))
    HttpsExtension({}).install_extension()

    env.ensure_certbot.assert_not_called()
    env.run_certbot.assert_not_called()
    env.write_site.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_reverts_when_a_privileged_step_raises(env, http_config_text):
    # reload after writing the new config fails; install must restore the
    # original site and never propagate the CalledProcessError
    env.reload_nginx.side_effect = CalledProcessError(1, "systemctl reload nginx")
    HttpsExtension({}).install_extension()

    assert env.site.read_text() == http_config_text
    env.restore_site.assert_called()
    assert not Path(str(env.site) + ".kiauh.bak").exists()


def test_install_survives_backup_failure(env, http_config_text):
    # even the first privileged step (backup) can fail; install must surface a
    # clean error and leave the original site untouched
    env.backup_site.side_effect = CalledProcessError(1, "cp")
    HttpsExtension({}).install_extension()

    assert env.site.read_text() == http_config_text
    env.write_site.assert_not_called()


def test_install_keeps_https_when_backup_cleanup_fails(env):
    # dropping the backup after a successful reload is best-effort cleanup; its
    # failure must NOT roll back the HTTPS config that is already live
    env.discard_backup.side_effect = CalledProcessError(1, "rm")
    HttpsExtension({}).install_extension()

    assert config_enables_https(env.site.read_text())
    env.restore_site.assert_not_called()


def test_install_keeps_backup_when_restore_fails(env):
    # the new config fails nginx -t AND restoring the backup also fails; the
    # backup must be kept (not discarded) so manual recovery is still possible
    env.nginx_config_test.return_value = False
    env.restore_site.side_effect = CalledProcessError(1, "cp")

    HttpsExtension({}).install_extension()  # must not raise

    env.discard_backup.assert_not_called()
    assert Path(str(env.site) + ".kiauh.bak").exists()


def test_install_does_not_restore_stale_backup_on_backup_failure(env, http_config_text):
    # a stale .bak from a previous failed run must NOT be restored when the
    # current backup step fails before creating its own
    stale = Path(str(env.site) + ".kiauh.bak")
    stale.write_text("STALE OLD CONFIG\n")
    env.backup_site.side_effect = CalledProcessError(1, "cp")

    HttpsExtension({}).install_extension()

    # the live site is untouched - not overwritten with the stale backup
    assert env.site.read_text() == http_config_text
    env.restore_site.assert_not_called()
    env.write_site.assert_not_called()


def test_install_survives_credentials_cleanup_failure(env, http_config_text):
    # issuance fails AND the token cleanup itself fails; the menu must still
    # surface its error rather than crash on the secondary CalledProcessError
    env.run_certbot.side_effect = CalledProcessError(1, "certbot")
    env.remove_credentials.side_effect = CalledProcessError(1, "rm")

    HttpsExtension({}).install_extension()  # must not raise

    env.backup_site.assert_not_called()
    assert env.site.read_text() == http_config_text


def test_install_token_uses_no_echo_prompt(env):
    HttpsExtension({}).install_extension()
    env.get_secret_input.assert_called_once()


# --------------------------------------------------------------------------- #
# remove_extension
# --------------------------------------------------------------------------- #
def test_remove_reverse_transforms_to_plain_http(env, http_config_text):
    env.site.write_text(_https_fixture(http_config_text))
    HttpsExtension({}).remove_extension()

    written = env.site.read_text()
    # back to plain HTTP, not a stock-template reset: the user body survives
    assert not config_enables_https(written)
    assert "listen 80;" in written
    assert "ssl_certificate" not in written
    assert "return 301" not in written  # the :80 redirect block is dropped
    # body carried over verbatim (custom locations, proxies, directives)
    assert "proxy_pass http://apiserver/websocket;" in written
    assert "proxy_pass http://mjpgstreamer4/;" in written
    assert "client_max_body_size 0;" in written
    env.reload_nginx.assert_called_once()


def test_remove_restores_port_from_live_site_not_settings(env, http_config_text):
    # the site was on 8080 before HTTPS; KIAUH settings (mock) report 80.
    # the restore must use the live site's recorded port, not settings.
    https = build_https_config(
        http_config_text, FQDN, FULLCHAIN, PRIVKEY, redirect_port=8080
    )
    env.site.write_text(https)
    env.settings.return_value.get.return_value = 80

    HttpsExtension({}).remove_extension()

    assert "listen 8080;" in env.site.read_text()


def test_remove_falls_back_to_settings_port_when_redirect_is_443(env):
    # a site whose first block is the TLS block (e.g. configured outside this
    # extension): extract_redirect_port would read 443, so the restore must
    # fall back to the configured HTTP port instead of rebuilding HTTP on 443
    manual = (
        "server {\n"
        "    listen 443 ssl;\n"
        "    server_name printer.example.com _;\n"
        "    root /home/pi/mainsail;\n"
        "}\n"
    )
    env.site.write_text(manual)
    env.settings.return_value.get.return_value = 80

    HttpsExtension({}).remove_extension()

    written = env.site.read_text()
    assert "listen 80;" in written
    assert "listen 443" not in written
    assert not config_enables_https(written)


def test_remove_informs_when_not_https(env):
    HttpsExtension({}).remove_extension()
    env.backup_site.assert_not_called()
    env.write_site.assert_not_called()


# --------------------------------------------------------------------------- #
# distro gate
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("distro_id", "supported"),
    [
        ("debian", True),
        ("ubuntu", True),
        ("raspbian", True),
        ("armbian", True),
        ("linuxmint", True),
        ("arch", False),
        ("fedora", False),
        ("", False),
    ],
)
def test_distro_gate(monkeypatch, distro_id, supported):
    monkeypatch.setattr(f"{MODULE}.get_distro_info", lambda: (distro_id, "1"))
    assert HttpsExtension({})._distro_supported() is supported


def test_distro_gate_handles_value_error(monkeypatch):
    def boom():
        raise ValueError("no os-release")

    monkeypatch.setattr(f"{MODULE}.get_distro_info", boom)
    assert HttpsExtension({})._distro_supported() is False


# --------------------------------------------------------------------------- #
# credential prompting
# --------------------------------------------------------------------------- #
def test_prompt_credentials_allows_special_chars_and_defaults(monkeypatch):
    provider = DnsProvider(
        key="custom",
        display_name="Custom",
        plugin_package="python3-certbot-dns-custom",
        plugin_flag="--dns-custom",
        credentials_fields=[
            CredField(ini_key="token", prompt="Token", secret=True),
            CredField(ini_key="zone", prompt="Zone", secret=False),
            CredField(ini_key="version", prompt="Version", secret=False, default="4"),
        ],
    )
    string_input = MagicMock(side_effect=["my-zone_id.example/v1", "4"])
    monkeypatch.setattr(f"{MODULE}.get_secret_input", MagicMock(return_value="tok"))
    monkeypatch.setattr(f"{MODULE}.get_string_input", string_input)

    values = HttpsExtension({})._prompt_credentials(provider)

    assert values == {"token": "tok", "zone": "my-zone_id.example/v1", "version": "4"}
    # plain fields must accept '-', '_', '.', '/' and offer the field default
    for call in string_input.call_args_list:
        assert call.kwargs.get("allow_special_chars") is True
    assert string_input.call_args_list[1].kwargs.get("default") == "4"


def test_distro_gate_handles_called_process_error(monkeypatch):
    def boom():
        # get_distro_info runs `cat /etc/os-release`; a missing file makes the
        # subprocess exit non-zero -> CalledProcessError (not an OSError)
        raise CalledProcessError(1, ["cat", "/etc/os-release"])

    monkeypatch.setattr(f"{MODULE}.get_distro_info", boom)
    assert HttpsExtension({})._distro_supported() is False
