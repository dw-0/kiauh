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

import re
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List, Tuple

from components.katapult import KATAPULT_FLASHTOOL_PATH
from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from utils.input_utils import (
    get_confirm,
    get_number_input,
    get_selection_input,
    get_string_input,
)
from utils.instance_utils import get_instances, stop_klipper_instances_interactively
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)

SYSFS_NET_DIR = Path("/sys/class/net")
SERIAL_BY_ID_DIR = Path("/dev/serial/by-id")
UART_DEVICE_PATTERNS = ["serial[0-9]", "ttyAMA[0-9]*", "ttyS0"]
DEFAULT_SERIAL_BAUD = 250000
# flashtool needs pyserial for USB and UART targets, but also for CAN when the
# target is a USB to CAN bridge, as it then switches over to its USB serial port
FLASHTOOL_DEPS = {"python3-serial"}

# interface type of CAN network devices, see linux/if_arp.h
ARPHRD_CAN = "280"
IFF_UP = 0x1

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{12}$")
SECTION_REGEX = re.compile(r"^\[([^\]]+)\]")
CANBUS_UUID_REGEX = re.compile(r"^canbus_uuid\s*[:=]\s*([0-9a-fA-F]{12})\s*([#;].*)?$")
# backups created by Klipper's SAVE_CONFIG, e.g. printer-20250101_120000.cfg
CFG_BACKUP_REGEX = re.compile(r"^printer-\d{8}_\d{6}\.cfg$")


@dataclass
class FlashtoolTarget:
    description: str
    args: List[str]
    # MCUs connected over UART can't be put into the bootloader automatically
    # by flashtool, so the bootloader has to be requested before flashing
    request_bootloader: bool = False


def check_katapult_running() -> bool:
    """Check if a Katapult flashtool.py process is currently running"""
    for cmdline in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            args = cmdline.read_bytes().split(b"\0")
        except OSError:
            # the process exited or is not readable by the current user
            continue
        if any(arg.endswith(b"flashtool.py") for arg in args):
            return True
    return False


def get_can_interfaces(sysfs_net_dir: Path = SYSFS_NET_DIR) -> List[str]:
    if not sysfs_net_dir.is_dir():
        return []
    return sorted(
        intf.name
        for intf in sysfs_net_dir.iterdir()
        if _read_sysfs(intf.joinpath("type")) == ARPHRD_CAN
    )


def is_interface_up(interface: str, sysfs_net_dir: Path = SYSFS_NET_DIR) -> bool:
    flags = _read_sysfs(sysfs_net_dir.joinpath(interface, "flags"))
    try:
        return bool(int(flags, 16) & IFF_UP)
    except ValueError:
        return False


def _read_sysfs(path: Path) -> str:
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def find_canbus_uuids(cfg_dirs: List[Path]) -> List[Tuple[str, str]]:
    """
    Collect the 'canbus_uuid' values from the Klipper configs |
    :param cfg_dirs: The config directories to search for *.cfg files
    :return: A list of (uuid, config section) tuples, without duplicates
    """
    uuids: List[Tuple[str, str]] = []
    for cfg_dir in cfg_dirs:
        if not cfg_dir.is_dir():
            continue
        for cfg_file in sorted(cfg_dir.rglob("*.cfg")):
            if CFG_BACKUP_REGEX.match(cfg_file.name):
                continue
            try:
                lines = cfg_file.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            section = ""
            for line in lines:
                line = line.strip()
                if section_match := SECTION_REGEX.match(line):
                    section = section_match.group(1).strip()
                elif uuid_match := CANBUS_UUID_REGEX.match(line):
                    uuid = uuid_match.group(1).lower()
                    if uuid not in [u for u, _ in uuids]:
                        uuids.append((uuid, section))
    return uuids


def find_usb_serial_devices(by_id_dir: Path = SERIAL_BY_ID_DIR) -> List[str]:
    if not by_id_dir.is_dir():
        return []
    return sorted(dev.as_posix() for dev in by_id_dir.iterdir())


def find_uart_devices(dev_dir: Path = Path("/dev")) -> List[str]:
    devices: List[str] = []
    for pattern in UART_DEVICE_PATTERNS:
        devices += sorted(dev.as_posix() for dev in dev_dir.glob(pattern))
    return devices


def build_flash_cmd(firmware: Path, target: FlashtoolTarget) -> List[str]:
    return [
        "python3",
        KATAPULT_FLASHTOOL_PATH.as_posix(),
        "-f",
        firmware.as_posix(),
        *target.args,
    ]


def build_request_bootloader_cmd(target: FlashtoolTarget) -> List[str]:
    return ["python3", KATAPULT_FLASHTOOL_PATH.as_posix(), *target.args, "-r"]


def flash_with_flashtool(firmware: Path, operation_name: str) -> None:
    """
    Interactively flash a firmware file to an MCU running Katapult |
    :param firmware: The firmware file to flash
    :param operation_name: Name of the operation for user messaging, not capitalized
    :return: None
    """
    if not KATAPULT_FLASHTOOL_PATH.is_file():
        Logger.print_error("Katapult is not installed! Install it first.")
        return
    if not firmware.is_file():
        Logger.print_error(f"Firmware file '{firmware}' not found!")
        return
    if check_katapult_running():
        Logger.print_error("Katapult's flashtool is already running! Aborting.")
        return
    if not install_flashtool_deps():
        return

    target = select_flashtool_target()
    if target is None:
        return

    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            f"Firmware: {firmware}",
            f"Target: {target.description}",
            "\n\n",
            "Make sure the firmware was built for this MCU, with a bootloader "
            "offset matching the application offset of Katapult on it.",
        ],
    )
    if not get_confirm("Start flashing?", default_choice=False):
        Logger.print_info(f"{operation_name.capitalize()} aborted!")
        return

    instances: List[Klipper] = get_instances(Klipper)
    if not stop_klipper_instances_interactively(instances, operation_name):
        return

    try:
        if target.request_bootloader:
            Logger.print_status("Requesting the bootloader ...")
            run(build_request_bootloader_cmd(target), check=True)

        Logger.print_status(f"Flashing '{firmware.name}' ...")
        run(build_flash_cmd(firmware, target), check=True)
        Logger.print_ok("Flashing successful!", start="\n", end="\n\n")
    except CalledProcessError:
        Logger.print_error("Flashing failed! See the flashtool output above.")
    finally:
        InstanceManager.start_all(instances)


def install_flashtool_deps() -> bool:
    missing_deps = check_package_install(FLASHTOOL_DEPS)
    if not missing_deps:
        return True

    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            "Katapult's flashtool requires the following packages:",
            *[f"● {dep}" for dep in missing_deps],
        ],
    )
    if not get_confirm("Install the missing packages now?"):
        Logger.print_info("Flashing aborted!")
        return False

    try:
        update_system_package_lists(silent=False)
        install_system_packages(missing_deps)
        return True
    except Exception as e:
        Logger.print_error(f"Installing the flashtool dependencies failed!\n{e}")
        return False


def select_flashtool_target() -> FlashtoolTarget | None:
    Logger.print_dialog(
        DialogType.CUSTOM,
        [
            "How is the MCU connected to the host?",
            "\n\n",
            "1) CAN bus (including USB to CAN bridge MCUs)",
            "2) USB",
            "3) UART",
        ],
        custom_title="Select connection",
    )
    choice = get_selection_input("Select connection (b=back)", ["1", "2", "3", "b"])

    if choice == "1":
        return _select_can_target()
    elif choice == "2":
        return _select_usb_target()
    elif choice == "3":
        return _select_uart_target()
    return None


def _select_can_target() -> FlashtoolTarget | None:
    interfaces = get_can_interfaces()
    if not interfaces:
        Logger.print_error("No CAN interface found! Set up the CAN interface first.")
        return None

    interface = _select_from_list("CAN interface", interfaces)
    if interface is None:
        return None
    if not is_interface_up(interface):
        Logger.print_error(f"CAN interface '{interface}' is down!")
        return None

    uuid = _select_canbus_uuid()
    if uuid is None:
        return None

    return FlashtoolTarget(
        description=f"CAN interface {interface}, UUID {uuid}",
        args=["-i", interface, "-u", uuid],
    )


def _select_canbus_uuid() -> str | None:
    cfg_dirs = [instance.base.cfg_dir for instance in get_instances(Klipper)]
    uuids = find_canbus_uuids(cfg_dirs)

    if uuids:
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                "The following UUIDs were found in your Klipper config:",
                "\n\n",
                *[
                    f"{i}) {uuid} [{section}]"
                    for i, (uuid, section) in enumerate(uuids, 1)
                ],
                "\n\n",
                "m) Enter a UUID manually",
            ],
            custom_title="Select MCU",
        )
        options = [str(i) for i in range(1, len(uuids) + 1)] + ["m", "b"]
        choice = get_selection_input("Select MCU to flash (b=back)", options)
        if choice == "b":
            return None
        if choice != "m":
            return uuids[int(choice) - 1][0]

    while True:
        uuid = get_string_input(
            "Enter the UUID of the MCU to flash (e.g. 'bd9dc195c7eb')"
        )
        if UUID_REGEX.match(uuid):
            return uuid.lower()
        Logger.print_error("A UUID consists of 12 hexadecimal characters!")


def _select_usb_target() -> FlashtoolTarget | None:
    devices = find_usb_serial_devices()
    if not devices:
        Logger.print_error(f"No USB device found in '{SERIAL_BY_ID_DIR}'!")
        return None

    device = _select_from_list("USB device", devices)
    if device is None:
        return None

    return FlashtoolTarget(description=f"USB {device}", args=["-d", device])


def _select_uart_target() -> FlashtoolTarget | None:
    devices = find_uart_devices()
    device: str | None
    if devices:
        device = _select_from_list("UART device", devices)
    else:
        device = _get_uart_device_input()
    if device is None:
        return None

    baud = get_number_input(
        "Enter the baud rate of the UART connection",
        min_value=1,
        default=DEFAULT_SERIAL_BAUD,
    )

    return FlashtoolTarget(
        description=f"UART {device} at {baud} baud",
        args=["-d", device, "-b", str(baud)],
        request_bootloader=True,
    )


def _get_uart_device_input() -> str:
    while True:
        device = get_string_input(
            "Enter the UART device path (e.g. /dev/ttyAMA0)",
            allow_special_chars=True,
        )
        if device.startswith("/dev/") and Path(device).exists():
            return device
        Logger.print_error(f"Device '{device}' not found!")


def _select_from_list(name: str, items: List[str]) -> str | None:
    if len(items) == 1:
        Logger.print_info(f"Using {name} '{items[0]}'")
        return items[0]

    Logger.print_dialog(
        DialogType.CUSTOM,
        [f"{i}) {item}" for i, item in enumerate(items, 1)],
        custom_title=f"Select {name}",
    )
    index = get_number_input(
        f"Select {name} (b=back)",
        min_value=1,
        max_value=len(items),
        allow_go_back=True,
    )
    return items[index - 1] if index is not None else None
