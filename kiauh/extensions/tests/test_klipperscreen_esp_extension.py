# ======================================================================= #
#  Copyright (C) 2026 umeiko                                               #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CalledProcessError
from types import SimpleNamespace

import pytest
from extensions.klipperscreen_esp import (
    KLIPPERSCREEN_ESP_RELEASE_BASE,
    KLIPPERSCREEN_ESP_UNINSTALL_SCRIPT,
)
from extensions.klipperscreen_esp.klipperscreen_esp_extension import (
    KlipperScreenEspExtension,
)

MODULE = "extensions.klipperscreen_esp.klipperscreen_esp_extension"


@pytest.fixture
def extension() -> KlipperScreenEspExtension:
    return KlipperScreenEspExtension({"name": "test"})


def mock_answers(monkeypatch: pytest.MonkeyPatch, answers: list[bool]) -> None:
    remaining = list(answers)
    monkeypatch.setattr(
        f"{MODULE}.get_confirm", lambda *args, **kwargs: remaining.pop(0)
    )


def mock_scripts(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[str], list[tuple[list[str], dict]]]:
    downloads: list[str] = []
    calls: list[tuple[list[str], dict]] = []
    monkeypatch.setattr(f"{MODULE}.platform.machine", lambda: "x86_64")

    def fake_run(command: list[str], check: bool, env: dict | None = None):
        if command[0] == "curl":
            downloads.append(command[-3])
            Path(command[-1]).write_text("ok", encoding="utf-8")
        else:
            calls.append((command, env or {}))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(f"{MODULE}.run", fake_run)
    return downloads, calls


def install_env(calls: list[tuple[list[str], dict]]) -> dict:
    return next(
        env
        for command, env in calls
        if command[0] == "bash" and command[1].endswith("install.sh")
    )


def test_install_wayland_service(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, True, False])
    downloads, calls = mock_scripts(monkeypatch)

    extension.install_extension()

    assert downloads == [
        f"{KLIPPERSCREEN_ESP_RELEASE_BASE}/desktop-linux-x86_64.tar.gz"
    ]
    assert install_env(calls)["SERVICE"] == "y"
    assert install_env(calls)["KR_BACKEND"] == "W"


def test_install_x11_service(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, True, True])
    _, calls = mock_scripts(monkeypatch)

    extension.install_extension()

    assert install_env(calls)["SERVICE"] == "y"
    assert install_env(calls)["KR_BACKEND"] == "X"


def test_service_lifecycle(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, True, False])
    _, calls = mock_scripts(monkeypatch)

    extension.install_extension()

    commands = [call[0] for call in calls]
    assert ["sudo", "systemctl", "stop", "KlipperScreen-esp.service"] in commands
    assert [
        "sudo",
        "rm",
        "-f",
        "/etc/systemd/system/KlipperScreen-esp.service.d/backend.conf",
    ] in commands
    assert ["sudo", "systemctl", "daemon-reload"] in commands
    assert ["sudo", "systemctl", "restart", "KlipperScreen-esp.service"] in commands


def test_service_lifecycle_uses_askpass_without_tty(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, True, False])
    _, calls = mock_scripts(monkeypatch)
    monkeypatch.setenv("SUDO_ASKPASS", "/tmp/askpass")
    monkeypatch.setattr(f"{MODULE}.sys.stdin.isatty", lambda: False)

    extension.install_extension()

    commands = [call[0] for call in calls]
    assert ["sudo", "-A", "systemctl", "stop", "KlipperScreen-esp.service"] in commands
    assert ["sudo", "-A", "systemctl", "daemon-reload"] in commands
    assert [
        "sudo",
        "-A",
        "systemctl",
        "restart",
        "KlipperScreen-esp.service",
    ] in commands


def test_install_desktop_app(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, False])
    _, calls = mock_scripts(monkeypatch)

    extension.install_extension()

    assert install_env(calls)["SERVICE"] == "n"
    assert install_env(calls)["KR_BACKEND"] == "W"


@pytest.mark.parametrize(
    ("machine", "package_arch"),
    [("armv7l", "armhf"), ("aarch64", "arm64"), ("x86_64", "x86_64")],
)
def test_install_architecture_mapping(
    monkeypatch, extension, machine, package_arch
) -> None:
    mock_answers(monkeypatch, [True, False])
    downloads, _ = mock_scripts(monkeypatch)
    monkeypatch.setattr(f"{MODULE}.platform.machine", lambda: machine)

    extension.install_extension()

    assert downloads[0].endswith(f"desktop-linux-{package_arch}.tar.gz")


def test_download_mirror_fallback(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, False])
    urls: list[str] = []
    results = iter([1, 1, 0])

    def fake_run(command: list[str], check: bool, env: dict | None = None):
        if command[0] == "curl":
            urls.append(command[-3])
            Path(command[-1]).write_text("ok", encoding="utf-8")
            return SimpleNamespace(returncode=next(results))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(f"{MODULE}.run", fake_run)
    extension.install_extension()

    assert urls[0].startswith(KLIPPERSCREEN_ESP_RELEASE_BASE)
    assert urls[1].startswith("https://ghproxy.net/")
    assert urls[2].startswith("https://gh-proxy.com/")


def test_cancel_install_runs_nothing(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [False])
    downloads, calls = mock_scripts(monkeypatch)

    extension.install_extension()

    assert not downloads
    assert not calls


def test_install_failure_is_reported(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True, False])
    downloads, _ = mock_scripts(monkeypatch)
    errors: list[str] = []
    monkeypatch.setattr(
        f"{MODULE}.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(CalledProcessError(1, "bash")),
    )
    monkeypatch.setattr(f"{MODULE}.Logger.print_error", errors.append)

    extension.install_extension()

    assert not downloads
    assert len(errors) == 1


def test_remove_extension(monkeypatch, extension) -> None:
    mock_answers(monkeypatch, [True])
    monkeypatch.setattr(f"{MODULE}.check_file_exist", lambda path: True)
    downloads, calls = mock_scripts(monkeypatch)

    extension.remove_extension()

    assert downloads == [KLIPPERSCREEN_ESP_UNINSTALL_SCRIPT]
    commands = [call[0] for call in calls]
    assert ["sudo", "systemctl", "stop", "KlipperScreen-esp.service"] in commands
    assert ["sudo", "systemctl", "daemon-reload"] in commands


def test_remove_missing_install_skips_scripts(monkeypatch, extension) -> None:
    monkeypatch.setattr(f"{MODULE}.check_file_exist", lambda path: False)
    downloads, calls = mock_scripts(monkeypatch)

    extension.remove_extension()

    assert not downloads
    assert not calls


def test_metadata() -> None:
    path = Path(__file__).parents[1].joinpath("klipperscreen_esp", "metadata.json")
    metadata = json.loads(path.read_text(encoding="utf-8"))["metadata"]

    assert metadata["index"] == 17
    assert metadata["module"] == "klipperscreen_esp_extension"
    assert metadata["updates"] is False
