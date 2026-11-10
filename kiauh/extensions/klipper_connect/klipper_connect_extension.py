# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Alejandro Mora <github.com/amd989>                  #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  It integrates klipper-connect (Prusa Connect bridge for Klipper):      #
#  https://github.com/amd989/klipper-connect                              #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import getpass
import re
import shutil
import subprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import List

from components.moonraker.moonraker import Moonraker
from core.constants import SYSTEMD
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from extensions.base_extension import BaseExtension
from extensions.klipper_connect import (
    KLIPPER_CONNECT_BIN,
    KLIPPER_CONNECT_BRANCH,
    KLIPPER_CONNECT_CFG_NAME,
    KLIPPER_CONNECT_CFG_SAMPLE,
    KLIPPER_CONNECT_DIR,
    KLIPPER_CONNECT_ENV_DIR,
    KLIPPER_CONNECT_MINI_CFG_SAMPLE,
    KLIPPER_CONNECT_NAME,
    KLIPPER_CONNECT_PRINTER_TYPES,
    KLIPPER_CONNECT_REPO,
    KLIPPER_CONNECT_SERVICE_TEMPLATE,
    KLIPPER_CONNECT_SN_REGEX,
    KLIPPER_CONNECT_STATE_DIR_NAME,
)
from utils.common import check_install_dependencies
from utils.config_utils import add_config_section, remove_config_section
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm, get_selection_input, get_string_input
from utils.instance_utils import get_instances
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    create_service_file,
    install_python_packages,
    remove_system_service,
)


def service_name(moonraker: Moonraker) -> str:
    """klipper-connect for the default instance, klipper-connect-<suffix>
    for others (one bridge per printer)."""
    if moonraker.suffix:
        return f"{KLIPPER_CONNECT_NAME}-{moonraker.suffix}"
    return KLIPPER_CONNECT_NAME


def updater_section(moonraker: Moonraker) -> str:
    return f"update_manager {service_name(moonraker)}"


def config_path(moonraker: Moonraker) -> Path:
    return moonraker.base.cfg_dir.joinpath(KLIPPER_CONNECT_CFG_NAME)


def is_registered(moonraker: Moonraker) -> bool:
    return moonraker.data_dir.joinpath(
        KLIPPER_CONNECT_STATE_DIR_NAME, "prusa_connect.ini"
    ).exists()


def is_active(service: str) -> bool:
    return (
        subprocess.run(
            ["systemctl", "is-active", "--quiet", service], check=False
        ).returncode
        == 0
    )


def installed_services() -> List[str]:
    """All klipper-connect*.service units on this machine."""
    if not SYSTEMD.exists():
        return []
    pattern = re.compile(rf"^{KLIPPER_CONNECT_NAME}(-[0-9a-zA-Z_]+)?\.service$")
    return sorted(f.name for f in SYSTEMD.iterdir() if pattern.match(f.name))


# noinspection PyMethodMayBeStatic
class KlipperConnectExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing klipper-connect ...")

        if not check_python_version(3, 9):
            return

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "Moonraker not found! klipper-connect talks to Klipper "
                    "through Moonraker, so install Moonraker first.",
                ],
            )
            return

        selected = self._select_instances(mr_instances)
        if not selected:
            Logger.print_info("No printer selected. Exiting ...")
            return

        try:
            check_install_dependencies()
            self._get_or_update_repo()
            self._install_python_env()

            BackupService().backup_moonraker_conf()
            for moonraker in selected:
                self._setup_instance(moonraker)

            InstanceManager.restart_all(selected)
        except Exception as e:
            Logger.print_error(f"Error installing klipper-connect:\n{e}")
            return

        for moonraker in selected:
            self._register_instance(moonraker)

        Logger.print_dialog(
            DialogType.SUCCESS,
            [
                "klipper-connect installed!",
                "\n\n",
                "Logs: journalctl -u <service> -f",
                "Config: <printer_data>/config/klipper_connect.conf",
            ],
            margin_bottom=1,
        )

    def update_extension(self, **kwargs) -> None:
        if not KLIPPER_CONNECT_DIR.exists():
            Logger.print_info(
                "klipper-connect doesn't seem to be installed! Skipping ..."
            )
            return

        Logger.print_status("Updating klipper-connect ...")
        # Only restart what was running; unlinked printers stay stopped
        services = [s for s in installed_services() if is_active(s)]
        try:
            for service in services:
                cmd_sysctl_service(service, "stop")

            git_pull_wrapper(KLIPPER_CONNECT_DIR)
            install_python_packages(
                KLIPPER_CONNECT_ENV_DIR, ["-e", KLIPPER_CONNECT_DIR.as_posix()]
            )

            for service in services:
                cmd_sysctl_service(service, "start")
            Logger.print_ok("klipper-connect updated successfully.", end="\n\n")
        except CalledProcessError as e:
            Logger.print_error(f"Error updating klipper-connect:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing klipper-connect ...")
        try:
            for service in installed_services():
                remove_system_service(service)

            mr_instances: List[Moonraker] = get_instances(Moonraker)
            if mr_instances:
                Logger.print_status("Removing klipper-connect from update manager ...")
                BackupService().backup_moonraker_conf()
                for moonraker in mr_instances:
                    remove_config_section(updater_section(moonraker), [moonraker])
                    self._remove_from_asvc(moonraker)

            for path in (KLIPPER_CONNECT_DIR, KLIPPER_CONNECT_ENV_DIR):
                if path.exists():
                    Logger.print_status(f"Removing {path} ...")
                    shutil.rmtree(path)

            Logger.print_dialog(
                DialogType.SUCCESS,
                [
                    "klipper-connect removed!",
                    "\n\n",
                    "Your klipper_connect.conf files and Prusa Connect tokens "
                    "(<printer_data>/klipper_connect) were kept. Delete them "
                    "and remove the printer in Prusa Connect if you don't "
                    "need them anymore.",
                ],
                margin_bottom=1,
            )
        except Exception as e:
            Logger.print_error(f"Error removing klipper-connect:\n{e}")

    # --- install steps ---------------------------------------------------

    def _select_instances(self, instances: List[Moonraker]) -> List[Moonraker]:
        if len(instances) == 1:
            if get_confirm(
                "Install klipper-connect?", default_choice=True, allow_go_back=True
            ):
                return instances
            return []

        Logger.print_dialog(
            DialogType.INFO,
            [
                "Several Moonraker instances found. klipper-connect runs one "
                "service per printer; choose which printers to connect.",
                "\n\n",
                *[
                    f"● {m.data_dir.name} ({m.service_file_path.name})"
                    for m in instances
                ],
            ],
        )
        return [
            m
            for m in instances
            if get_confirm(f"Set up {m.data_dir.name}?", default_choice=True)
        ]

    def _get_or_update_repo(self) -> None:
        if KLIPPER_CONNECT_DIR.exists():
            Logger.print_info(f"{KLIPPER_CONNECT_DIR} exists, updating it ...")
            git_pull_wrapper(KLIPPER_CONNECT_DIR)
        else:
            git_clone_wrapper(
                KLIPPER_CONNECT_REPO, KLIPPER_CONNECT_DIR, KLIPPER_CONNECT_BRANCH
            )

    def _install_python_env(self) -> None:
        # Only create the env when missing: older KIAUH versions ask whether
        # to re-create an existing one. Packages are refreshed either way so
        # a re-install picks up new dependencies.
        if not KLIPPER_CONNECT_ENV_DIR.exists():
            create_python_venv(KLIPPER_CONNECT_ENV_DIR)
        install_python_packages(
            KLIPPER_CONNECT_ENV_DIR, ["-e", KLIPPER_CONNECT_DIR.as_posix()]
        )

    def _setup_instance(self, moonraker: Moonraker) -> None:
        name = service_name(moonraker)
        Logger.print_status(f"Setting up {name} for {moonraker.data_dir.name} ...")

        self._create_config(moonraker)

        template = KLIPPER_CONNECT_SERVICE_TEMPLATE.read_text()
        content = (
            template.replace("%NAME%", name)
            .replace("%MOONRAKER%", moonraker.service_file_path.name)
            .replace("%USER%", getpass.getuser())
            .replace("%HOME%", Path.home().as_posix())
            .replace("%ENV%", KLIPPER_CONNECT_ENV_DIR.as_posix())
            .replace("%CONFIG%", config_path(moonraker).as_posix())
        )
        create_service_file(f"{name}.service", content)
        cmd_sysctl_manage("daemon-reload")
        # Enabled once the printer is linked (see _register_instance); without
        # a token the bridge would exit and restart every few seconds

        self._add_to_asvc(moonraker)
        add_config_section(
            section=updater_section(moonraker),
            instances=[moonraker],
            options=[
                ("type", "git_repo"),
                ("path", KLIPPER_CONNECT_DIR.as_posix()),
                ("origin", KLIPPER_CONNECT_REPO),
                ("primary_branch", KLIPPER_CONNECT_BRANCH),
                ("virtualenv", KLIPPER_CONNECT_ENV_DIR.as_posix()),
                ("requirements", "requirements.txt"),
                ("managed_services", name),
            ],
        )

    def _create_config(self, moonraker: Moonraker) -> None:
        cfg = config_path(moonraker)
        if cfg.exists():
            Logger.print_info(f"Keeping existing {cfg}")
            return

        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                f"Printer: {moonraker.data_dir.name}",
                "\n\n",
                "Prusa Connect identifies the printer by the serial number "
                "on the sticker on its back (CZPX...).",
            ],
            custom_title="klipper-connect",
        )
        serial = get_string_input(
            "Serial number", regex=KLIPPER_CONNECT_SN_REGEX
        ).upper()

        options = {str(i + 1): t for i, t in enumerate(KLIPPER_CONNECT_PRINTER_TYPES)}
        for key, value in options.items():
            Logger.print_info(f"{key}) {value}", prefix=False)
        printer_type = options[
            get_selection_input("Printer type", option_list=options, default="1")
        ]

        sample = (
            KLIPPER_CONNECT_MINI_CFG_SAMPLE
            if printer_type == "MINI"
            else KLIPPER_CONNECT_CFG_SAMPLE
        )
        text = sample.read_text()
        text = re.sub(
            r"^serial_number:.*$", f"serial_number: {serial}", text, flags=re.MULTILINE
        )
        text = re.sub(
            r"^type:.*$", f"type: {printer_type}", text, count=1, flags=re.MULTILINE
        )
        cfg.write_text(text)
        Logger.print_ok(f"Created {cfg}")

    def _add_to_asvc(self, moonraker: Moonraker) -> None:
        """Let Moonraker's update manager restart the service."""
        asvc = moonraker.data_dir.joinpath("moonraker.asvc")
        name = service_name(moonraker)
        if not asvc.is_file():
            return
        lines = asvc.read_text().splitlines()
        if name not in lines:
            asvc.write_text("\n".join([*lines, name]) + "\n")

    def _remove_from_asvc(self, moonraker: Moonraker) -> None:
        asvc = moonraker.data_dir.joinpath("moonraker.asvc")
        if not asvc.is_file():
            return
        name = service_name(moonraker)
        lines = asvc.read_text().splitlines()
        if name in lines:
            asvc.write_text("\n".join(x for x in lines if x != name) + "\n")

    def _register_instance(self, moonraker: Moonraker) -> None:
        name = service_name(moonraker)
        cfg = config_path(moonraker)
        service = f"{name}.service"
        if is_registered(moonraker):
            cmd_sysctl_service(service, "enable")
            cmd_sysctl_service(service, "restart")
            return

        if not get_confirm(
            f"Link {moonraker.data_dir.name} to Prusa Connect now?",
            default_choice=True,
        ):
            Logger.print_dialog(
                DialogType.ATTENTION,
                [
                    "To link it later, run:",
                    f"{KLIPPER_CONNECT_BIN} -c {cfg} register",
                    f"then: sudo systemctl enable --now {name}",
                ],
            )
            return

        # Interactive: prints a link to open in the browser and waits until
        # the printer is confirmed in Prusa Connect.
        result = subprocess.run(
            [KLIPPER_CONNECT_BIN.as_posix(), "-c", cfg.as_posix(), "register"],
            check=False,
        )
        if result.returncode == 0:
            cmd_sysctl_service(service, "enable")
            cmd_sysctl_service(service, "start")
        else:
            Logger.print_warn(f"{name} wasn't linked. Run the register command again.")
