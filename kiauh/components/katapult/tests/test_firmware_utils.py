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

from pathlib import Path
from typing import List

import pytest
from components.katapult import firmware_utils
from components.katapult.firmware_utils import (
    KatapultArch,
    find_usb_rp2_boot_devices,
    get_kconfig_arch,
    run_make_flash,
)

LSUSB_OUTPUT = """\
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 004: ID 2e8a:0003 Raspberry Pi RP2 Boot
Bus 001 Device 005: ID 0483:df11 STMicroelectronics STM Device in DFU Mode
Bus 001 Device 006: ID 2e8a:000f Raspberry Pi RP2350 Boot
Bus 001 Device 007: ID 2e8a:00031 Not a boot device
"""


class TestGetKconfigArch:
    @pytest.mark.parametrize(
        "line, arch",
        [
            ("CONFIG_MACH_STM32=y", KatapultArch.STM32),
            ("CONFIG_MACH_RPXXXX=y", KatapultArch.RP2),
            ("CONFIG_MACH_LPC176X=y", KatapultArch.LPC176X),
        ],
    )
    def test_reads_arch(self, tmp_path: Path, line: str, arch: KatapultArch) -> None:
        kconfig = tmp_path.joinpath(".config")
        kconfig.write_text(f'CONFIG_LOW_LEVEL_OPTIONS=y\n{line}\nCONFIG_MCU="x"\n')
        assert get_kconfig_arch(kconfig) is arch

    def test_ignores_unset_options(self, tmp_path: Path) -> None:
        kconfig = tmp_path.joinpath(".config")
        kconfig.write_text("# CONFIG_MACH_STM32 is not set\n")
        assert get_kconfig_arch(kconfig) is None

    def test_missing_config(self, tmp_path: Path) -> None:
        assert get_kconfig_arch(tmp_path.joinpath(".config")) is None


class TestFindRp2BootDevices:
    def test_parses_lsusb(self, monkeypatch) -> None:
        monkeypatch.setattr(
            firmware_utils, "check_output", lambda *a, **k: LSUSB_OUTPUT
        )
        assert find_usb_rp2_boot_devices() == ["2e8a:0003", "2e8a:000f"]

    def test_lsusb_missing(self, monkeypatch) -> None:
        def missing(*args, **kwargs):
            raise FileNotFoundError("lsusb")

        monkeypatch.setattr(firmware_utils, "check_output", missing)
        assert find_usb_rp2_boot_devices() == []


class TestRunMakeFlash:
    @pytest.fixture
    def calls(self, monkeypatch) -> List[List[str]]:
        calls: List[List[str]] = []
        monkeypatch.setattr(
            firmware_utils, "run_make_clean", lambda kconfig: calls.append(["clean"])
        )
        monkeypatch.setattr(
            firmware_utils, "run", lambda cmd, cwd, check: calls.append(cmd)
        )
        return calls

    def test_cleans_before_flashing_dfu_device(self, calls) -> None:
        run_make_flash(Path("/cfg/stm32.config"), "0483:df11")
        assert calls == [
            ["clean"],
            [
                "make",
                "PYTHON=python3",
                "KCONFIG_CONFIG=/cfg/stm32.config",
                "flash",
                "FLASH_DEVICE=0483:df11",
            ],
        ]

    def test_no_flash_device_for_rp2(self, calls) -> None:
        run_make_flash(Path("/cfg/rp2040.config"))
        assert calls[-1] == [
            "make",
            "PYTHON=python3",
            "KCONFIG_CONFIG=/cfg/rp2040.config",
            "flash",
        ]
