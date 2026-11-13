# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
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
from typing import Any, Dict, Iterator, List

import pytest
from components.katapult import klipper_flashing
from components.katapult.flashtool import Connection, FlashtoolTarget
from components.katapult.klipper_flashing import (
    RememberedMcu,
    describe_mcu,
    diff_firmware_config,
    forget_mcu,
    get_kconfig_mcu,
    load_remembered_mcus,
    offer_to_remember_mcu,
    save_remembered_mcus,
    update_all_mcus,
)
from components.klipper_firmware.flash_options import FlashOptions

HEAD = {"MCU": "stm32g0b1xx", "CLOCK_FREQ": 64000000, "CANBUS_FREQUENCY": 1000000}
MAIN = {"MCU": "stm32h723xx", "CLOCK_FREQ": 400000000}
VERSION = "v0.13.0-1-gabcdef12"


def _can(uuid: str) -> FlashtoolTarget:
    return FlashtoolTarget(Connection.CAN, interface="can0", uuid=uuid)


def _write_kconfig(kconfigs_dir: Path, name: str, mcu: str) -> Path:
    kconfigs_dir.mkdir(exist_ok=True)
    kconfig = kconfigs_dir.joinpath(name)
    kconfig.write_text(f'CONFIG_MACH_STM32=y\nCONFIG_MCU="{mcu}"\n')
    return kconfig


def _write_dict(dict_file: Path, config: Dict[str, Any]) -> None:
    dict_file.write_text(json.dumps({"config": config, "version": VERSION}))


class TestRememberedMcus:
    def test_round_trip(self, tmp_path: Path) -> None:
        file = tmp_path.joinpath("kconfigs", "mcus.json")
        mcus = [
            RememberedMcu(_can("aabbccddeeff"), "head.config", HEAD),
            RememberedMcu(
                FlashtoolTarget(Connection.USB, device="/dev/serial/by-id/x"),
                "main.config",
                MAIN,
            ),
            RememberedMcu(
                FlashtoolTarget(Connection.UART, device="/dev/ttyAMA0", baud=250000),
                "main.config",
                MAIN,
            ),
        ]

        save_remembered_mcus(mcus, file)

        assert load_remembered_mcus(file) == mcus
        data = json.loads(file.read_text())
        assert data["version"] == 1
        assert data["mcus"][0]["target"] == {
            "connection": "can",
            "interface": "can0",
            "uuid": "aabbccddeeff",
        }

    @pytest.mark.parametrize(
        "content",
        ["", "not json", "[]", '{"mcus": []}', '{"version": 2, "mcus": []}'],
    )
    def test_invalid_file(self, tmp_path: Path, content: str) -> None:
        file = tmp_path.joinpath("mcus.json")
        file.write_text(content)
        assert load_remembered_mcus(file) == []

    @pytest.mark.parametrize(
        "target",
        [
            {"connection": "spi", "device": "/dev/x"},
            {"connection": "can", "interface": "can0", "uuid": "xyz"},
            {"connection": "can", "uuid": "aabbccddeeff"},
            {"connection": "usb"},
            {"connection": "uart", "device": "/dev/ttyAMA0", "baud": "fast"},
            "can0",
        ],
    )
    def test_skips_invalid_entries(self, tmp_path: Path, target: Any) -> None:
        file = tmp_path.joinpath("mcus.json")
        valid = RememberedMcu(_can("aabbccddeeff"), "a.config", HEAD)
        save_remembered_mcus([valid], file)
        data = json.loads(file.read_text())
        data["mcus"].append({**data["mcus"][0], "target": target})
        data["mcus"].append({"kconfig": "b.config"})
        file.write_text(json.dumps(data))

        assert load_remembered_mcus(file) == [valid]

    def test_missing_file(self, tmp_path: Path) -> None:
        assert load_remembered_mcus(tmp_path.joinpath("missing.json")) == []


class TestHelpers:
    def test_kconfig_mcu(self, tmp_path: Path) -> None:
        kconfig = _write_kconfig(tmp_path, "a.config", "stm32g0b1xx")
        assert get_kconfig_mcu(kconfig) == "stm32g0b1xx"
        kconfig.write_text("CONFIG_MACH_STM32=y\n")
        assert get_kconfig_mcu(kconfig) is None
        assert get_kconfig_mcu(tmp_path.joinpath("missing")) is None

    def test_diff_ignores_settings_of_other_klipper_versions(self) -> None:
        assert diff_firmware_config(HEAD, {**HEAD, "NEW_SETTING": 1}) == []
        assert diff_firmware_config({**HEAD, "OLD_SETTING": 1}, HEAD) == []
        changed = {**HEAD, "MCU": "stm32g0b1xx", "CANBUS_FREQUENCY": 500000}
        assert diff_firmware_config(HEAD, changed) == ["CANBUS_FREQUENCY"]

    def test_describe_uses_the_config_section(self) -> None:
        mcu = RememberedMcu(_can("aabbccddeeff"), "t0.config", HEAD)
        assert describe_mcu(mcu, {"aabbccddeeff": "mcu T0"}) == "[mcu T0] aabbccddeeff"
        assert describe_mcu(mcu, {}) == "CAN interface can0, UUID aabbccddeeff"


class TestOfferToRememberMcu:
    @pytest.fixture
    def env(self, tmp_path: Path, monkeypatch) -> Iterator[Dict[str, Any]]:
        kconfigs_dir = tmp_path.joinpath("kconfigs")
        dict_file = tmp_path.joinpath("klipper.dict")
        _write_dict(dict_file, HEAD)
        state: Dict[str, Any] = {
            "kconfigs_dir": kconfigs_dir,
            "dict_file": dict_file,
            "mcus_file": kconfigs_dir.joinpath("mcus.json"),
            "answers": [],
            "questions": [],
            "numbers": [],
        }

        def fake_confirm(question: str, **kwargs: Any) -> bool:
            state["questions"].append(question)
            answer: bool = state["answers"].pop(0)
            return answer

        monkeypatch.setattr(klipper_flashing, "get_confirm", fake_confirm)
        monkeypatch.setattr(
            klipper_flashing,
            "get_number_input",
            lambda *a, **k: state["numbers"].pop(0),
        )
        monkeypatch.setattr(klipper_flashing, "get_mcu_sections", lambda: {})
        monkeypatch.setattr(
            klipper_flashing.Logger, "print_dialog", lambda *a, **k: None
        )
        FlashOptions.destroy()
        yield state
        FlashOptions.destroy()

    def _offer(self, env: Dict[str, Any], target: FlashtoolTarget) -> None:
        offer_to_remember_mcu(
            target, env["dict_file"], env["kconfigs_dir"], env["mcus_file"]
        )

    def test_needs_a_saved_config_for_the_mcu(self, env) -> None:
        _write_kconfig(env["kconfigs_dir"], "other.config", "rp2040")

        self._offer(env, _can("aabbccddeeff"))

        assert env["questions"] == []
        assert not env["mcus_file"].exists()

    def test_needs_the_firmware_dict(self, env) -> None:
        _write_kconfig(env["kconfigs_dir"], "t0.config", "stm32g0b1xx")
        env["dict_file"].unlink()

        self._offer(env, _can("aabbccddeeff"))

        assert env["questions"] == []

    def test_remembers_with_the_config_built_in_this_session(self, env) -> None:
        kconfig = _write_kconfig(env["kconfigs_dir"], "t0.config", "stm32g0b1xx")
        _write_kconfig(env["kconfigs_dir"], "t1.config", "stm32g0b1xx")
        kconfig.write_text(kconfig.read_text() + "CONFIG_CANBUS_FREQUENCY=1000000\n")
        FlashOptions().selected_kconfig = kconfig.as_posix()
        env["answers"] = [True]
        target = _can("aabbccddeeff")

        self._offer(env, target)

        assert "'t0.config'" in env["questions"][0]
        assert load_remembered_mcus(env["mcus_file"]) == [
            RememberedMcu(target, "t0.config", HEAD)
        ]

    def test_asks_for_the_config_without_a_build_in_this_session(
        self, env, monkeypatch
    ) -> None:
        # the default selected config is relative, and must not be read
        monkeypatch.chdir(env["kconfigs_dir"].parent)
        _write_kconfig(env["kconfigs_dir"], "a.config", "stm32g0b1xx")
        _write_kconfig(env["kconfigs_dir"], "b.config", "stm32g0b1xx")
        Path(".config").write_bytes(
            env["kconfigs_dir"].joinpath("a.config").read_bytes()
        )
        env["answers"] = [True]
        env["numbers"] = [2]
        target = _can("aabbccddeeff")

        self._offer(env, target)

        assert env["questions"] == ["Remember this MCU for updates?"]
        assert load_remembered_mcus(env["mcus_file"]) == [
            RememberedMcu(target, "b.config", HEAD)
        ]

    def test_replaces_an_mcu_flashed_with_other_settings(self, env) -> None:
        kconfig = _write_kconfig(env["kconfigs_dir"], "new.config", "stm32g0b1xx")
        target = _can("aabbccddeeff")
        other = RememberedMcu(_can("112233445566"), "old.config", MAIN)
        old_settings = {**HEAD, "CANBUS_FREQUENCY": 500000}
        save_remembered_mcus(
            [RememberedMcu(target, "old.config", old_settings), other],
            env["mcus_file"],
        )
        FlashOptions().selected_kconfig = kconfig.as_posix()
        env["answers"] = [True]

        self._offer(env, target)

        assert load_remembered_mcus(env["mcus_file"]) == [
            other,
            RememberedMcu(target, "new.config", HEAD),
        ]

    def test_doesnt_ask_again_for_the_same_settings(self, env) -> None:
        _write_kconfig(env["kconfigs_dir"], "t0.config", "stm32g0b1xx")
        target = _can("aabbccddeeff")
        save_remembered_mcus(
            [RememberedMcu(target, "t0.config", HEAD)], env["mcus_file"]
        )

        self._offer(env, target)

        assert env["questions"] == []

    def test_declined(self, env) -> None:
        kconfig = _write_kconfig(env["kconfigs_dir"], "t0.config", "stm32g0b1xx")
        FlashOptions().selected_kconfig = kconfig.as_posix()
        env["answers"] = [False]

        self._offer(env, _can("aabbccddeeff"))

        assert not env["mcus_file"].exists()


class _FakeInstance:
    def __init__(self, uds: Path) -> None:
        self.uds = uds


class TestUpdateAllMcus:
    @pytest.fixture
    def env(self, tmp_path: Path, monkeypatch) -> Dict[str, Any]:
        kconfigs_dir = tmp_path.joinpath("kconfigs")
        out_dir = tmp_path.joinpath("out")
        out_dir.mkdir()
        tool = tmp_path.joinpath("flashtool.py")
        tool.touch()

        state: Dict[str, Any] = {
            "kconfigs_dir": kconfigs_dir,
            "mcus_file": kconfigs_dir.joinpath("mcus.json"),
            "answers": [False, True],
            "built": [],
            "flashed": [],
            "events": [],
            "bridges": set(),
            "sections": {},
            "interfaces": {"can0": True},
            "fail_build": set(),
            "fail_flash": set(),
            # settings written to klipper.dict by the build of each config
            "settings": {"head.config": HEAD, "main.config": MAIN},
            "state": ("ready", ""),
            # the version reported by each section, the built one if missing
            "reported": {},
            "dialogs": [],
        }

        def fake_make(kconfig: Path) -> None:
            if kconfig.name in state["fail_build"]:
                raise CalledProcessError(2, "make")
            state["built"].append(kconfig.name)
            _write_dict(
                out_dir.joinpath("klipper.dict"), state["settings"][kconfig.name]
            )
            out_dir.joinpath("klipper.bin").write_text(kconfig.name)

        def fake_flash(firmware: Path, target: FlashtoolTarget) -> bool:
            state["events"].append("flash")
            state["flashed"].append((target.uuid, firmware.read_text()))
            return target.uuid not in state["fail_flash"]

        def fake_stop(instances, operation_name) -> bool:
            state["events"].append("stop")
            return True

        def fake_versions(uds: Path, sections: List[str]) -> Dict[str, str]:
            reported = {section: VERSION for section in sections}
            reported.update(state["reported"])
            return {s: v for s, v in reported.items() if s in sections and v}

        mod = klipper_flashing
        monkeypatch.setattr(mod, "KATAPULT_FLASHTOOL_PATH", tool)
        monkeypatch.setattr(
            mod, "KLIPPER_FIRMWARE_BIN", out_dir.joinpath("klipper.bin")
        )
        monkeypatch.setattr(
            mod, "KLIPPER_FIRMWARE_DICT", out_dir.joinpath("klipper.dict")
        )
        monkeypatch.setattr(mod, "check_katapult_running", lambda: False)
        monkeypatch.setattr(mod, "install_flash_deps", lambda deps: True)
        monkeypatch.setattr(mod, "find_can_bridge_uuids", lambda: state["bridges"])
        monkeypatch.setattr(mod, "get_mcu_sections", lambda: state["sections"])
        monkeypatch.setattr(
            mod, "get_can_interfaces", lambda: list(state["interfaces"])
        )
        monkeypatch.setattr(
            mod, "is_interface_up", lambda interface: state["interfaces"][interface]
        )
        monkeypatch.setattr(mod, "get_confirm", lambda *a, **k: state["answers"].pop(0))
        monkeypatch.setattr(
            mod,
            "run_make_clean",
            lambda kconfig=None: state["events"].append("clean"),
        )
        monkeypatch.setattr(mod, "run_make_menuconfig", lambda kconfig: None)
        monkeypatch.setattr(mod, "run_make", fake_make)
        monkeypatch.setattr(mod, "run_flashtool", fake_flash)
        monkeypatch.setattr(
            mod, "get_instances", lambda _: [_FakeInstance(tmp_path / "klippy.sock")]
        )
        monkeypatch.setattr(mod, "stop_klipper_instances_interactively", fake_stop)
        monkeypatch.setattr(
            mod.InstanceManager,
            "start_all",
            lambda instances: state["events"].append("start"),
        )
        monkeypatch.setattr(mod, "wait_until_ready", lambda uds: state["state"])
        monkeypatch.setattr(mod, "get_mcu_versions", fake_versions)
        monkeypatch.setattr(
            mod.Logger,
            "print_dialog",
            lambda _type, content, **k: state["dialogs"].append(content),
        )
        return state

    def _remember(self, env: Dict[str, Any], *mcus: tuple) -> None:
        remembered: List[RememberedMcu] = []
        for uuid, kconfig, section in mcus:
            settings = env["settings"][kconfig]
            if not env["kconfigs_dir"].joinpath(kconfig).exists():
                _write_kconfig(env["kconfigs_dir"], kconfig, settings["MCU"])
            remembered.append(RememberedMcu(_can(uuid), kconfig, settings))
            env["sections"][uuid] = section
        save_remembered_mcus(remembered, env["mcus_file"])

    def _update(self, env: Dict[str, Any]) -> List[str]:
        update_all_mcus(env["kconfigs_dir"], env["mcus_file"])
        results: List[str] = env["dialogs"][-1]
        return results

    def test_updates_toolheads_then_bridges(self, env) -> None:
        self._remember(
            env,
            ("000000000000", "main.config", "mcu"),
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("bbbbbbbbbbbb", "head.config", "mcu T1"),
        )
        env["bridges"] = {"000000000000"}

        results = self._update(env)

        assert env["built"] == ["head.config", "main.config"]
        assert env["flashed"] == [
            ("aaaaaaaaaaaa", "head.config"),
            ("bbbbbbbbbbbb", "head.config"),
            ("000000000000", "main.config"),
        ]
        assert env["events"] == [
            "clean",
            "clean",
            "clean",
            "stop",
            "flash",
            "flash",
            "flash",
            "start",
        ]
        assert results == [
            f"[mcu T0] aaaaaaaaaaaa: updated to {VERSION}",
            f"[mcu T1] bbbbbbbbbbbb: updated to {VERSION}",
            f"[mcu] 000000000000: updated to {VERSION}",
        ]

    def test_aborts_before_building(self, env) -> None:
        self._remember(env, ("aaaaaaaaaaaa", "head.config", "mcu T0"))
        env["answers"] = [False, False]

        update_all_mcus(env["kconfigs_dir"], env["mcus_file"])

        assert env["built"] == []
        assert env["events"] == []

    def test_skips_unavailable_mcus_before_stopping_klipper(self, env) -> None:
        self._remember(
            env,
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("bbbbbbbbbbbb", "head.config", "mcu T1"),
        )
        del env["sections"]["bbbbbbbbbbbb"]
        env["interfaces"] = {"can0": False}

        results = self._update(env)

        assert env["events"] == []
        assert results == [
            "[mcu T0] aaaaaaaaaaaa: skipped, CAN interface 'can0' is down",
            "CAN interface can0, UUID bbbbbbbbbbbb: skipped, CAN interface "
            "'can0' is down",
        ]

    def test_skips_mcus_removed_from_the_configs(self, env) -> None:
        self._remember(
            env,
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("bbbbbbbbbbbb", "head.config", "mcu T1"),
        )
        del env["sections"]["bbbbbbbbbbbb"]

        results = self._update(env)

        assert env["flashed"] == [("aaaaaaaaaaaa", "head.config")]
        assert results[-1] == (
            "CAN interface can0, UUID bbbbbbbbbbbb: skipped, its UUID isn't in "
            "the Klipper configs anymore"
        )

    def test_skips_missing_configs_and_devices(self, env) -> None:
        self._remember(env, ("aaaaaaaaaaaa", "head.config", "mcu T0"))
        mcus = load_remembered_mcus(env["mcus_file"])
        mcus.append(
            RememberedMcu(
                FlashtoolTarget(Connection.USB, device="/dev/serial/by-id/gone"),
                "head.config",
                HEAD,
            )
        )
        mcus.append(RememberedMcu(_can("cccccccccccc"), "gone.config", HEAD))
        save_remembered_mcus(mcus, env["mcus_file"])

        results = self._update(env)

        assert env["flashed"] == [("aaaaaaaaaaaa", "head.config")]
        assert results[1:] == [
            "USB /dev/serial/by-id/gone: skipped, device "
            "'/dev/serial/by-id/gone' not found",
            "CAN interface can0, UUID cccccccccccc: skipped, its firmware "
            "config 'gone.config' doesn't exist anymore",
        ]

    def test_skips_failed_builds(self, env) -> None:
        self._remember(
            env,
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("000000000000", "main.config", "mcu"),
        )
        env["fail_build"] = {"main.config"}

        results = self._update(env)

        assert env["flashed"] == [("aaaaaaaaaaaa", "head.config")]
        assert results[-1] == "[mcu] 000000000000: skipped, the build failed"

    def test_skips_mcus_whose_build_settings_changed(self, env) -> None:
        self._remember(env, ("aaaaaaaaaaaa", "head.config", "mcu T0"))
        # e.g. the saved config of another board with the same MCU was chosen
        env["settings"]["head.config"] = {**HEAD, "CANBUS_FREQUENCY": 500000}

        results = self._update(env)

        assert env["flashed"] == []
        assert "stop" not in env["events"]
        assert results == [
            "[mcu T0] aaaaaaaaaaaa: skipped, the build settings differ "
            "(CANBUS_FREQUENCY)"
        ]

    def test_reports_failed_flashes_and_restarts_klipper(self, env) -> None:
        self._remember(
            env,
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("bbbbbbbbbbbb", "head.config", "mcu T1"),
        )
        env["fail_flash"] = {"aaaaaaaaaaaa"}

        results = self._update(env)

        assert env["events"][-1] == "start"
        assert results == [
            f"[mcu T1] bbbbbbbbbbbb: updated to {VERSION}",
            "[mcu T0] aaaaaaaaaaaa: flashing failed",
        ]

    def test_reports_mcus_running_another_version(self, env) -> None:
        self._remember(
            env,
            ("aaaaaaaaaaaa", "head.config", "mcu T0"),
            ("bbbbbbbbbbbb", "head.config", "mcu T1"),
        )
        env["state"] = ("error", "mcu 'T1': Unable to connect\nOnce the issue...")
        env["reported"] = {"mcu T0": "v0.12.0", "mcu T1": ""}

        results = self._update(env)

        assert results == [
            "[mcu T0] aaaaaaaaaaaa: flashed, but it reports v0.12.0",
            "[mcu T1] bbbbbbbbbbbb: flashed, but not connected (mcu 'T1': "
            "Unable to connect)",
        ]

    def test_nothing_remembered(self, env) -> None:
        update_all_mcus(env["kconfigs_dir"], env["mcus_file"])

        assert env["built"] == []
        assert "No MCU to update!" in env["dialogs"][0]


class TestForgetMcu:
    def test_forgets_the_selected_mcu(self, tmp_path: Path, monkeypatch) -> None:
        file = tmp_path.joinpath("mcus.json")
        t0 = RememberedMcu(_can("aaaaaaaaaaaa"), "head.config", HEAD)
        t1 = RememberedMcu(_can("bbbbbbbbbbbb"), "head.config", HEAD)
        save_remembered_mcus([t0, t1], file)
        monkeypatch.setattr(klipper_flashing, "get_mcu_sections", lambda: {})
        monkeypatch.setattr(klipper_flashing, "get_number_input", lambda *a, **k: 1)
        monkeypatch.setattr(
            klipper_flashing.Logger, "print_dialog", lambda *a, **k: None
        )

        forget_mcu(file)

        assert load_remembered_mcus(file) == [t1]

    def test_going_back_keeps_all_mcus(self, tmp_path: Path, monkeypatch) -> None:
        file = tmp_path.joinpath("mcus.json")
        t0 = RememberedMcu(_can("aaaaaaaaaaaa"), "head.config", HEAD)
        save_remembered_mcus([t0], file)
        monkeypatch.setattr(klipper_flashing, "get_mcu_sections", lambda: {})
        monkeypatch.setattr(klipper_flashing, "get_number_input", lambda *a, **k: None)
        monkeypatch.setattr(
            klipper_flashing.Logger, "print_dialog", lambda *a, **k: None
        )

        forget_mcu(file)

        assert load_remembered_mcus(file) == [t0]
