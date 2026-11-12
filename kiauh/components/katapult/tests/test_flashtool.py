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

import subprocess
import sys
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List

import pytest
from components.katapult import flashtool
from components.katapult.flashtool import (
    Connection,
    FlashtoolTarget,
    build_flash_cmd,
    build_request_bootloader_cmd,
    check_katapult_running,
    find_canbus_uuids,
    find_uart_devices,
    find_usb_serial_devices,
    flash_with_flashtool,
    get_can_interfaces,
    is_interface_up,
)


def _can(uuid: str) -> FlashtoolTarget:
    return FlashtoolTarget(Connection.CAN, interface="can0", uuid=uuid)


def _make_net_dev(sysfs: Path, name: str, dev_type: str, flags: str) -> None:
    dev = sysfs.joinpath(name)
    dev.mkdir(parents=True)
    dev.joinpath("type").write_text(f"{dev_type}\n")
    dev.joinpath("flags").write_text(f"{flags}\n")


class TestCanInterfaces:
    def test_lists_only_can_interfaces(self, tmp_path: Path) -> None:
        _make_net_dev(tmp_path, "can1", "280", "0x41")
        _make_net_dev(tmp_path, "eth0", "1", "0x1003")
        _make_net_dev(tmp_path, "can0", "280", "0x40")
        assert get_can_interfaces(tmp_path) == ["can0", "can1"]

    def test_missing_sysfs_returns_empty(self, tmp_path: Path) -> None:
        assert get_can_interfaces(tmp_path.joinpath("missing")) == []

    @pytest.mark.parametrize(
        "flags, expected", [("0x40c1", True), ("0x40c0", False), ("", False)]
    )
    def test_is_interface_up(self, tmp_path: Path, flags: str, expected: bool) -> None:
        _make_net_dev(tmp_path, "can0", "280", flags)
        assert is_interface_up("can0", tmp_path) is expected

    def test_missing_interface_is_down(self, tmp_path: Path) -> None:
        assert is_interface_up("can0", tmp_path) is False


class TestFindCanbusUuids:
    def test_collects_uuids_with_sections(self, tmp_path: Path) -> None:
        tmp_path.joinpath("printer.cfg").write_text(
            "[include toolhead.cfg]\n"
            "[mcu]\n"
            "canbus_uuid: ABCDEF012345\n"
            "#canbus_uuid: 111111111111\n"
        )
        tmp_path.joinpath("hw").mkdir()
        tmp_path.joinpath("hw", "toolhead.cfg").write_text(
            "[mcu toolhead]\ncanbus_uuid = 0123456789ab  # EBB36\n"
        )

        assert find_canbus_uuids([tmp_path]) == [
            ("0123456789ab", "mcu toolhead"),
            ("abcdef012345", "mcu"),
        ]

    def test_ignores_save_config_backups_and_duplicates(self, tmp_path: Path) -> None:
        tmp_path.joinpath("printer.cfg").write_text(
            "[mcu]\ncanbus_uuid: abcdef012345\n"
        )
        tmp_path.joinpath("printer-20250101_120000.cfg").write_text(
            "[mcu]\ncanbus_uuid: 999999999999\n"
        )
        other = tmp_path.joinpath("other")
        other.mkdir()
        other.joinpath("printer.cfg").write_text("[mcu]\ncanbus_uuid: abcdef012345\n")

        assert find_canbus_uuids([tmp_path, other]) == [("abcdef012345", "mcu")]

    def test_ignores_invalid_uuids_and_missing_dirs(self, tmp_path: Path) -> None:
        tmp_path.joinpath("printer.cfg").write_text("[mcu]\ncanbus_uuid: 12345\n")
        assert find_canbus_uuids([tmp_path, tmp_path.joinpath("missing")]) == []


class TestSerialDevices:
    def test_usb_devices(self, tmp_path: Path) -> None:
        tmp_path.joinpath("usb-Klipper_stm32h723xx_1A00-if00").touch()
        tmp_path.joinpath("usb-katapult_stm32f103xe_2B00-if00").touch()
        assert find_usb_serial_devices(tmp_path) == [
            tmp_path.joinpath("usb-Klipper_stm32h723xx_1A00-if00").as_posix(),
            tmp_path.joinpath("usb-katapult_stm32f103xe_2B00-if00").as_posix(),
        ]

    def test_no_usb_devices(self, tmp_path: Path) -> None:
        assert find_usb_serial_devices(tmp_path.joinpath("by-id")) == []

    def test_uart_devices(self, tmp_path: Path) -> None:
        for dev in ["serial0", "ttyAMA0", "ttyS0", "ttyS1", "ttyUSB0"]:
            tmp_path.joinpath(dev).touch()
        assert find_uart_devices(tmp_path) == [
            tmp_path.joinpath(dev).as_posix() for dev in ["serial0", "ttyAMA0", "ttyS0"]
        ]


class TestCommands:
    def test_flash_cmd_passes_firmware_file(self, monkeypatch) -> None:
        monkeypatch.setattr(
            flashtool, "KATAPULT_FLASHTOOL_PATH", Path("/k/flashtool.py")
        )
        target = FlashtoolTarget(Connection.CAN, interface="can0", uuid="abcdef012345")
        assert build_flash_cmd(Path("/klipper/out/klipper.bin"), target) == [
            "python3",
            "/k/flashtool.py",
            "-f",
            "/klipper/out/klipper.bin",
            "-i",
            "can0",
            "-u",
            "abcdef012345",
        ]

    def test_request_bootloader_cmd(self, monkeypatch) -> None:
        monkeypatch.setattr(
            flashtool, "KATAPULT_FLASHTOOL_PATH", Path("/k/flashtool.py")
        )
        target = FlashtoolTarget(Connection.UART, device="/dev/ttyAMA0", baud=250000)
        assert build_request_bootloader_cmd(target) == [
            "python3",
            "/k/flashtool.py",
            "-d",
            "/dev/ttyAMA0",
            "-b",
            "250000",
            "-r",
        ]


class TestCheckKatapultRunning:
    def test_detects_running_flashtool(self, tmp_path: Path) -> None:
        script = tmp_path.joinpath("flashtool.py")
        script.write_text("import time\ntime.sleep(10)\n")
        proc = subprocess.Popen([sys.executable, script.as_posix()])
        try:
            time.sleep(0.2)
            assert check_katapult_running() is True
        finally:
            proc.kill()
            proc.wait()


class TestManualInput:
    @pytest.fixture
    def answer(self, monkeypatch):
        def set_answers(*answers: str) -> None:
            inputs = iter(answers)
            monkeypatch.setattr(
                flashtool, "get_string_input", lambda *a, **k: next(inputs)
            )

        monkeypatch.setattr(flashtool, "get_instances", lambda _: [])
        return set_answers

    def test_uuid_is_validated(self, answer) -> None:
        answer("xyz", "BD9DC195C7EB")
        assert flashtool._select_canbus_uuid(set()) == "bd9dc195c7eb"

    def test_uuid_entry_can_go_back(self, answer) -> None:
        answer("b")
        assert flashtool._select_canbus_uuid(set()) is None

    def test_uart_device_is_validated(self, answer) -> None:
        answer("/dev/does-not-exist", "/dev/null")
        assert flashtool._get_uart_device_input() == "/dev/null"

    def test_uart_device_entry_can_go_back(self, answer) -> None:
        answer("b")
        assert flashtool._get_uart_device_input() is None


class TestFlashWithFlashtool:
    @pytest.fixture
    def env(self, tmp_path: Path, monkeypatch) -> Dict[str, Any]:
        tool = tmp_path.joinpath("flashtool.py")
        tool.touch()
        firmware = tmp_path.joinpath("klipper.bin")
        firmware.touch()

        state: Dict[str, Any] = {
            "firmware": firmware,
            "calls": [],
            "fail": False,
            "stopped": False,
            "started": False,
            # answers to the confirmations, and the targets selected, in order
            "answers": [],
            "targets": [],
            "dialogs": [],
        }

        def fake_run(cmd: List[str], check: bool) -> None:
            state["calls"].append(cmd)
            if state["fail"]:
                raise CalledProcessError(1, cmd)

        def fake_stop(instances, operation_name) -> bool:
            state["stopped"] = True
            return True

        def fake_start(instances) -> None:
            state["started"] = True

        def fake_select(flashed_uuids) -> FlashtoolTarget | None:
            state.setdefault("flashed_seen", []).append(set(flashed_uuids))
            target: FlashtoolTarget | None = state["targets"].pop(0)
            return target

        monkeypatch.setattr(flashtool, "KATAPULT_FLASHTOOL_PATH", tool)
        monkeypatch.setattr(flashtool, "check_katapult_running", lambda: False)
        monkeypatch.setattr(flashtool, "install_flash_deps", lambda deps: True)
        monkeypatch.setattr(flashtool, "get_instances", lambda _: [])
        monkeypatch.setattr(
            flashtool, "get_confirm", lambda *a, **k: state["answers"].pop(0)
        )
        monkeypatch.setattr(
            flashtool.Logger,
            "print_dialog",
            lambda _type, content, **k: state["dialogs"].append(content),
        )
        monkeypatch.setattr(flashtool, "select_flashtool_target", fake_select)
        monkeypatch.setattr(
            flashtool, "stop_klipper_instances_interactively", fake_stop
        )
        monkeypatch.setattr(flashtool.InstanceManager, "start_all", fake_start)
        monkeypatch.setattr(flashtool, "run", fake_run)
        return state

    def test_uart_requests_bootloader_before_flashing(self, env) -> None:
        env["targets"] = [
            FlashtoolTarget(Connection.UART, device="/dev/ttyAMA0", baud=250000)
        ]
        env["answers"] = [True, False]

        flash_with_flashtool(env["firmware"], "flashing")

        assert [cmd[-1] for cmd in env["calls"]] == ["-r", "250000"]
        assert "-f" in env["calls"][1]
        assert env["started"] is True

    def test_flashes_several_mcus_with_klipper_stopped(self, env) -> None:
        env["targets"] = [
            _can("000000000000"),
            _can("111111111111"),
        ]
        # confirm T0, flash another, confirm T1, don't flash another
        env["answers"] = [True, True, True, False]

        flash_with_flashtool(env["firmware"], "flashing")

        assert [cmd[-1] for cmd in env["calls"]] == ["000000000000", "111111111111"]
        # T0 is marked as flashed when selecting the next MCU
        assert env["flashed_seen"] == [set(), {"000000000000"}]
        assert env["started"] is True

    def test_declining_the_next_mcu_restarts_klipper(self, env) -> None:
        env["targets"] = [
            _can("000000000000"),
            _can("111111111111"),
        ]
        # confirm T0, flash another, but don't confirm T1
        env["answers"] = [True, True, False]

        flash_with_flashtool(env["firmware"], "flashing")

        assert len(env["calls"]) == 1
        assert env["started"] is True

    def test_failed_flash_is_not_marked_as_flashed(self, env) -> None:
        env["targets"] = [
            _can("000000000000"),
            None,
        ]
        env["answers"] = [True, True]
        env["fail"] = True

        flash_with_flashtool(env["firmware"], "flashing")

        assert env["flashed_seen"] == [set(), set()]
        assert env["started"] is True

    def test_shows_firmware_info(self, env) -> None:
        env["targets"] = [FlashtoolTarget(Connection.USB, device="/dev/x")]
        env["answers"] = [False]

        flash_with_flashtool(env["firmware"], "flashing", ["MCU: stm32g0b1xx"])

        assert "MCU: stm32g0b1xx" in env["dialogs"][0]

    def test_nothing_happens_without_target(self, env) -> None:
        env["targets"] = [None]

        flash_with_flashtool(env["firmware"], "flashing")

        assert env["calls"] == []
        assert env["stopped"] is False

    def test_aborts_before_stopping_klipper(self, env) -> None:
        env["targets"] = [FlashtoolTarget(Connection.USB, device="/dev/x")]
        env["answers"] = [False]

        flash_with_flashtool(env["firmware"], "flashing")

        assert env["calls"] == []
        assert env["stopped"] is False

    def test_aborts_when_deps_are_not_installed(self, env, monkeypatch) -> None:
        monkeypatch.setattr(flashtool, "install_flash_deps", lambda deps: False)

        flash_with_flashtool(env["firmware"], "flashing")

        assert env["calls"] == []
        assert env["stopped"] is False

    def test_missing_firmware(self, env) -> None:
        flash_with_flashtool(env["firmware"].with_name("missing.bin"), "flashing")

        assert env["calls"] == []
