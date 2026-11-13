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
import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Callable, List, Set, Tuple

from components.katapult import KATAPULT_FLASHTOOL_PATH
from components.katapult.firmware_utils import install_flash_deps
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

SYSFS_NET_DIR = Path("/sys/class/net")
SYSFS_USB_DIR = Path("/sys/bus/usb/devices")
SERIAL_BY_ID_DIR = Path("/dev/serial/by-id")
UART_DEVICE_PATTERNS = ["serial[0-9]", "ttyAMA[0-9]*", "ttyS0"]
DEFAULT_SERIAL_BAUD = 250000
# flashtool needs pyserial for USB and UART targets, but also for CAN when the
# target is a USB to CAN bridge, as it then switches over to its USB serial port
FLASHTOOL_DEPS = {"python3-serial"}

# USB ID of Klipper running in USB to CAN bridge mode
CAN_BRIDGE_USB_ID = "1d50:606f"
# seed Klipper uses to derive the CAN UUID of a bridge from its serial number
CAN_BRIDGE_UUID_SEED = 0xA16231A7
MASK_64 = 0xFFFFFFFFFFFFFFFF

# interface type of CAN network devices, see linux/if_arp.h
ARPHRD_CAN = "280"
IFF_UP = 0x1

UUID_REGEX = re.compile(r"^[0-9a-fA-F]{12}$")
SECTION_REGEX = re.compile(r"^\[([^\]]+)\]")
CANBUS_UUID_REGEX = re.compile(r"^canbus_uuid\s*[:=]\s*([0-9a-fA-F]{12})\s*([#;].*)?$")
# backups created by Klipper's SAVE_CONFIG, e.g. printer-20250101_120000.cfg
CFG_BACKUP_REGEX = re.compile(r"^printer-\d{8}_\d{6}\.cfg$")


class Connection(Enum):
    CAN = "can"
    USB = "usb"
    UART = "uart"


@dataclass(frozen=True)
class FlashtoolTarget:
    connection: Connection
    # CAN interface and UUID of CAN targets
    interface: str | None = None
    uuid: str | None = None
    # serial device of USB and UART targets, and the baud rate of UART targets
    device: str | None = None
    baud: int | None = None

    @property
    def description(self) -> str:
        if self.connection is Connection.CAN:
            return f"CAN interface {self.interface}, UUID {self.uuid}"
        if self.connection is Connection.USB:
            return f"USB {self.device}"
        return f"UART {self.device} at {self.baud} baud"

    @property
    def args(self) -> List[str]:
        if self.connection is Connection.CAN:
            return ["-i", str(self.interface), "-u", str(self.uuid)]
        if self.connection is Connection.USB:
            return ["-d", str(self.device)]
        return ["-d", str(self.device), "-b", str(self.baud)]

    @property
    def request_bootloader(self) -> bool:
        # MCUs connected over UART can't be put into the bootloader automatically
        # by flashtool, so the bootloader has to be requested before flashing
        return self.connection is Connection.UART


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


def find_can_bridge_uuids(sysfs_usb_dir: Path = SYSFS_USB_DIR) -> Set[str]:
    """
    Find the CAN UUIDs of the USB to CAN bridge MCUs running Klipper, the same
    way flashtool does, without sending anything on the CAN bus |
    :param sysfs_usb_dir: The sysfs directory of the USB devices
    :return: The CAN UUIDs of the connected bridges
    """
    if not sysfs_usb_dir.is_dir():
        return set()

    uuids: Set[str] = set()
    for device in sysfs_usb_dir.iterdir():
        vendor = _read_sysfs(device.joinpath("idVendor")).lower()
        product = _read_sysfs(device.joinpath("idProduct")).lower()
        manufacturer = _read_sysfs(device.joinpath("manufacturer")).lower()
        serial = _read_sysfs(device.joinpath("serial"))
        if f"{vendor}:{product}" != CAN_BRIDGE_USB_ID or manufacturer != "klipper":
            continue
        try:
            uuids.add(convert_serial_to_can_uuid(serial))
        except ValueError:
            continue
    return uuids


def convert_serial_to_can_uuid(serial: str) -> str:
    """
    Derive the CAN UUID of a USB to CAN bridge from its USB serial number, which
    is the chip ID of the MCU, as Klipper does |
    :param serial: The USB serial number, in hex
    :return: The CAN UUID
    """
    result = _fasthash64(bytes.fromhex(serial), CAN_BRIDGE_UUID_SEED)
    # the UUID reported by Klipper is byteswapped
    uuid = 0
    for i in range(6):
        uuid |= ((result >> (i * 8)) & 0xFF) << ((5 - i) * 8)
    return f"{uuid:012x}"


def _fasthash64(buffer: bytes, seed: int) -> int:
    """Port of the fasthash64 function used by Klipper and flashtool"""

    def mix(value: int) -> int:
        value ^= value >> 23
        value = (value * 0x2127599BF4325C37) & MASK_64
        value ^= value >> 47
        return value

    m = 0x880355F21E6D1965
    h = seed ^ ((len(buffer) * m) & MASK_64)
    long_count = len(buffer) // 8
    for value in struct.unpack(f"<{long_count}Q", buffer[: long_count * 8]):
        h ^= mix(value)
        h = (h * m) & MASK_64
    remaining = buffer[long_count * 8 :]
    if remaining:
        h ^= mix(int.from_bytes(remaining, "little"))
        h = (h * m) & MASK_64
    return mix(h)


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


def flash_with_flashtool(
    firmware: Path,
    operation_name: str,
    firmware_info: List[str] | None = None,
    on_flashed: Callable[[FlashtoolTarget], None] | None = None,
) -> None:
    """
    Interactively flash a firmware file to one or more MCUs running Katapult.
    Klipper stays stopped until the last MCU was flashed. |
    :param firmware: The firmware file to flash
    :param operation_name: Name of the operation for user messaging, not capitalized
    :param firmware_info: Optional details about the firmware to show before flashing
    :param on_flashed: Optional callback for each successfully flashed MCU
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
    if not install_flash_deps(FLASHTOOL_DEPS):
        return

    flashed_uuids: Set[str] = set()
    target = select_flashtool_target(flashed_uuids)
    if target is None or not confirm_flash(firmware, target, firmware_info):
        Logger.print_info(f"{operation_name.capitalize()} aborted!")
        return

    instances: List[Klipper] = get_instances(Klipper)
    if not stop_klipper_instances_interactively(instances, operation_name):
        return

    try:
        while target is not None:
            if run_flashtool(firmware, target):
                if target.uuid is not None:
                    flashed_uuids.add(target.uuid)
                if on_flashed is not None:
                    on_flashed(target)

            question = f"Flash '{firmware.name}' to another MCU?"
            if not get_confirm(question, default_choice=False):
                break
            target = select_flashtool_target(flashed_uuids)
            if target is not None and not confirm_flash(
                firmware, target, firmware_info
            ):
                target = None
    finally:
        InstanceManager.start_all(instances)


def confirm_flash(
    firmware: Path, target: FlashtoolTarget, firmware_info: List[str] | None
) -> bool:
    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            f"Firmware: {firmware}",
            *(firmware_info or []),
            f"Target: {target.description}",
            "\n\n",
            "Make sure the firmware was built for this MCU, with a bootloader "
            "offset matching the application offset of Katapult on it.",
        ],
    )
    return get_confirm("Start flashing?", default_choice=False) is True


def run_flashtool(firmware: Path, target: FlashtoolTarget) -> bool:
    try:
        if target.request_bootloader:
            Logger.print_status("Requesting the bootloader ...")
            run(build_request_bootloader_cmd(target), check=True)

        Logger.print_status(f"Flashing '{firmware.name}' to {target.description} ...")
        run(build_flash_cmd(firmware, target), check=True)
        Logger.print_ok("Flashing successful!", start="\n", end="\n\n")
        return True
    except CalledProcessError:
        Logger.print_error("Flashing failed! See the flashtool output above.")
        return False


def select_flashtool_target(flashed_uuids: Set[str]) -> FlashtoolTarget | None:
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
        return _select_can_target(flashed_uuids)
    elif choice == "2":
        return _select_usb_target()
    elif choice == "3":
        return _select_uart_target()
    return None


def _select_can_target(flashed_uuids: Set[str]) -> FlashtoolTarget | None:
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

    uuid = _select_canbus_uuid(flashed_uuids)
    if uuid is None:
        return None

    return FlashtoolTarget(Connection.CAN, interface=interface, uuid=uuid)


def _select_canbus_uuid(flashed_uuids: Set[str]) -> str | None:
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
                    + (" (flashed)" if uuid in flashed_uuids else "")
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
            "Enter the UUID of the MCU to flash (e.g. 'bd9dc195c7eb', b=back)"
        )
        if uuid.lower() == "b":
            return None
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

    return FlashtoolTarget(Connection.USB, device=device)


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

    return FlashtoolTarget(Connection.UART, device=device, baud=baud)


def _get_uart_device_input() -> str | None:
    while True:
        device = get_string_input(
            "Enter the UART device path (e.g. /dev/ttyAMA0, b=back)",
            allow_special_chars=True,
        )
        if device.lower() == "b":
            return None
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
