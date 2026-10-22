# ======================================================================= #
#  Copyright (C) 2026 Ahmed Bebars                                        #
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
from typing import List

import pytest
from extensions.klipper_auto_eject import klipper_auto_eject_extension as ext_mod
from extensions.klipper_auto_eject.klipper_auto_eject_extension import (
    KlipperAutoEjectExtension,
)

EXT_DIR = Path(__file__).resolve().parent.parent.joinpath("klipper_auto_eject")


class FakeBase:
    def __init__(self, cfg_dir: Path) -> None:
        self.cfg_dir = cfg_dir


class FakeKlipper:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.base = FakeBase(data_dir.joinpath("config"))


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The extension with Klipper, git, systemd and the installer faked."""
    calls: List[tuple] = []
    repo = tmp_path.joinpath("klipper-auto-eject")
    service = tmp_path.joinpath("klipper-auto-eject.service")
    printers = [FakeKlipper(tmp_path.joinpath("printer_data"))]

    monkeypatch.setattr(ext_mod, "AE_DIR", repo)
    monkeypatch.setattr(ext_mod, "AE_INSTALL_SCRIPT", repo.joinpath("install.sh"))
    monkeypatch.setattr(ext_mod, "AE_SERVICE_FILE", service)
    monkeypatch.setattr(ext_mod, "get_instances", lambda _cls: printers)
    monkeypatch.setattr(
        ext_mod,
        "git_clone_wrapper",
        lambda url, target: (calls.append(("clone", url)), target.mkdir()),
    )
    monkeypatch.setattr(ext_mod, "git_pull_wrapper", lambda d: calls.append(("pull",)))
    monkeypatch.setattr(
        ext_mod, "cmd_sysctl_service", lambda n, a: calls.append(("systemctl", a, n))
    )
    monkeypatch.setattr(
        ext_mod, "run", lambda cmd, check: calls.append(("run", *cmd[2:]))
    )
    monkeypatch.setattr(
        ext_mod, "run_remove_routines", lambda p: calls.append(("remove", p.name))
    )
    monkeypatch.setattr(ext_mod, "get_confirm", lambda *a, **k: True)

    class Settings:
        class kiauh:  # noqa: N801
            backup_before_update = False

    monkeypatch.setattr(ext_mod, "KiauhSettings", Settings)
    return {
        "calls": calls,
        "repo": repo,
        "service": service,
        "printers": printers,
        "ext": KlipperAutoEjectExtension({}),
    }


class TestKlipperAutoEjectExtension:
    def test_metadata(self) -> None:
        meta = json.loads(EXT_DIR.joinpath("metadata.json").read_text())["metadata"]
        assert meta["module"] == "klipper_auto_eject_extension"
        assert EXT_DIR.joinpath(meta["module"] + ".py").exists()
        assert meta["updates"] is True
        # no other extension uses its index
        others = [
            json.loads(p.read_text())["metadata"]["index"]
            for p in EXT_DIR.parent.glob("*/metadata.json")
            if p.parent != EXT_DIR
        ]
        assert meta["index"] not in others

    def test_install_clones_then_runs_its_installer(self, env) -> None:
        env["ext"].install_extension()
        cfg = env["printers"][0].base.cfg_dir.as_posix()
        assert env["calls"] == [
            ("clone", "https://github.com/ahmedbebars/klipper-auto-eject.git"),
            ("run", "--config-dir", cfg),
        ]

    def test_install_runs_the_installer_for_each_printer(self, env, tmp_path) -> None:
        env["printers"].append(FakeKlipper(tmp_path.joinpath("printer_2_data")))
        env["ext"].install_extension()
        runs = [c for c in env["calls"] if c[0] == "run"]
        assert [r[2] for r in runs] == [
            p.base.cfg_dir.as_posix() for p in env["printers"]
        ]

    def test_installed_already_runs_the_installer_again(self, env) -> None:
        env["repo"].mkdir()
        env["ext"].install_extension()
        assert [c[0] for c in env["calls"]] == ["run"]

    def test_install_without_klipper_does_nothing(self, env) -> None:
        env["printers"].clear()
        env["ext"].install_extension()
        assert env["calls"] == []

    def test_install_stops_when_the_installer_fails(self, env, monkeypatch) -> None:
        def fail(cmd, check):
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(ext_mod, "run", fail)
        env["ext"].install_extension()  # logs the error, does not raise

    def test_update_pulls_and_restarts_the_service(self, env) -> None:
        env["repo"].mkdir()
        env["service"].touch()
        env["ext"].update_extension()
        assert env["calls"] == [
            ("pull",),
            ("systemctl", "restart", "klipper-auto-eject.service"),
        ]

    def test_update_without_the_service_only_pulls(self, env) -> None:
        env["repo"].mkdir()
        env["ext"].update_extension()
        assert env["calls"] == [("pull",)]

    def test_update_when_not_installed_does_nothing(self, env) -> None:
        env["ext"].update_extension()
        assert env["calls"] == []

    def test_remove_uninstalls_then_deletes_the_repository(self, env) -> None:
        env["repo"].mkdir()
        env["ext"].remove_extension()
        cfg = env["printers"][0].base.cfg_dir.as_posix()
        assert env["calls"] == [
            ("run", "--uninstall", "--config-dir", cfg),
            ("remove", "klipper-auto-eject"),
        ]

    def test_remove_keeps_the_repository_when_uninstalling_fails(
        self, env, monkeypatch
    ) -> None:
        env["repo"].mkdir()

        def fail(cmd, check):
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(ext_mod, "run", fail)
        env["ext"].remove_extension()
        assert ("remove", "klipper-auto-eject") not in env["calls"]
