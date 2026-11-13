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
import shutil
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Set

from components.katapult import KATAPULT_FLASHTOOL_PATH
from components.katapult.firmware_utils import install_flash_deps
from components.katapult.flashtool import (
    FLASHTOOL_DEPS,
    UUID_REGEX,
    Connection,
    FlashtoolTarget,
    check_katapult_running,
    find_can_bridge_uuids,
    find_canbus_uuids,
    flash_with_flashtool,
    get_can_interfaces,
    is_interface_up,
    run_flashtool,
)
from components.katapult.katapult import (
    KLIPPER_FIRMWARE_BIN,
    KLIPPER_FIRMWARE_DICT,
    get_klipper_firmware_info,
    read_klipper_firmware_dict,
)
from components.katapult.klipper_api import (
    KlipperApiError,
    get_mcu_versions,
    wait_until_ready,
)
from components.klipper import KLIPPER_KCONFIGS_DIR
from components.klipper.klipper import Klipper
from components.klipper_firmware.firmware_utils import (
    run_make,
    run_make_clean,
    run_make_menuconfig,
)
from components.klipper_firmware.flash_options import FlashOptions
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from utils.input_utils import get_confirm, get_number_input
from utils.instance_utils import get_instances, stop_klipper_instances_interactively

# stored next to the saved firmware configs it refers to
REMEMBERED_MCUS_FILE = KLIPPER_KCONFIGS_DIR.joinpath("katapult-mcus.json")
# increase when the file format changes in an incompatible way
REMEMBERED_MCUS_VERSION = 1
KLIPPER_BUILD_DEPS = {"build-essential", "dpkg-dev", "make"}


@dataclass
class RememberedMcu:
    target: FlashtoolTarget
    # file name of the saved firmware config in KLIPPER_KCONFIGS_DIR
    kconfig: str
    # the build settings reported in the klipper.dict of the flashed firmware,
    # e.g. the MCU, its clock and the CAN bus speed. A build from the saved
    # config must report the same settings to be flashed to this MCU.
    firmware_config: Dict[str, Any]

    @property
    def mcu(self) -> str:
        return str(self.firmware_config.get("MCU", ""))


@dataclass
class Firmware:
    file: Path
    version: str
    config: Dict[str, Any]


@dataclass
class UpdateResult:
    mcu: RememberedMcu
    ok: bool
    message: str


def load_remembered_mcus(file: Path = REMEMBERED_MCUS_FILE) -> List[RememberedMcu]:
    try:
        data = json.loads(file.read_text())
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict) or data.get("version") != REMEMBERED_MCUS_VERSION:
        return []

    entries = data.get("mcus")
    mcus = [_mcu_from_dict(e) for e in entries] if isinstance(entries, list) else []
    return [mcu for mcu in mcus if mcu is not None]


def save_remembered_mcus(
    mcus: List[RememberedMcu], file: Path = REMEMBERED_MCUS_FILE
) -> None:
    file.parent.mkdir(exist_ok=True)
    data = {
        "version": REMEMBERED_MCUS_VERSION,
        "mcus": [_mcu_to_dict(mcu) for mcu in mcus],
    }
    file.write_text(json.dumps(data, indent=2) + "\n")


def _mcu_to_dict(mcu: RememberedMcu) -> Dict[str, Any]:
    target = mcu.target
    fields = {
        "interface": target.interface,
        "uuid": target.uuid,
        "device": target.device,
        "baud": target.baud,
    }
    return {
        "target": {
            "connection": target.connection.value,
            **{key: value for key, value in fields.items() if value is not None},
        },
        "kconfig": mcu.kconfig,
        "firmware_config": mcu.firmware_config,
    }


def _mcu_from_dict(entry: Any) -> RememberedMcu | None:
    try:
        fields = entry["target"]
        target = FlashtoolTarget(
            Connection(fields["connection"]),
            interface=fields.get("interface"),
            uuid=fields.get("uuid"),
            device=fields.get("device"),
            baud=fields.get("baud"),
        )
        mcu = RememberedMcu(target, entry["kconfig"], entry["firmware_config"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return None

    valid = isinstance(mcu.kconfig, str) and isinstance(mcu.firmware_config, dict)
    return mcu if valid and _is_valid_target(target) else None


def _is_valid_target(target: FlashtoolTarget) -> bool:
    if target.connection is Connection.CAN:
        return isinstance(target.interface, str) and bool(
            isinstance(target.uuid, str) and UUID_REGEX.match(target.uuid)
        )
    if target.connection is Connection.UART and not isinstance(target.baud, int):
        return False
    return isinstance(target.device, str)


def get_kconfig_mcu(kconfig: Path) -> str | None:
    """Read the MCU from a Klipper firmware config, e.g. 'stm32g0b1xx'"""
    try:
        lines = kconfig.read_text().splitlines()
    except OSError:
        return None
    for line in lines:
        if line.startswith("CONFIG_MCU="):
            return line.split("=", 1)[1].strip().strip('"') or None
    return None


def diff_firmware_config(
    remembered: Dict[str, Any], built: Dict[str, Any]
) -> List[str]:
    """
    Compare the build settings of two Klipper firmwares |
    :param remembered: The settings of the firmware flashed to an MCU
    :param built: The settings of a new build
    :return: The settings that differ. Settings only one of the Klipper versions
        knows about are ignored, so a Klipper update doesn't prevent flashing.
    """
    return sorted(
        key for key in remembered.keys() & built.keys() if remembered[key] != built[key]
    )


def get_mcu_sections() -> Dict[str, str]:
    """Map the CAN UUIDs found in the Klipper configs to their config section"""
    cfg_dirs = [instance.base.cfg_dir for instance in get_instances(Klipper)]
    return {uuid: section for uuid, section in find_canbus_uuids(cfg_dirs)}


def describe_mcu(mcu: RememberedMcu, sections: Dict[str, str]) -> str:
    uuid = mcu.target.uuid
    if uuid is not None and uuid in sections:
        return f"[{sections[uuid]}] {uuid}"
    return mcu.target.description


def flash_klipper_via_katapult() -> None:
    if not KLIPPER_FIRMWARE_BIN.is_file():
        Logger.print_dialog(
            DialogType.ERROR,
            [
                f"No Klipper firmware found at '{KLIPPER_FIRMWARE_BIN}'!",
                "\n\n",
                "Build the Klipper firmware first, with a bootloader offset matching "
                "the application offset of Katapult on the MCU.",
            ],
        )
        return

    flash_with_flashtool(
        KLIPPER_FIRMWARE_BIN,
        "flashing of Klipper",
        get_klipper_firmware_info(),
        on_flashed=offer_to_remember_mcu,
    )


def offer_to_remember_mcu(
    target: FlashtoolTarget,
    dict_file: Path = KLIPPER_FIRMWARE_DICT,
    kconfigs_dir: Path = KLIPPER_KCONFIGS_DIR,
    mcus_file: Path = REMEMBERED_MCUS_FILE,
) -> None:
    """
    Offer to remember a flashed MCU with the saved firmware config it was built
    with, so it can be updated by 'Update all remembered MCUs' later on |
    :param target: The flashed MCU
    :param dict_file: The klipper.dict of the flashed firmware
    :param kconfigs_dir: The directory of the saved firmware configs
    :param mcus_file: The file the remembered MCUs are stored in
    :return: None
    """
    firmware_config = read_klipper_firmware_dict(dict_file).get("config")
    if not isinstance(firmware_config, dict) or not firmware_config.get("MCU"):
        return

    remembered = load_remembered_mcus(mcus_file)
    known = next((m for m in remembered if m.target == target), None)
    if known is not None and known.firmware_config == firmware_config:
        # flashed with the same build settings as when it was remembered
        return

    mcu = firmware_config["MCU"]
    configs = sorted(
        c for c in kconfigs_dir.glob("*.config") if get_kconfig_mcu(c) == mcu
    )
    if not configs:
        Logger.print_info(
            f"Save the firmware config to remember this MCU for updates, "
            f"no saved config is built for '{mcu}'."
        )
        return

    kconfig = _select_kconfig_to_remember(configs)
    if kconfig is None:
        return

    new = RememberedMcu(target, kconfig.name, firmware_config)
    save_remembered_mcus([m for m in remembered if m is not known] + [new], mcus_file)
    Logger.print_ok(
        f"Remembered {describe_mcu(new, get_mcu_sections())} with '{kconfig.name}'."
    )


def _select_kconfig_to_remember(configs: List[Path]) -> Path | None:
    # the selected config is only a path once a firmware was built in this
    # session, and is then the likely match
    selected = Path(FlashOptions().selected_kconfig)
    matching = (
        [c for c in configs if _same_content(c, selected)]
        if selected.is_absolute()
        else []
    )

    if len(matching) == 1:
        question = f"Remember this MCU for updates, with '{matching[0].name}'?"
        return matching[0] if get_confirm(question, default_choice=True) else None

    if not get_confirm("Remember this MCU for updates?", default_choice=True):
        return None
    Logger.print_dialog(
        DialogType.CUSTOM,
        [f"{i}) {config.name}" for i, config in enumerate(configs, 1)],
        custom_title="Which saved config was this firmware built with?",
    )
    index = get_number_input(
        "Select firmware config (b=back)",
        min_value=1,
        max_value=len(configs),
        allow_go_back=True,
    )
    return configs[index - 1] if index is not None else None


def _same_content(file1: Path, file2: Path) -> bool:
    try:
        return file1.read_bytes() == file2.read_bytes()
    except OSError:
        return False


def update_all_mcus(
    kconfigs_dir: Path = KLIPPER_KCONFIGS_DIR,
    mcus_file: Path = REMEMBERED_MCUS_FILE,
) -> None:
    """
    Rebuild the Klipper firmware of every remembered MCU from its saved config,
    flash them all through Katapult with Klipper stopped only once, then check
    the version each MCU reports. USB to CAN bridges are flashed last, as their
    CAN interface goes down while they are flashed. |
    :param kconfigs_dir: The directory of the saved firmware configs
    :param mcus_file: The file the remembered MCUs are stored in
    :return: None
    """
    if not KATAPULT_FLASHTOOL_PATH.is_file():
        Logger.print_error("Katapult is not installed! Install it first.")
        return
    if check_katapult_running():
        Logger.print_error("Katapult's flashtool is already running! Aborting.")
        return

    mcus = load_remembered_mcus(mcus_file)
    if not mcus:
        Logger.print_dialog(
            DialogType.INFO,
            [
                "No MCU to update!",
                "\n\n",
                "Build the Klipper firmware from a saved config, then flash it "
                "with 'Flash Klipper to an MCU' and choose to remember the MCU.",
            ],
        )
        return

    sections = get_mcu_sections()
    skipped: List[UpdateResult] = []
    available: List[RememberedMcu] = []
    for mcu in mcus:
        problem = _find_problem(mcu, kconfigs_dir, sections)
        if problem is None:
            available.append(mcu)
        else:
            skipped.append(UpdateResult(mcu, False, f"skipped, {problem}"))
    if not available:
        _print_update_results(skipped, sections)
        return

    bridges = find_can_bridge_uuids()
    # stable sort: bridges last, the other MCUs keep their order
    available.sort(key=lambda m: m.target.uuid in bridges)
    _print_update_plan(available, skipped, bridges, sections)

    review = bool(
        get_confirm(
            "Review each config with menuconfig before building?",
            default_choice=False,
        )
    )
    if not get_confirm("Build and flash the firmware?", default_choice=False):
        Logger.print_info("Update of the MCUs aborted!")
        return
    if not install_flash_deps(FLASHTOOL_DEPS | KLIPPER_BUILD_DEPS):
        return

    with TemporaryDirectory(prefix="kiauh-katapult-") as tmp:
        firmwares = _build_firmwares(available, kconfigs_dir, Path(tmp), review)
        to_flash: List[RememberedMcu] = []
        for mcu in available:
            problem = _check_firmware(mcu, firmwares.get(mcu.kconfig))
            if problem is None:
                to_flash.append(mcu)
            else:
                skipped.append(UpdateResult(mcu, False, f"skipped, {problem}"))
        results = _flash_mcus(to_flash, firmwares, sections) if to_flash else []

    _print_update_results(results + skipped, sections)


def _find_problem(
    mcu: RememberedMcu, kconfigs_dir: Path, sections: Dict[str, str]
) -> str | None:
    """Find what prevents updating an MCU, before anything is built or stopped"""
    if not kconfigs_dir.joinpath(mcu.kconfig).is_file():
        return f"its firmware config '{mcu.kconfig}' doesn't exist anymore"

    target = mcu.target
    if target.connection is Connection.CAN:
        if target.interface not in get_can_interfaces():
            return f"CAN interface '{target.interface}' not found"
        if not is_interface_up(str(target.interface)):
            return f"CAN interface '{target.interface}' is down"
        if target.uuid not in sections:
            return "its UUID isn't in the Klipper configs anymore"
    elif not Path(str(target.device)).exists():
        return f"device '{target.device}' not found"
    return None


def _check_firmware(mcu: RememberedMcu, firmware: Firmware | None) -> str | None:
    """Check the new firmware was built with the settings of the flashed one"""
    if firmware is None:
        return "the build failed"
    changed = diff_firmware_config(mcu.firmware_config, firmware.config)
    if changed:
        return f"the build settings differ ({', '.join(changed)})"
    return None


def _print_update_plan(
    mcus: List[RememberedMcu],
    skipped: List[UpdateResult],
    bridges: Set[str],
    sections: Dict[str, str],
) -> None:
    lines: List[str] = ["The firmware will be built and flashed in this order:"]
    lines.append("\n\n")
    for i, mcu in enumerate(mcus, 1):
        bridge = ", USB to CAN bridge" if mcu.target.uuid in bridges else ""
        lines.append(f"{i}) {describe_mcu(mcu, sections)} ({mcu.kconfig}{bridge})")
    if skipped:
        lines.append("\n\n")
        lines += [f"● {describe_mcu(r.mcu, sections)}: {r.message}" for r in skipped]
    lines += [
        "\n\n",
        "All Klipper instances are stopped until the last MCU was flashed.",
    ]
    Logger.print_dialog(DialogType.ATTENTION, lines)


def _build_firmwares(
    mcus: List[RememberedMcu], kconfigs_dir: Path, out_dir: Path, review: bool
) -> Dict[str, Firmware]:
    """Build each config once, and keep a copy of each firmware in out_dir"""
    firmwares: Dict[str, Firmware] = {}
    failed: Set[str] = set()
    for kconfig_name in dict.fromkeys(mcu.kconfig for mcu in mcus):
        kconfig = kconfigs_dir.joinpath(kconfig_name)
        Logger.print_status(f"Building the Klipper firmware with '{kconfig}' ...")
        try:
            run_make_clean(kconfig)
            if review:
                run_make_menuconfig(kconfig)
            run_make(kconfig)
        except CalledProcessError:
            Logger.print_error(f"Building the firmware with '{kconfig}' failed!")
            failed.add(kconfig_name)
            continue

        build_dir = out_dir.joinpath(kconfig.stem)
        build_dir.mkdir()
        firmware_file = Path(shutil.copy(KLIPPER_FIRMWARE_BIN, build_dir))
        data = read_klipper_firmware_dict(KLIPPER_FIRMWARE_DICT)
        config = data.get("config")
        firmwares[kconfig_name] = Firmware(
            firmware_file,
            str(data.get("version", "")),
            config if isinstance(config, dict) else {},
        )

    if firmwares or failed:
        # don't leave the last build behind, to not flash it by mistake later on
        try:
            run_make_clean()
        except CalledProcessError:
            pass
    return firmwares


def _flash_mcus(
    mcus: List[RememberedMcu], firmwares: Dict[str, Firmware], sections: Dict[str, str]
) -> List[UpdateResult]:
    instances: List[Klipper] = get_instances(Klipper)
    if not stop_klipper_instances_interactively(instances, "update of the MCUs"):
        return [UpdateResult(m, False, "skipped, Klipper wasn't stopped") for m in mcus]

    flashed: List[RememberedMcu] = []
    results: List[UpdateResult] = []
    try:
        for mcu in mcus:
            if run_flashtool(firmwares[mcu.kconfig].file, mcu.target):
                flashed.append(mcu)
            else:
                results.append(UpdateResult(mcu, False, "flashing failed"))
    finally:
        InstanceManager.start_all(instances)

    return _check_mcu_versions(flashed, firmwares, instances, sections) + results


def _check_mcu_versions(
    mcus: List[RememberedMcu],
    firmwares: Dict[str, Firmware],
    instances: List[Klipper],
    sections: Dict[str, str],
) -> List[UpdateResult]:
    """
    Check the version each flashed MCU reports to Klipper. Klipper is asked
    directly, as querying the CAN bus could disrupt the MCUs on it.
    """
    wanted = [sections[m.target.uuid] for m in mcus if m.target.uuid in sections]
    versions: Dict[str, str] = {}
    errors: List[str] = []
    if wanted:
        Logger.print_status("Waiting for Klipper to connect to the MCUs ...")
    for instance in instances if wanted else []:
        state, message = wait_until_ready(instance.uds)
        if state != "ready":
            errors.append(message.strip().splitlines()[0] if message.strip() else state)
        try:
            versions.update(get_mcu_versions(instance.uds, wanted))
        except KlipperApiError:
            continue

    results: List[UpdateResult] = []
    for mcu in mcus:
        expected = firmwares[mcu.kconfig].version
        section = sections.get(str(mcu.target.uuid))
        reported = versions.get(section) if section is not None else None
        if section is None:
            results.append(UpdateResult(mcu, True, "flashed, version not checked"))
        elif reported == expected:
            results.append(UpdateResult(mcu, True, f"updated to {expected}"))
        elif reported is None:
            reason = f" ({errors[0]})" if errors else ""
            results.append(
                UpdateResult(mcu, False, f"flashed, but not connected{reason}")
            )
        else:
            results.append(
                UpdateResult(mcu, False, f"flashed, but it reports {reported}")
            )
    return results


def _print_update_results(
    results: List[UpdateResult], sections: Dict[str, str]
) -> None:
    if not results:
        return
    Logger.print_dialog(
        DialogType.SUCCESS if all(r.ok for r in results) else DialogType.WARNING,
        [f"{describe_mcu(r.mcu, sections)}: {r.message}" for r in results],
    )


def forget_mcu(mcus_file: Path = REMEMBERED_MCUS_FILE) -> None:
    mcus = load_remembered_mcus(mcus_file)
    if not mcus:
        Logger.print_info("No MCU is remembered.")
        return

    sections = get_mcu_sections()
    Logger.print_dialog(
        DialogType.CUSTOM,
        [
            f"{i}) {describe_mcu(mcu, sections)} ({mcu.kconfig})"
            for i, mcu in enumerate(mcus, 1)
        ],
        custom_title="Remembered MCUs",
    )
    index = get_number_input(
        "Select MCU to forget (b=back)",
        min_value=1,
        max_value=len(mcus),
        allow_go_back=True,
    )
    if index is None:
        return

    forgotten = mcus.pop(index - 1)
    save_remembered_mcus(mcus, mcus_file)
    Logger.print_ok(f"Forgot {describe_mcu(forgotten, sections)}.")
