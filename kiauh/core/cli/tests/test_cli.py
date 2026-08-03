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
from typing import Any, Dict, List, Set

import core.cli as cli_module
import pytest
from core.cli import run_cli


class FakeKlipperService:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.results: Dict[str, bool] = {}
        self.settings = type(
            "Settings",
            (),
            {
                "kiauh": type(
                    "KiauhSettingsSection", (), {"backup_before_update": False}
                )()
            },
        )()

    def install(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "install", "kwargs": kwargs})
        return self.results.get("install", True)

    def remove(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "remove", "kwargs": kwargs})
        return self.results.get("remove", True)

    def update(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "update", "kwargs": kwargs})
        return self.results.get("update", True)


class FakeMoonrakerService:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.results: Dict[str, bool] = {}

    def install(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "install", "kwargs": kwargs})
        return self.results.get("install", True)

    def remove(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "remove", "kwargs": kwargs})
        return self.results.get("remove", True)

    def update(self, **kwargs: Any) -> bool:
        self.calls.append({"method": "update", "kwargs": kwargs})
        return self.results.get("update", True)


class FakeWebClientService:
    def __init__(self) -> None:
        self.install_calls: List[Dict[str, Any]] = []
        self.remove_calls: List[Dict[str, Any]] = []
        self.update_calls: List[str] = []
        self.results: Dict[str, bool] = {}

    def install(self, **kwargs: Any) -> bool:
        self.install_calls.append(kwargs)
        return self.results.get("install", True)

    def remove(self, **kwargs: Any) -> bool:
        self.remove_calls.append(kwargs)
        return self.results.get("remove", True)

    def update(self) -> bool:
        self.update_calls.append("update")
        return self.results.get("update", True)


class FakeWebClientConfigService:
    def __init__(self) -> None:
        self.install_calls: List[Dict[str, Any]] = []
        self.update_calls: List[Dict[str, Any]] = []
        self.results: Dict[str, bool] = {}

    def install(self, **kwargs: Any) -> bool:
        self.install_calls.append(kwargs)
        return self.results.get("install", True)

    def update(self, **kwargs: Any) -> bool:
        self.update_calls.append(kwargs)
        return self.results.get("update", True)


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> FakeKlipperService:
    fake = FakeKlipperService()
    monkeypatch.setattr("core.cli.KlipperSetupService", lambda: fake)
    return fake


@pytest.fixture
def fake_moonraker_service(monkeypatch: pytest.MonkeyPatch) -> FakeMoonrakerService:
    fake = FakeMoonrakerService()
    monkeypatch.setattr("core.cli.MoonrakerSetupService", lambda: fake)
    return fake


@pytest.fixture
def fake_web_client_service(monkeypatch: pytest.MonkeyPatch) -> FakeWebClientService:
    fake = FakeWebClientService()
    monkeypatch.setattr("core.cli.WebClientSetupService", lambda name: fake)
    return fake


@pytest.fixture
def fake_web_client_config_service(
    monkeypatch: pytest.MonkeyPatch,
) -> FakeWebClientConfigService:
    fake = FakeWebClientConfigService()
    monkeypatch.setattr("core.cli.WebClientConfigSetupService", lambda name: fake)
    return fake


class TestCliDispatch:
    def test_no_args_returns_tui_signal(self) -> None:
        assert run_cli([]) == -1

    def test_install_klipper(self, fake_service: FakeKlipperService) -> None:
        rc = run_cli(["install", "klipper", "--count", "2"])
        assert rc == 0
        assert fake_service.calls == [
            {
                "method": "install",
                "kwargs": {
                    "count": 2,
                    "custom_names": None,
                    "create_example_cfg": False,
                    "match_moonraker": False,
                    "interactive": False,
                },
            }
        ]

    def test_install_klipper_default_count_is_none(
        self, fake_service: FakeKlipperService
    ) -> None:
        rc = run_cli(["install", "klipper"])
        assert rc == 0
        assert fake_service.calls[0]["kwargs"]["count"] is None

    def test_install_klipper_with_names(self, fake_service: FakeKlipperService) -> None:
        rc = run_cli(["install", "klipper", "--name", "a", "--name", "b"])
        assert rc == 0
        assert fake_service.calls[0]["kwargs"]["custom_names"] == {0: "a", 1: "b"}
        assert fake_service.calls[0]["kwargs"]["count"] is None

    def test_install_klipper_count_and_name_mismatch_rejected(self) -> None:
        with pytest.raises(SystemExit):
            run_cli([
                "install",
                "klipper",
                "--count",
                "3",
                "--name",
                "a",
                "--name",
                "b",
            ])

    def test_install_klipper_with_flags(self, fake_service: FakeKlipperService) -> None:
        rc = run_cli([
            "install",
            "klipper",
            "--create-example-cfg",
            "--match-moonraker",
        ])
        assert rc == 0
        kwargs = fake_service.calls[0]["kwargs"]
        assert kwargs["create_example_cfg"] is True
        assert kwargs["match_moonraker"] is True
        assert kwargs["interactive"] is False

    def test_install_klipper_failure_returns_nonzero(
        self, fake_service: FakeKlipperService
    ) -> None:
        fake_service.results["install"] = False
        assert run_cli(["install", "klipper"]) == 1

    def test_remove_klipper(self, fake_service: FakeKlipperService) -> None:
        rc = run_cli(["remove", "klipper", "--service", "--all", "--dir", "--env"])
        assert rc == 0
        assert fake_service.calls == [
            {
                "method": "remove",
                "kwargs": {
                    "remove_service": True,
                    "interactive": False,
                    "remove_dir": True,
                    "remove_env": True,
                    "remove_all": True,
                    "instance_suffixes": None,
                },
            }
        ]

    def test_remove_klipper_failure_returns_nonzero(
        self, fake_service: FakeKlipperService
    ) -> None:
        fake_service.results["remove"] = False
        assert run_cli(["remove", "klipper", "--service", "--all"]) == 1

    def test_remove_klipper_no_flags_is_rejected(
        self, fake_service: FakeKlipperService
    ) -> None:
        # a remove with no removal flags must not silently succeed
        with pytest.raises(SystemExit):
            run_cli(["remove", "klipper"])
        assert fake_service.calls == []

    def test_remove_klipper_service_without_explicit_intent_is_rejected(
        self, fake_service: FakeKlipperService
    ) -> None:
        # `--service` alone must NOT silently wipe all instances.
        # The user must pass `--all` (or `--instance <suffix>`).
        with pytest.raises(SystemExit):
            run_cli(["remove", "klipper", "--service"])
        assert fake_service.calls == []

    def test_remove_klipper_with_instance_suffix(
        self, fake_service: FakeKlipperService
    ) -> None:
        rc = run_cli([
            "remove",
            "klipper",
            "--service",
            "--instance",
            "a",
            "--instance",
            "b",
        ])
        assert rc == 0
        assert fake_service.calls[0]["kwargs"]["instance_suffixes"] == ["a", "b"]
        assert fake_service.calls[0]["kwargs"]["remove_all"] is False

    def test_update_klipper(self, fake_service: FakeKlipperService) -> None:
        rc = run_cli(["update", "klipper"])
        assert rc == 0
        assert fake_service.calls == [
            {"method": "update", "kwargs": {"interactive": False}}
        ]

    def test_update_klipper_with_backup_flag(
        self, fake_service: FakeKlipperService
    ) -> None:
        rc = run_cli(["update", "klipper", "--backup"])
        assert rc == 0
        assert fake_service.settings.kiauh.backup_before_update is True

    def test_update_klipper_failure_returns_nonzero(
        self, fake_service: FakeKlipperService
    ) -> None:
        fake_service.results["update"] = False
        assert run_cli(["update", "klipper"]) == 1


class TestMoonrakerCliDispatch:
    def test_install_moonraker_default(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        rc = run_cli(["install", "moonraker"])
        assert rc == 0
        assert fake_moonraker_service.calls == [
            {
                "method": "install",
                "kwargs": {
                    "klipper_suffixes": None,
                    "create_example_cfg": False,
                    "interactive": False,
                },
            }
        ]

    def test_install_moonraker_with_suffixes(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        rc = run_cli([
            "install",
            "moonraker",
            "--klipper-suffix",
            "a",
            "--klipper-suffix",
            "b",
        ])
        assert rc == 0
        assert fake_moonraker_service.calls[0]["kwargs"]["klipper_suffixes"] == [
            "a",
            "b",
        ]

    def test_install_moonraker_failure_returns_nonzero(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        fake_moonraker_service.results["install"] = False
        assert run_cli(["install", "moonraker"]) == 1

    def test_remove_moonraker(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        rc = run_cli([
            "remove",
            "moonraker",
            "--service",
            "--all",
            "--dir",
            "--env",
            "--polkit",
        ])
        assert rc == 0
        assert fake_moonraker_service.calls == [
            {
                "method": "remove",
                "kwargs": {
                    "remove_service": True,
                    "remove_dir": True,
                    "remove_env": True,
                    "remove_polkit": True,
                    "interactive": False,
                    "remove_all": True,
                    "instance_suffixes": None,
                },
            }
        ]

    def test_remove_moonraker_service_without_explicit_intent_is_rejected(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        # `--service` alone must NOT silently wipe all instances.
        with pytest.raises(SystemExit):
            run_cli(["remove", "moonraker", "--service"])
        assert fake_moonraker_service.calls == []

    def test_update_moonraker(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        rc = run_cli(["update", "moonraker"])
        assert rc == 0
        assert fake_moonraker_service.calls == [
            {"method": "update", "kwargs": {"interactive": False}}
        ]

    def test_remove_moonraker_no_flags_is_rejected(
        self, fake_moonraker_service: FakeMoonrakerService
    ) -> None:
        # a remove with no removal flags must not silently succeed
        with pytest.raises(SystemExit):
            run_cli(["remove", "moonraker"])
        assert fake_moonraker_service.calls == []


class TestWebClientCliDispatch:
    def test_install_mainsail(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        rc = run_cli([
            "install",
            "mainsail",
            "--port",
            "8080",
            "--install-config",
            "--continue-without-moonraker",
        ])
        assert rc == 0
        assert fake_web_client_service.install_calls == [
            {
                "port": 8080,
                "install_client_cfg": True,
                "continue_without_moonraker": True,
                "interactive": False,
            }
        ]

    def test_install_fluidd_default(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        rc = run_cli(["install", "fluidd"])
        assert rc == 0
        assert fake_web_client_service.install_calls == [
            {
                "port": None,
                "install_client_cfg": False,
                "continue_without_moonraker": False,
                "interactive": False,
            }
        ]

    def test_install_client_config_runs_non_interactively(
        self, fake_web_client_config_service: FakeWebClientConfigService
    ) -> None:
        rc = run_cli(["install", "mainsail-config"])
        assert rc == 0
        assert fake_web_client_config_service.install_calls == [{"interactive": False}]

    def test_install_web_client_failure_returns_nonzero(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        fake_web_client_service.results["install"] = False
        assert run_cli(["install", "mainsail"]) == 1

    def test_remove_mainsail_no_flags_is_rejected(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        # a remove with no removal flags must not silently succeed
        with pytest.raises(SystemExit):
            run_cli(["remove", "mainsail"])
        assert fake_web_client_service.remove_calls == []

    def test_remove_mainsail_with_client_and_config(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        rc = run_cli(["remove", "mainsail", "--client", "--config"])
        assert rc == 0
        assert fake_web_client_service.remove_calls == [
            {
                "remove_client": True,
                "remove_client_cfg": True,
                "backup_config": True,
                "interactive": False,
            }
        ]

    def test_remove_fluidd_no_backup(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        rc = run_cli(["remove", "fluidd", "--client", "--no-backup"])
        assert rc == 0
        assert fake_web_client_service.remove_calls == [
            {
                "remove_client": True,
                "remove_client_cfg": False,
                "backup_config": False,
                "interactive": False,
            }
        ]

    def test_update_mainsail(
        self, fake_web_client_service: FakeWebClientService
    ) -> None:
        rc = run_cli(["update", "mainsail"])
        assert rc == 0
        assert fake_web_client_service.update_calls == ["update"]

    def test_update_fluidd_config_runs_non_interactively(
        self, fake_web_client_config_service: FakeWebClientConfigService
    ) -> None:
        rc = run_cli(["update", "fluidd-config"])
        assert rc == 0
        assert fake_web_client_config_service.update_calls == [{"interactive": False}]


class TestDispatchRegistry:
    """``run_cli`` must use a dispatch registry instead of a long
    if/elif chain, and the registry must cover every (command, component) pair
    the argument parser can produce."""

    _EXPECTED: Set[tuple] = {
        ("install", "klipper"),
        ("remove", "klipper"),
        ("update", "klipper"),
        ("install", "moonraker"),
        ("remove", "moonraker"),
        ("update", "moonraker"),
        ("install", "mainsail"),
        ("install", "fluidd"),
        ("remove", "mainsail"),
        ("remove", "fluidd"),
        ("update", "mainsail"),
        ("update", "fluidd"),
        ("install", "mainsail-config"),
        ("install", "fluidd-config"),
        ("update", "mainsail-config"),
        ("update", "fluidd-config"),
    }

    def test_dispatch_registry_exists_and_covers_every_pair(self) -> None:
        dispatch = getattr(cli_module, "DISPATCH", None)
        assert dispatch is not None, "run_cli must expose a DISPATCH registry"
        assert set(dispatch.keys()) == self._EXPECTED
        for handler in dispatch.values():
            assert callable(handler)

    def test_subparser_helpers_are_typed_not_any(self) -> None:
        # the ``_add_*`` helpers must accept ``argparse._SubParsersAction``, not ``Any``.
        import inspect

        for name in dir(cli_module):
            if not name.startswith("_add_"):
                continue
            func = getattr(cli_module, name)
            if not inspect.isfunction(func):
                continue
            hints = inspect.signature(func).parameters.get("sub")
            assert hints is not None
            assert hints.annotation is not Any, f"{name} must not type ``sub`` as Any"
            assert "SubParsersAction" in str(hints.annotation), (
                f"{name} must type ``sub`` as an argparse SubParsersAction"
            )


class TestPackaging:
    def test_pyproject_metadata_allows_editable_dev_install(self) -> None:
        project_root = Path(__file__).resolve().parents[4]
        import subprocess as sp
        import sys

        cmd = [sys.executable, "-m", "pip", "install", "--dry-run", "-e", ".[dev]"]
        result = sp.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0 and "externally-managed-environment" in result.stderr:
            result = sp.run(
                [*cmd[:5], "--break-system-packages", *cmd[5:]],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
        assert result.returncode == 0, result.stderr
