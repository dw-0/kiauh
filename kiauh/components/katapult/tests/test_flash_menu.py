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
from components.katapult.firmware_utils import KatapultArch
from components.katapult.menus import katapult_flash_menu
from components.katapult.menus.katapult_flash_menu import (
    KatapultFlashMethodMenu,
    check_deployer_built,
    select_flash_device,
)


class TestSelectFlashDevice:
    def test_single_dfu_device(self, monkeypatch) -> None:
        monkeypatch.setattr(
            katapult_flash_menu, "find_usb_dfu_device", lambda: ["0483:df11"]
        )
        assert select_flash_device(KatapultArch.STM32) == "0483:df11"

    def test_no_device(self, monkeypatch) -> None:
        monkeypatch.setattr(
            katapult_flash_menu, "find_usb_rp2_boot_devices", lambda: []
        )
        assert select_flash_device(KatapultArch.RP2) is None

    def test_refuses_multiple_rp2_devices(self, monkeypatch) -> None:
        monkeypatch.setattr(
            katapult_flash_menu,
            "find_usb_rp2_boot_devices",
            lambda: ["2e8a:0003", "2e8a:0003"],
        )
        assert select_flash_device(KatapultArch.RP2) is None

    def test_selects_one_of_multiple_dfu_devices(self, monkeypatch) -> None:
        monkeypatch.setattr(
            katapult_flash_menu,
            "find_usb_dfu_device",
            lambda: ["0483:df11", "28e9:0189"],
        )
        monkeypatch.setattr(katapult_flash_menu, "get_number_input", lambda *a, **k: 2)
        assert select_flash_device(KatapultArch.STM32) == "28e9:0189"


class TestFlashDirectly:
    @pytest.fixture
    def flashed(self, tmp_path: Path, monkeypatch) -> List[tuple]:
        flashed: List[tuple] = []

        class FakeKConfigMenu:
            def run(self) -> None:
                pass

        class FakeFlashOptions:
            selected_kconfig = tmp_path.joinpath(".config").as_posix()

        monkeypatch.setattr(katapult_flash_menu, "KatapultKConfigMenu", FakeKConfigMenu)
        monkeypatch.setattr(katapult_flash_menu, "FlashOptions", FakeFlashOptions)
        monkeypatch.setattr(
            katapult_flash_menu, "install_flash_deps", lambda arch: True
        )
        monkeypatch.setattr(katapult_flash_menu, "get_confirm", lambda *a, **k: True)
        monkeypatch.setattr(
            katapult_flash_menu,
            "run_make_flash",
            lambda kconfig, device: flashed.append((kconfig, device)),
        )
        return flashed

    def _write_kconfig(self, tmp_path: Path, line: str) -> Path:
        kconfig = tmp_path.joinpath(".config")
        kconfig.write_text(f"{line}\n")
        return kconfig

    def test_flashes_stm32_dfu_device(
        self, flashed, tmp_path: Path, monkeypatch
    ) -> None:
        kconfig = self._write_kconfig(tmp_path, "CONFIG_MACH_STM32=y")
        monkeypatch.setattr(
            katapult_flash_menu, "find_usb_dfu_device", lambda: ["0483:df11"]
        )

        KatapultFlashMethodMenu().flash_directly()

        assert flashed == [(kconfig, "0483:df11")]

    def test_flashes_rp2_without_flash_device(
        self, flashed, tmp_path: Path, monkeypatch
    ) -> None:
        kconfig = self._write_kconfig(tmp_path, "CONFIG_MACH_RPXXXX=y")
        monkeypatch.setattr(
            katapult_flash_menu, "find_usb_rp2_boot_devices", lambda: ["2e8a:0003"]
        )

        KatapultFlashMethodMenu().flash_directly()

        assert flashed == [(kconfig, None)]

    def test_refuses_unsupported_arch(self, flashed, tmp_path: Path) -> None:
        self._write_kconfig(tmp_path, "CONFIG_MACH_LPC176X=y")

        KatapultFlashMethodMenu().flash_directly()

        assert flashed == []

    def test_aborts_without_confirmation(
        self, flashed, tmp_path: Path, monkeypatch
    ) -> None:
        self._write_kconfig(tmp_path, "CONFIG_MACH_STM32=y")
        monkeypatch.setattr(
            katapult_flash_menu, "find_usb_dfu_device", lambda: ["0483:df11"]
        )
        monkeypatch.setattr(katapult_flash_menu, "get_confirm", lambda *a, **k: False)

        KatapultFlashMethodMenu().flash_directly()

        assert flashed == []


class TestDeployer:
    def test_requires_deployer(self, tmp_path: Path, monkeypatch) -> None:
        tool = tmp_path.joinpath("flashtool.py")
        tool.touch()
        monkeypatch.setattr(katapult_flash_menu, "KATAPULT_FLASHTOOL_PATH", tool)
        monkeypatch.setattr(
            katapult_flash_menu,
            "KATAPULT_DEPLOYER_BIN",
            tmp_path.joinpath("deployer.bin"),
        )
        assert check_deployer_built() is False

        tmp_path.joinpath("deployer.bin").touch()
        assert check_deployer_built() is True

    def test_update_flashes_deployer(self, tmp_path: Path, monkeypatch) -> None:
        flashed: List[Path] = []
        monkeypatch.setattr(katapult_flash_menu, "check_deployer_built", lambda: True)
        monkeypatch.setattr(
            katapult_flash_menu,
            "flash_with_flashtool",
            lambda firmware, operation: flashed.append(firmware),
        )

        KatapultFlashMethodMenu().update_through_katapult()

        assert flashed == [katapult_flash_menu.KATAPULT_DEPLOYER_BIN]
