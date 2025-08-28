# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.types.color import Color
from core.menus.base_menu import print_back_footer
from extensions.base_extension import BaseExtension
from extensions.octoprint import (
    OP_SUDOERS_FILE, OP_DEFAULT_PORT,
)
from extensions.octoprint.octoprint import Octoprint
from utils.common import check_install_dependencies
from utils.fs_utils import run_remove_routines, remove_with_sudo
from utils.input_utils import get_selection_input, get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    create_python_venv,
    get_ipv4_addr,
    install_python_packages,
)


# noinspection PyMethodMayBeStatic
class OctoprintExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing OctoPrint ...")

        klipper_instances: List[Klipper] = get_instances(Klipper)
        if not klipper_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "Klipper not found! Please install Klipper first.",
                ],
            )
            return

        existing_ops: List[Octoprint] = get_instances(Octoprint)
        existing_by_suffix: Dict[str, Octoprint] = {op.suffix: op for op in existing_ops}
        candidates: List[Klipper] = [k for k in klipper_instances if k.suffix not in existing_by_suffix]

        chosen: List[Klipper] = []

        if len(klipper_instances) == 1:
            k = klipper_instances[0]
            if k.suffix in existing_by_suffix:
                if not get_confirm(
                    f"OctoPrint already exists for '{k.service_file_path.stem}'. Reinstall?",
                    default_choice=True,
                    allow_go_back=True,
                ):
                    Logger.print_info("Aborted OctoPrint installation.")
                    return
            chosen = [k]
        else:
            while True:
                dialog = "╔═══════════════════════════════════════════════════════╗\n"
                headline = Color.apply(
                    "The following Klipper instances were found:", Color.GREEN
                )
                dialog += f"║{headline:^64}║\n"
                dialog += "╟───────────────────────────────────────────────────────╢\n"

                if candidates:
                    line_all = Color.apply("a) Select all (install for all missing)", Color.YELLOW)
                    dialog += f"║ {line_all:<63}║\n"
                    dialog += "║                                                       ║\n"

                index_map: Dict[str, Klipper] = {}
                for i, k in enumerate(klipper_instances, start=1):
                    mapping = existing_by_suffix.get(k.suffix)
                    suffix = f" <-> {mapping.service_file_path.stem}" if mapping else ""
                    line = Color.apply(f"{i}) {k.service_file_path.stem}{suffix}", Color.CYAN)
                    dialog += f"║ {line:<63}║\n"
                    index_map[str(i)] = k

                dialog += "╟───────────────────────────────────────────────────────╢\n"
                print(dialog, end="")
                print_back_footer()

                allowed = list(index_map.keys()) + ["b"] + (["a"] if candidates else [])
                choice = get_selection_input("Choose instance to install OctoPrint for", allowed)

                if choice == "b":
                    Logger.print_info("Aborted OctoPrint installation.")
                    return
                if choice == "a":
                    chosen = candidates
                    break

                selected = index_map[choice]
                if selected.suffix in existing_by_suffix:
                    confirm = get_confirm(
                        f"OctoPrint already exists for '{selected.service_file_path.stem}'. Reinstall?",
                        default_choice=True,
                        allow_go_back=True,
                    )
                    if not confirm:
                        # back to menu
                        continue
                chosen = [selected]
                break

        deps = {
            "git",
            "wget",
            "python3-pip",
            "python3-dev",
            "libyaml-dev",
            "build-essential",
            "python3-setuptools",
            "python3-virtualenv",
        }
        check_install_dependencies(deps)

        # Determine used ports from existing OctoPrint services and prepare regex
        used_ports: Set[int] = set()
        port_re = re.compile(r"--port=(\d+)")
        for op in existing_ops:
            try:
                content = op.service_file_path.read_text()
                m = port_re.search(content)
                if m:
                    used_ports.add(int(m.group(1)))
            except OSError:
                pass

        # noinspection PyShadowingNames
        def read_existing_port(suffix: str) -> Optional[int]:
            op = existing_by_suffix.get(suffix)
            if not op:
                return None
            try:
                content = op.service_file_path.read_text()
                m = port_re.search(content)
                return int(m.group(1)) if m else None
            except OSError:
                return None

        def next_free_port(start: int, used: Set[int]) -> int:
            p = start
            while p in used:
                p += 1
            used.add(p)
            return p

        created_ops: List[Octoprint] = []
        for k in chosen:
            # Keep existing port on reinstall, otherwise assign next free one
            existing_port = read_existing_port(k.suffix)
            port = existing_port if existing_port is not None else next_free_port(OP_DEFAULT_PORT, used_ports)

            instance = Octoprint(suffix=k.suffix)

            if create_python_venv(instance.env_dir, force=False):
                Logger.print_ok(
                    f"Virtualenv created: {instance.env_dir}", prefix=False
                )
            else:
                Logger.print_info(
                    f"Virtualenv exists: {instance.env_dir}. Skipping creation ..."
                )

            install_python_packages(instance.env_dir, ["octoprint"])

            instance.create(port=port)
            created_ops.append(instance)

        for inst in created_ops:
            try:
                InstanceManager.enable(inst)
                InstanceManager.start(inst)
            except Exception as e:
                Logger.print_error(
                    f"Failed to enable/start {inst.service_file_path.name}: {e}"
                )

        ip = get_ipv4_addr()
        lines = ["Access your new OctoPrint instance(s) at:"]
        for inst in created_ops:
            try:
                content = inst.service_file_path.read_text()
                m = port_re.search(content)
                if m:
                    # noinspection HttpUrlsUsage
                    lines.append(f"● {inst.service_file_path.stem}: http://{ip}:{m.group(1)}")
            except OSError:
                pass

        Logger.print_dialog(DialogType.SUCCESS, lines, center_content=False)

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing OctoPrint ...")

        try:
            op_instances: List[Octoprint] = get_instances(Octoprint)
            if not op_instances:
                Logger.print_info("No OctoPrint instances found. Skipped ...")
                return

            remove_all = False
            if len(op_instances) == 1:
                to_remove = op_instances
            else:
                dialog = "╔═══════════════════════════════════════════════════════╗\n"
                headline = Color.apply(
                    "The following OctoPrint instances were found:", Color.GREEN
                )
                dialog += f"║{headline:^64}║\n"
                dialog += "╟───────────────────────────────────────────────────────╢\n"
                select_all = Color.apply("a) Select all", Color.YELLOW)
                dialog += f"║ {select_all:<63}║\n"
                dialog += "║                                                       ║\n"

                for i, inst in enumerate(op_instances, start=1):
                    line = Color.apply(
                        f"{i}) {inst.service_file_path.stem}", Color.CYAN
                    )
                    dialog += f"║ {line:<63}║\n"
                dialog += "╟───────────────────────────────────────────────────────╢\n"
                print(dialog, end="")
                print_back_footer()

                allowed = [str(i) for i in range(1, len(op_instances) + 1)]
                allowed.extend(["a", "b"])
                choice = get_selection_input("Choose instance to remove", allowed)

                if choice == "a":
                    remove_all = True
                    to_remove = op_instances
                elif choice == "b":
                    Logger.print_info("Aborted OctoPrint removal.")
                    return
                else:
                    idx = int(choice) - 1
                    to_remove = [op_instances[idx]]

            for inst in to_remove:
                Logger.print_status(
                    f"Removing instance {inst.service_file_path.stem} ..."
                )
                try:
                    InstanceManager.remove(inst)
                except Exception as e:
                    Logger.print_error(
                        f"Failed to remove service {inst.service_file_path.name}: {e}"
                    )

                # Remove only this instance's env and basedir
                if inst.env_dir.exists():
                    Logger.print_status(f"Removing {inst.env_dir} ...")
                    run_remove_routines(inst.env_dir)
                if inst.basedir.exists():
                    Logger.print_status(f"Removing {inst.basedir} ...")
                    run_remove_routines(inst.basedir)

            # Remove sudoers file only if no instances remain
            remaining = get_instances(Octoprint)
            if not remaining and OP_SUDOERS_FILE.exists():
                Logger.print_status(f"Removing {OP_SUDOERS_FILE} ...")
                remove_with_sudo(OP_SUDOERS_FILE)

            Logger.print_dialog(
                DialogType.SUCCESS,
                [
                    "Selected OctoPrint instance(s) successfully removed!"
                    if not remove_all
                    else "All OctoPrint instances successfully removed!",
                ],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during OctoPrint removal: {e}")
