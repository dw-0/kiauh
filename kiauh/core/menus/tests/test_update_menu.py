# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, List

import pytest
from core.menus.update_menu import UpdateMenu


def _make_status(status: int = 2, local: str | None = "v1", remote: str | None = "v2"):
    return type(
        "ComponentStatus", (), {"status": status, "local": local, "remote": remote}
    )()


@pytest.fixture
def patched_menu(monkeypatch: pytest.MonkeyPatch) -> UpdateMenu:
    monkeypatch.setattr(
        "core.menus.update_menu.get_klipper_status",
        lambda: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_moonraker_status",
        lambda: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_client_status",
        lambda *args, **kwargs: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_client_config_status",
        lambda *args, **kwargs: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_klipperscreen_status",
        lambda: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_crowsnest_status",
        lambda: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.get_katapult_status",
        lambda: _make_status(),
    )
    monkeypatch.setattr(
        "core.menus.update_menu.update_system_package_lists", lambda silent: None
    )
    monkeypatch.setattr("core.menus.update_menu.get_upgradable_packages", lambda: [])

    class FakeSpinner:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def pause(self):
            pass

        def resume(self):
            pass

    monkeypatch.setattr("core.menus.base_menu.Spinner", FakeSpinner)

    return UpdateMenu()


class TestUpdateMenuConstruction:
    def test_options_cover_all_components(self, patched_menu: UpdateMenu) -> None:
        expected = {"a", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "b"}
        assert set(patched_menu.options.keys()) == expected

    def test_status_data_marked_installed(self, patched_menu: UpdateMenu) -> None:
        for name in ["klipper", "moonraker", "mainsail", "fluidd"]:
            assert patched_menu.status_data[name]["installed"] is True


class TestUpdateRoutine:
    def test_run_update_routine_skips_not_installed(
        self, patched_menu: UpdateMenu, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patched_menu.status_data["klipper"]["installed"] = False
        called: List[Any] = []

        patched_menu._run_update_routine("klipper", lambda: called.append(True))

        assert called == []

    def test_run_update_routine_skips_up_to_date(
        self, patched_menu: UpdateMenu
    ) -> None:
        patched_menu.status_data["klipper"]["local"] = "v1"
        patched_menu.status_data["klipper"]["remote"] = "v1"
        called: List[Any] = []

        patched_menu._run_update_routine("klipper", lambda: called.append(True))

        assert called == []

    def test_run_update_routine_executes_when_update_available(
        self, patched_menu: UpdateMenu, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patched_menu.status_data["klipper"]["installed"] = True
        patched_menu.status_data["klipper"]["local"] = "v1"
        patched_menu.status_data["klipper"]["remote"] = "v2"
        called: List[Any] = []
        monkeypatch.setattr(
            "core.menus.update_menu.get_klipper_status", lambda: _make_status()
        )

        patched_menu._run_update_routine("klipper", lambda: called.append(True))

        assert called == [True]


class TestSystemUpdates:
    def test_no_packages_logs_info(self, patched_menu: UpdateMenu) -> None:
        patched_menu.packages = []
        # should not raise
        patched_menu._run_system_updates()

    def test_fetch_status_translates_runtime_error_to_warning(
        self, patched_menu: UpdateMenu, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # when ``apt-get update`` fails, ``update_system_package_lists``
        # raises ``RuntimeError``. The update menu is a presentation boundary —
        # it must catch, log a warning and show an empty upgradable list instead
        # of crashing the menu.
        def _raise(*_a, **_k):
            raise RuntimeError("apt-get update failed")

        monkeypatch.setattr(
            "core.menus.update_menu.update_system_package_lists", _raise
        )
        monkeypatch.setattr(
            "core.menus.update_menu.get_upgradable_packages", lambda: []
        )

        patched_menu._fetch_system_package_update_status()

        assert patched_menu.packages == []
        assert patched_menu.package_count == 0

    def test_packages_trigger_upgrade_flow(
        self, patched_menu: UpdateMenu, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        patched_menu.packages = ["curl", "git"]
        upgraded: List[List[str]] = []
        monkeypatch.setattr("core.menus.update_menu.get_confirm", lambda *a, **k: True)
        monkeypatch.setattr(
            "core.menus.update_menu.upgrade_system_packages",
            lambda pkgs: upgraded.append(pkgs),
        )
        monkeypatch.setattr(
            "core.menus.update_menu.update_system_package_lists", lambda silent: None
        )
        monkeypatch.setattr(
            "core.menus.update_menu.get_upgradable_packages", lambda: []
        )

        patched_menu._run_system_updates()

        assert upgraded == [["curl", "git"]]


class TestSpinnerPauseDuringSystemUpdateFetch:
    def test_fetch_system_package_status_pauses_spinner_during_apt_update(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The loading spinner must be paused while ``apt-get update`` runs so
        that a possible sudo password prompt is not overwritten by the spinner.
        """
        calls: list[str | tuple[str, bool]] = []

        @contextmanager
        def recording_pause_loading(self: UpdateMenu) -> Generator[None, None, None]:
            calls.append("pause")
            yield
            calls.append("resume")

        monkeypatch.setattr(UpdateMenu, "pause_loading", recording_pause_loading)
        monkeypatch.setattr(
            "core.menus.update_menu.update_system_package_lists",
            lambda silent: calls.append(("apt", silent)),
        )
        monkeypatch.setattr(
            "core.menus.update_menu.get_upgradable_packages",
            lambda: ["curl"],
        )
        monkeypatch.setattr(
            "core.menus.update_menu.Logger.print_warn", lambda *a, **k: None
        )

        menu = UpdateMenu()
        # the constructor already calls _fetch_system_package_update_status once
        assert calls == ["pause", ("apt", True), "resume"]

        menu._fetch_system_package_update_status()

        # every fetch must pause the spinner around the apt call
        assert calls == [
            "pause",
            ("apt", True),
            "resume",
            "pause",
            ("apt", True),
            "resume",
        ]


class TestUpdateAll:
    def test_update_all_invokes_each_component_update(
        self, patched_menu: UpdateMenu, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: List[str] = []
        monkeypatch.setattr(
            patched_menu, "update_klipper", lambda **k: calls.append("klipper")
        )
        monkeypatch.setattr(
            patched_menu, "update_moonraker", lambda **k: calls.append("moonraker")
        )
        monkeypatch.setattr(
            patched_menu, "update_mainsail", lambda **k: calls.append("mainsail")
        )
        monkeypatch.setattr(
            patched_menu,
            "update_mainsail_config",
            lambda **k: calls.append("mainsail_config"),
        )
        monkeypatch.setattr(
            patched_menu, "update_fluidd", lambda **k: calls.append("fluidd")
        )
        monkeypatch.setattr(
            patched_menu,
            "update_fluidd_config",
            lambda **k: calls.append("fluidd_config"),
        )
        monkeypatch.setattr(
            patched_menu,
            "update_klipperscreen",
            lambda **k: calls.append("klipperscreen"),
        )
        monkeypatch.setattr(
            patched_menu, "update_crowsnest", lambda **k: calls.append("crowsnest")
        )
        monkeypatch.setattr(
            patched_menu, "update_katapult", lambda **k: calls.append("katapult")
        )
        monkeypatch.setattr(
            patched_menu, "upgrade_system_packages", lambda **k: calls.append("system")
        )

        patched_menu.update_all()

        assert set(calls) == {
            "klipper",
            "moonraker",
            "mainsail",
            "mainsail_config",
            "fluidd",
            "fluidd_config",
            "klipperscreen",
            "crowsnest",
            "katapult",
            "system",
        }
