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
from typing import Any, List

import components.webui_client.menus.client_install_menu as cim_module
import pytest
from components.webui_client.menus.client_install_menu import ClientInstallMenu


class _FakeClient:
    def __init__(self, name: str = "mainsail") -> None:
        self.name = name
        self.display_name = name.capitalize()
        self.nginx_config = Path("/tmp/nginx/mainsail")


def _build_menu(monkeypatch: pytest.MonkeyPatch, current_port: int | None = 80) -> ClientInstallMenu:
    # Neutralise singletons / IO from BaseMenu and KiauhSettings.
    monkeypatch.setattr(cim_module, "KiauhSettings", lambda: _FakeSettings())
    monkeypatch.setattr(cim_module, "get_nginx_listen_port", lambda cfg: current_port)
    return ClientInstallMenu(_FakeClient())


class _FakeSettings:
    def __init__(self) -> None:
        self._section = _FakeSection()
        self.mainsail = self._section
        self.fluidd = self._section

    def save(self) -> None:
        self._section.saved = True

    def __getitem__(self, key):
        return self._section


class _FakeSection:
    port = 80
    saved = False


class TestClientInstallMenu:
    def test_options_cover_reinstall_and_port_change(self, monkeypatch) -> None:
        menu = _build_menu(monkeypatch)
        # BaseMenu may append a "back" footer option depending on the menu's
        # footer type; the two install-specific entries must always be present.
        assert {"1", "2"}.issubset(menu.options.keys())

    def test_set_previous_menu_defaults_to_install_menu(self, monkeypatch) -> None:
        menu = _build_menu(monkeypatch)
        menu.set_previous_menu(None)
        from core.menus.install_menu import InstallMenu

        assert menu.previous_menu is InstallMenu

    def test_get_current_port_uses_nginx_value(self, monkeypatch) -> None:
        menu = _build_menu(monkeypatch, current_port=8080)
        assert menu._get_current_port() == 8080

    def test_get_current_port_falls_back_to_settings(self, monkeypatch) -> None:
        menu = _build_menu(monkeypatch, current_port=None)
        # FakeSettings._FakeSection.port == 80
        assert menu._get_current_port() == 80

    def test_reinstall_delegates_to_web_client_setup_service(self, monkeypatch) -> None:
        menu = _build_menu(monkeypatch)
        calls: List[Any] = []

        class _FakeService:
            def install(self, **kwargs) -> bool:
                calls.append(kwargs)
                return True

        monkeypatch.setattr(cim_module, "WebClientSetupService", lambda name: _FakeService())
        menu.reinstall_client()

        assert calls
        assert calls[0]["reinstall"] is True
        assert calls[0]["interactive"] is True

    def test_change_listen_port_persists_and_restarts_nginx(self, monkeypatch, tmp_path) -> None:
        menu = _build_menu(monkeypatch)
        captured: dict = {}

        monkeypatch.setattr(cim_module, "get_client_port_selection", lambda *a, **k: 9090)
        monkeypatch.setattr(cim_module, "cmd_sysctl_service", lambda svc, action: captured.setdefault("nginx", []).append(action))
        monkeypatch.setattr(cim_module, "set_listen_port", lambda client, c, n: captured.setdefault("set_port", (c, n)))
        monkeypatch.setattr(cim_module, "get_ipv4_addr", lambda: "127.0.0.1")
        # Inject a fake message service to avoid the real MessageService.
        menu.message_service = type("MS", (), {"set_message": lambda self, m: captured.setdefault("msg", m)})()

        menu.change_listen_port()

        assert captured["nginx"] == ["stop", "start"]
        assert captured["set_port"] == (80, 9090)
        assert menu.client_settings.port == 9090


class _CapturingMessageService:
    def __init__(self) -> None:
        self.messages: List[Any] = []

    def set_message(self, message: Any) -> None:
        self.messages.append(message)


class TestHttpsGuards:
    """Both menu actions rewrite the nginx site from the plain-HTTP template.

    Doing that on a TLS site strips the 443 block and orphans the certificate,
    so both must refuse while HTTPS is enabled.
    """

    def _menu_for(
        self, monkeypatch, tmp_path: Path, config_text: str
    ) -> ClientInstallMenu:
        site = tmp_path.joinpath("mainsail")
        site.write_text(config_text)
        menu = _build_menu(monkeypatch)
        menu.client.nginx_config = site
        menu.message_service = _CapturingMessageService()
        return menu

    def test_reinstall_refused_on_https_site(self, monkeypatch, tmp_path) -> None:
        menu = self._menu_for(
            monkeypatch,
            tmp_path,
            "server {\n    listen 443 ssl http2;\n    server_name x _;\n}\n",
        )
        installed: List[Any] = []
        monkeypatch.setattr(
            cim_module, "WebClientSetupService", lambda name: installed.append(name)
        )

        menu.reinstall_client()

        assert not installed
        assert menu.message_service.messages

    def test_change_listen_port_refused_on_https_site(
        self, monkeypatch, tmp_path
    ) -> None:
        menu = self._menu_for(
            monkeypatch,
            tmp_path,
            "server {\n    listen 443 ssl http2;\n    server_name x _;\n}\n",
        )
        touched: List[Any] = []
        monkeypatch.setattr(
            cim_module, "set_listen_port", lambda *a: touched.append("set_port")
        )
        monkeypatch.setattr(
            cim_module, "cmd_sysctl_service", lambda *a: touched.append("nginx")
        )

        menu.change_listen_port()

        # the port is never rewritten and nginx is never bounced
        assert not touched
        assert menu.message_service.messages

    def test_reinstall_proceeds_on_plain_http_site(self, monkeypatch, tmp_path) -> None:
        menu = self._menu_for(
            monkeypatch,
            tmp_path,
            "server {\n    listen 80;\n    server_name _;\n}\n",
        )
        calls: List[Any] = []

        class _FakeService:
            def install(self, **kwargs) -> bool:
                calls.append(kwargs)
                return True

        monkeypatch.setattr(
            cim_module, "WebClientSetupService", lambda name: _FakeService()
        )

        menu.reinstall_client()

        assert calls
        assert calls[0]["reinstall"] is True