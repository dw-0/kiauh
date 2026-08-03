# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import re
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import List, Tuple

from components.moonraker.moonraker import Moonraker
from components.moonraker.services.moonraker_instance_service import (
    MoonrakerInstanceService,
)
from core.instance_manager.instance_manager import InstanceManager
from core.i18n import _tr
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from extensions.base_extension import BaseExtension
from extensions.spoolman import (
    SPOOLMAN_COMPOSE_FILE,
    SPOOLMAN_DATA_DIR,
    SPOOLMAN_DEFAULT_PORT,
    SPOOLMAN_DIR,
)
from extensions.spoolman.spoolman import Spoolman
from utils.config_utils import (
    add_config_section,
    remove_config_section,
)
from utils.fs_utils import run_remove_routines
from utils.input_utils import get_confirm, get_number_input
from utils.sys_utils import get_ipv4_addr


# noinspection PyMethodMayBeStatic
class SpoolmanExtension(BaseExtension):
    ip: str = ""
    port: int = SPOOLMAN_DEFAULT_PORT

    def install_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Installing Spoolman using Docker..."))

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        if not self.__handle_existing_installation():
            self.ip: str = get_ipv4_addr()
            self.__run_setup()

            Logger.print_dialog(
                DialogType.SUCCESS,
                [
                    _tr("Spoolman successfully installed using Docker!"),
                    _tr("You can access Spoolman via the following URL:"),
                    f"http://{self.ip}:{self.port}",
                ],
                center_content=True,
            )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Updating Spoolman Docker container..."))

        if not SPOOLMAN_DIR.exists() or not SPOOLMAN_COMPOSE_FILE.exists():
            Logger.print_error(_tr("Spoolman installation not found or incomplete."))
            return

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        Logger.print_status(_tr("Updating Spoolman container..."))
        if not Spoolman.update_container():
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            [_tr("Spoolman Docker container successfully updated!")],
            center_content=True,
        )

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Removing Spoolman Docker container..."))

        if not SPOOLMAN_DIR.exists():
            Logger.print_info(_tr("Spoolman is not installed. Nothing to remove."))
            return

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances: List[Moonraker] = mrsvc.get_all_instances()

        Logger.print_status(_tr("Removing Spoolman configuration from moonraker.conf..."))
        BackupService().backup_moonraker_conf()
        remove_config_section("spoolman", mr_instances)

        Logger.print_status(_tr("Removing Spoolman from moonraker.asvc..."))
        self.__remove_from_moonraker_asvc()

        if SPOOLMAN_COMPOSE_FILE.exists():
            Logger.print_status(_tr("Stopping and removing Spoolman container..."))

            if Spoolman.tear_down_container():
                Logger.print_ok(_tr("Spoolman container removed!"))
            else:
                Logger.print_error(
                    _tr("Failed to remove Spoolman container! Please remove it manually.")
                )

            if Spoolman.remove_image():
                Logger.print_ok(_tr("Spoolman container and image removed!"))
            else:
                Logger.print_error(
                    _tr("Failed to remove Spoolman image! Please remove it manually.")
                )

        try:
            svc = BackupService()
            success = svc.backup_directory(
                source_path=SPOOLMAN_DIR,
                backup_name="spoolman",
                target_path="spoolman",
            )
            if success:
                Logger.print_ok(_tr("Spoolman data backed up to {}").format(success))
                Logger.print_status(_tr("Removing Spoolman directory..."))
                if run_remove_routines(SPOOLMAN_DIR):
                    Logger.print_ok(_tr("Spoolman directory removed!"))
                else:
                    Logger.print_error(
                        _tr("Failed to remove Spoolman directory! Please remove it manually.")
                    )
        except Exception as e:
            Logger.print_error(_tr("Failed to backup Spoolman directory: {}").format(e))
            Logger.print_info(_tr("Skipping Spoolman directory removal..."))

        Logger.print_dialog(
            DialogType.SUCCESS,
            [_tr("Spoolman successfully removed!")],
            center_content=True,
        )

    def __run_setup(self) -> None:
        Logger.print_status(_tr("Setting up Spoolman directories..."))
        SPOOLMAN_DIR.mkdir(parents=True)
        Logger.print_ok(_tr("Directory {} created!").format(SPOOLMAN_DIR))
        SPOOLMAN_DATA_DIR.mkdir(parents=True)
        Logger.print_ok(_tr("Directory {} created!").format(SPOOLMAN_DATA_DIR))

        try:
            Logger.print_status(_tr("Setting permissions for Spoolman data directory..."))
            run(["chown", "1000:1000", str(SPOOLMAN_DATA_DIR)], check=True)
            Logger.print_ok(_tr("Permissions set!"))
        except CalledProcessError:
            Logger.print_warn(
                _tr("Could not set permissions on data directory. This might cause issues.")
            )

        Logger.print_status(_tr("Creating Docker Compose file..."))
        if Spoolman.create_docker_compose():
            Logger.print_ok(_tr("Docker Compose file created!"))
        else:
            Logger.print_error(_tr("Failed to create Docker Compose file!"))

        self.__port_config_prompt()

        Logger.print_status(_tr("Spinning up Spoolman container..."))
        if Spoolman.start_container():
            Logger.print_ok(_tr("Spoolman container started!"))
        else:
            Logger.print_error(_tr("Failed to start Spoolman container!"))

        if self.__add_moonraker_integration():
            Logger.print_ok(_tr("Spoolman integration added to Moonraker!"))
        else:
            Logger.print_info(_tr("Moonraker integration skipped."))

    def __check_docker_prereqs(self) -> Tuple[bool, bool]:
        is_docker_available = Spoolman.is_docker_available()
        if not is_docker_available:
            Logger.print_error(_tr("Docker is not installed or not available."))
            Logger.print_info(
                _tr("Please install Docker first: https://docs.docker.com/engine/install/")
            )

        is_docker_compose_available = Spoolman.is_docker_compose_available()
        if not is_docker_compose_available:
            Logger.print_error(_tr("Docker Compose is not installed or not available."))

        return is_docker_available, is_docker_compose_available

    def __port_config_prompt(self) -> None:
        Logger.print_dialog(
            DialogType.INFO,
            [
                _tr("You can configure Spoolman to run on a different port than the default. Make sure you don't select a port which is already in use by another application. Your input will not be validated! The default port is 7912."),
            ],
        )
        if not get_confirm(_tr("Continue with default port 7912?"), default_choice=True):
            self.__set_port()

    def __set_port(self) -> None:
        port = get_number_input(
            _tr("Which port should Spoolman run on?"),
            default=SPOOLMAN_DEFAULT_PORT,
            min_value=1024,
            max_value=65535,
        )

        if port != SPOOLMAN_DEFAULT_PORT:
            self.port = port

            with open(SPOOLMAN_COMPOSE_FILE, "r") as f:
                content = f.read()

            port_mapping_pattern = r'"(\d+):8000"'
            content = re.sub(port_mapping_pattern, f'"{port}:8000"', content)

            with open(SPOOLMAN_COMPOSE_FILE, "w") as f:
                f.write(content)

            Logger.print_ok(_tr("Port set to {}...").format(port))

    def __handle_existing_installation(self) -> bool:
        if not (SPOOLMAN_DIR.exists() and SPOOLMAN_DIR.is_dir()):
            return False

        compose_file_exists = SPOOLMAN_COMPOSE_FILE.exists()
        container_running = Spoolman.is_container_running()

        if container_running and compose_file_exists:
            Logger.print_info(_tr("Spoolman is already installed!"))
            return True
        elif container_running and not compose_file_exists:
            Logger.print_status(
                _tr("Spoolman container is running but Docker Compose file is missing...")
            )
            if get_confirm(
                _tr("Do you want to recreate the Docker Compose file?"),
                default_choice=True,
            ):
                Spoolman.create_docker_compose()
                self.__port_config_prompt()
            return True
        elif not container_running and compose_file_exists:
            Logger.print_status(
                _tr("Docker Compose file exists but container is not running...")
            )
            Spoolman.start_container()
            return True
        return False

    def __add_moonraker_integration(self) -> bool:
        if not get_confirm(_tr("Add Moonraker integration?"), default_choice=True):
            return False

        Logger.print_status(_tr("Adding Spoolman integration to Moonraker..."))

        port = SPOOLMAN_DEFAULT_PORT
        if SPOOLMAN_COMPOSE_FILE.exists():
            with open(SPOOLMAN_COMPOSE_FILE, "r") as f:
                content = f.read()
                port_match = re.search(r'"(\d+):8000"', content)
                if port_match:
                    port = port_match.group(1)

        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()

        BackupService().backup_moonraker_conf()
        add_config_section(
            section="spoolman",
            instances=mr_instances,
            options=[("server", f"http://{self.ip}:{port}")],
        )

        Logger.print_status(_tr("Adding Spoolman to moonraker.asvc..."))
        self.__add_to_moonraker_asvc()

        InstanceManager.restart_all(mr_instances)

        return True

    def __add_to_moonraker_asvc(self) -> None:
        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()
        for instance in mr_instances:
            asvc_path: Path = instance.data_dir.joinpath("moonraker.asvc")
            if asvc_path.exists() and asvc_path.is_file():
                with open(asvc_path, "a+") as f:
                    if "Spoolman" in f.read():
                        Logger.print_info(
                            _tr("Spoolman already in {}. Skipping...").format(asvc_path)
                        )
                        continue

                    content: List[str] = f.readlines()
                    if content and not content[-1].endswith("\n"):
                        f.write("\n")

                    f.write("Spoolman\n")

                Logger.print_ok(_tr("Spoolman added to {}!").format(asvc_path))

    def __remove_from_moonraker_asvc(self) -> None:
        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()
        for instance in mr_instances:
            asvc_path = instance.data_dir.joinpath("moonraker.asvc")
            if asvc_path.exists():
                if "Spoolman" not in open(asvc_path).read():
                    Logger.print_info(_tr("Spoolman not in {}. Skipping...").format(asvc_path))
                    continue

                with open(asvc_path, "r") as f:
                    lines = f.readlines()

                new_lines = [line for line in lines if "Spoolman" not in line]

                with open(asvc_path, "w") as f:
                    f.writelines(new_lines)

                Logger.print_ok(_tr("Spoolman removed from {}!").format(asvc_path))
