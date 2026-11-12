# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, List

import pytest
from components.webui_client import client_utils
from components.webui_client.base_data import WebClientType
from components.webui_client.client_utils import (
    backup_client_config_data,
    backup_client_data,
    create_client_config_symlink,
    detect_client_cfg_conflict,
    get_client_status,
    get_current_client_config,
    get_download_url,
    get_existing_clients,
    get_local_client_version,
    get_next_free_port,
    get_nginx_listen_port,
    get_remote_client_version,
    is_https_nginx_config,
    read_ports_from_nginx_configs,
    set_listen_port,
)


class TestGetLocalClientVersion:
    def test_returns_none_when_client_dir_missing(self, client) -> None:
        client.client_dir = Path("/does/not/exist")
        assert get_local_client_version(client) is None

    def test_reads_release_info_json(self, client, tmp_path: Path) -> None:
        client.client_dir = tmp_path
        release = tmp_path / "release_info.json"
        release.write_text('{"version": "v2.0.0"}')

        assert get_local_client_version(client) == "v2.0.0"

    def test_falls_back_to_version_file(self, client, tmp_path: Path) -> None:
        client.client_dir = tmp_path
        (tmp_path / ".version").write_text("v1.2.3\n")

        assert get_local_client_version(client) == "v1.2.3"

    def test_returns_none_for_empty_version_file(self, client, tmp_path: Path) -> None:
        client.client_dir = tmp_path
        (tmp_path / ".version").write_text("")

        assert get_local_client_version(client) is None


class TestGetRemoteClientVersion:
    def test_returns_tag_when_available(self, monkeypatch, client) -> None:
        monkeypatch.setattr(
            client_utils, "get_latest_remote_tag", lambda repo: "v3.0.0"
        )
        assert get_remote_client_version(client) == "v3.0.0"

    def test_returns_none_when_tag_empty(self, monkeypatch, client) -> None:
        monkeypatch.setattr(client_utils, "get_latest_remote_tag", lambda repo: "")
        assert get_remote_client_version(client) is None

    def test_returns_none_on_error(self, monkeypatch, client) -> None:
        monkeypatch.setattr(
            client_utils,
            "get_latest_remote_tag",
            lambda repo: (_ for _ in ()).throw(RuntimeError("network")),
        )
        assert get_remote_client_version(client) is None


class TestGetDownloadUrl:
    def test_returns_stable_url_when_not_unstable(self, monkeypatch, client) -> None:
        class FakeSettings:
            def get(self, name, key):
                return False

        monkeypatch.setattr(client_utils, "KiauhSettings", FakeSettings)
        url = get_download_url("https://example.com/repo", client)
        assert "latest/download" in url

    def test_returns_unstable_url_when_available(self, monkeypatch, client) -> None:
        class FakeSettings:
            def get(self, name, key):
                return True

        monkeypatch.setattr(client_utils, "KiauhSettings", FakeSettings)
        monkeypatch.setattr(
            client_utils, "get_latest_unstable_tag", lambda repo: "v9.9.9"
        )
        url = get_download_url("https://example.com/repo", client)
        assert "v9.9.9" in url


class TestDetectClientCfgConflict:
    def test_mainsail_conflicts_with_fluidd_installed(
        self, monkeypatch, client
    ) -> None:
        def fake_status(c):
            code = 2 if c.client == WebClientType.FLUIDD else 0
            return type("S", (), {"status": code})()

        monkeypatch.setattr(client_utils, "get_client_config_status", fake_status)
        client.client = WebClientType.MAINSAIL
        assert detect_client_cfg_conflict(client) is True

    def test_fluidd_conflicts_with_mainsail_installed(
        self, monkeypatch, client
    ) -> None:
        def fake_status(c):
            code = 2 if c.client == WebClientType.MAINSAIL else 0
            return type("S", (), {"status": code})()

        monkeypatch.setattr(client_utils, "get_client_config_status", fake_status)
        client.client = WebClientType.FLUIDD
        assert detect_client_cfg_conflict(client) is True


class TestGetNextFreePort:
    def test_returns_lowest_unused_port(self) -> None:
        assert get_next_free_port([80, 81]) == 82

    def test_starts_at_80(self) -> None:
        assert get_next_free_port([]) == 80


class TestNginxPortParsing:
    def test_parses_plain_listen_port(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen 8080;\n}\n")
        assert get_nginx_listen_port(cfg) == 8080

    def test_parses_listen_port_with_host(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen 127.0.0.1:9090;\n}\n")
        assert get_nginx_listen_port(cfg) == 9090

    def test_returns_none_when_no_listen(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n}\n")
        assert get_nginx_listen_port(cfg) is None

    @pytest.mark.parametrize(
        ("listen_line", "expected"),
        [
            ("    listen 80 default_server;", 80),
            ("    listen [::]:80;", 80),
            # a TLS listen: the trailing flags must not be mistaken for the port
            ("    listen 443 ssl http2;", 443),
            ("    listen [::]:443 ssl http2;", 443),
        ],
    )
    def test_parses_tls_and_ipv6_listen(
        self, tmp_path: Path, listen_line: str, expected: int
    ) -> None:
        cfg = tmp_path / "site"
        cfg.write_text(f"server {{\n{listen_line}\n    server_name _;\n}}\n")
        assert get_nginx_listen_port(cfg) == expected

    def test_returns_none_when_unparsable(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen ssl;\n}\n")
        assert get_nginx_listen_port(cfg) is None

    def test_https_dual_block_returns_443(self, tmp_path: Path) -> None:
        # the HTTPS rewrite yields an :80 redirect block plus a 443 TLS block
        cfg = tmp_path / "site"
        cfg.write_text(
            "server {\n    listen 80;\n    return 301 https://printer.example.com$request_uri;\n}\n"
            "server {\n    listen 443 ssl http2;\n    server_name printer.example.com _;\n}\n"
        )
        assert get_nginx_listen_port(cfg) == 443

    def test_reads_all_configs_in_enabled_dir(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        sites = tmp_path / "sites-enabled"
        sites.mkdir()
        (sites / "a").write_text("listen 1000;")
        (sites / "b").write_text("listen 2000;")
        monkeypatch.setattr(client_utils, "NGINX_SITES_ENABLED", sites)

        ports = read_ports_from_nginx_configs()
        assert ports == [1000, 2000]

    def test_reads_every_listen_port_not_just_the_last(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        # an HTTPS site has both the :80 redirect block and the :443 TLS block;
        # availability checks must see BOTH, not just the last listen in the file
        sites = tmp_path / "sites-enabled"
        sites.mkdir()
        (sites / "mainsail").write_text(
            "server {\n    listen 80;\n}\nserver {\n    listen 443 ssl http2;\n}\n"
        )
        (sites / "fluidd").write_text("server {\n    listen 8080;\n}\n")
        monkeypatch.setattr(client_utils, "NGINX_SITES_ENABLED", sites)

        assert read_ports_from_nginx_configs() == [80, 443, 8080]

    def test_returns_empty_when_enabled_dir_missing(self, monkeypatch) -> None:
        monkeypatch.setattr(client_utils, "NGINX_SITES_ENABLED", Path("/missing"))
        assert read_ports_from_nginx_configs() == []


class TestIsHttpsNginxConfig:
    def test_true_for_tls_block(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen 443 ssl http2;\n}\n")
        assert is_https_nginx_config(cfg) is True

    def test_false_for_plain_http(self, tmp_path: Path) -> None:
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen 80;\n}\n")
        assert is_https_nginx_config(cfg) is False

    def test_false_when_missing(self, tmp_path: Path) -> None:
        assert is_https_nginx_config(tmp_path / "nope") is False

    def test_ignores_commented_directive(self, tmp_path: Path) -> None:
        # a commented-out example must not be read as an enabled TLS block
        cfg = tmp_path / "site"
        cfg.write_text("server {\n    listen 80;\n    # listen 443 ssl;\n}\n")
        assert is_https_nginx_config(cfg) is False


class TestSetListenPort:
    def test_replaces_port_in_config(
        self, client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client.name = "mainsail"
        monkeypatch.setattr(client_utils, "NGINX_SITES_AVAILABLE", tmp_path)
        cfg = tmp_path / "mainsail"
        cfg.write_text("server {\n    listen 80;\n}\n")

        set_listen_port(client, 80, 8080)

        assert "listen 8080" in cfg.read_text()


class TestCreateClientConfigSymlink:
    def test_creates_symlink_per_instance(
        self, monkeypatch, client, tmp_path: Path
    ) -> None:
        client.client_config.config_dir = tmp_path / "cfg"
        client.client_config.config_filename = "mainsail.cfg"
        called: List[Any] = []
        monkeypatch.setattr(
            client_utils, "create_symlink", lambda s, t: called.append((s, t))
        )

        class FakeInstance:
            base = type("Base", (), {"cfg_dir": tmp_path / "printer"})()

        create_client_config_symlink(client.client_config, [FakeInstance()])

        assert len(called) == 1

    def test_symlink_failure_logs_error_and_continues(
        self, monkeypatch, client, tmp_path: Path
    ) -> None:
        client.client_config.config_dir = tmp_path / "cfg"
        client.client_config.config_filename = "mainsail.cfg"

        attempt: List[Any] = []

        def flaky_create_symlink(source, target) -> None:
            attempt.append(target)
            if len(attempt) == 1:
                raise RuntimeError("permission denied")

        monkeypatch.setattr(client_utils, "create_symlink", flaky_create_symlink)
        errors: List[str] = []
        monkeypatch.setattr(
            client_utils.Logger,
            "print_error",
            lambda msg, *a, **k: errors.append(str(msg)),
        )

        class FakeInstance:
            def __init__(self, cfg: Path) -> None:
                self.base = type("Base", (), {"cfg_dir": cfg})()

        create_client_config_symlink(
            client.client_config,
            [FakeInstance(tmp_path / "a"), FakeInstance(tmp_path / "b")],
        )

        assert len(attempt) == 2  # failure did not abort the loop
        assert any("symlink" in m.lower() for m in errors)


class TestBackupClientData:
    def test_backs_up_client_dir_and_config_file(
        self, monkeypatch, client, tmp_path: Path
    ) -> None:
        client.client_dir = tmp_path / "mainsail"
        client.client_dir.mkdir()
        (client.client_dir / ".version").write_text("v1\n")
        client.config_file = client.client_dir / "config.json"
        client.config_file.write_text("{}")

        calls: List[str] = []

        class FakeBackup:
            backup_root = tmp_path / "backups"

            def backup_directory(self, **kwargs):
                calls.append("dir")

            def backup_file(self, **kwargs):
                calls.append("file")

        monkeypatch.setattr(client_utils, "BackupService", FakeBackup)
        backup_client_data(client)

        assert "dir" in calls
        assert "file" in calls


class TestBackupClientConfigData:
    def test_backs_up_config_dir(self, monkeypatch, client, tmp_path: Path) -> None:
        client.client_dir = tmp_path / "mainsail"
        client.client_dir.mkdir()
        (client.client_dir / ".version").write_text("v1\n")
        client.client_config.config_dir = tmp_path / "mainsail-config"

        calls: List[str] = []

        class FakeBackup:
            backup_root = tmp_path / "backups"

            def backup_directory(self, **kwargs):
                calls.append("dir")

        monkeypatch.setattr(client_utils, "BackupService", FakeBackup)
        backup_client_config_data(client)

        assert "dir" in calls


class TestGetClientStatus:
    def test_sets_status_not_installed_when_dir_missing(
        self, monkeypatch, client, tmp_path: Path
    ) -> None:
        client.client_dir = tmp_path / "missing"
        monkeypatch.setattr(
            client_utils,
            "get_install_status",
            lambda *args, **kwargs: type(
                "S", (), {"status": 2, "local": None, "remote": None}
            )(),
        )

        status = get_client_status(client)
        assert status.status == 0


class TestGetCurrentClientConfig:
    def test_returns_dash_when_no_config_dirs(self, monkeypatch) -> None:
        monkeypatch.setattr(
            client_utils,
            "MainsailData",
            lambda: type(
                "M",
                (),
                {
                    "client_config": type(
                        "C", (), {"config_dir": Path("/no/mainsail")}
                    )()
                },
            )(),
        )
        monkeypatch.setattr(
            client_utils,
            "FluiddData",
            lambda: type(
                "F",
                (),
                {"client_config": type("C", (), {"config_dir": Path("/no/fluidd")})()},
            )(),
        )

        result = get_current_client_config()
        assert "-" in result

    def test_returns_single_installed_name(self, monkeypatch, tmp_path: Path) -> None:
        cfg_dir = tmp_path / "mainsail-config"
        cfg_dir.mkdir()
        monkeypatch.setattr(
            client_utils,
            "MainsailData",
            lambda: type(
                "M",
                (),
                {
                    "client_config": type(
                        "C",
                        (),
                        {"config_dir": cfg_dir, "display_name": "Mainsail-Config"},
                    )()
                },
            )(),
        )
        monkeypatch.setattr(
            client_utils,
            "FluiddData",
            lambda: type(
                "F",
                (),
                {"client_config": type("C", (), {"config_dir": Path("/no/fluidd")})()},
            )(),
        )

        result = get_current_client_config()
        assert "Mainsail-Config" in result


class TestGetExistingClients:
    @staticmethod
    def _client(installed: bool) -> SimpleNamespace:
        return SimpleNamespace(client_dir=SimpleNamespace(exists=lambda: installed))

    def test_returns_only_installed_clients(self, monkeypatch) -> None:
        mainsail = self._client(installed=True)
        fluidd = self._client(installed=False)
        monkeypatch.setattr(
            client_utils,
            "CLIENTS",
            {"mainsail": lambda: mainsail, "fluidd": lambda: fluidd},
        )

        assert get_existing_clients() == [mainsail]

    def test_returns_only_fluidd_when_only_fluidd_installed(self, monkeypatch) -> None:
        mainsail = self._client(installed=False)
        fluidd = self._client(installed=True)
        monkeypatch.setattr(
            client_utils,
            "CLIENTS",
            {"mainsail": lambda: mainsail, "fluidd": lambda: fluidd},
        )

        assert get_existing_clients() == [fluidd]

    def test_returns_both_clients_in_order_when_both_installed(
        self, monkeypatch
    ) -> None:
        mainsail = self._client(installed=True)
        fluidd = self._client(installed=True)
        monkeypatch.setattr(
            client_utils,
            "CLIENTS",
            {"mainsail": lambda: mainsail, "fluidd": lambda: fluidd},
        )

        assert get_existing_clients() == [mainsail, fluidd]

    def test_returns_empty_list_when_no_client_installed(self, monkeypatch) -> None:
        monkeypatch.setattr(
            client_utils,
            "CLIENTS",
            {
                "mainsail": lambda: self._client(installed=False),
                "fluidd": lambda: self._client(installed=False),
            },
        )

        assert get_existing_clients() == []
