# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import re
from subprocess import CalledProcessError, run
from typing import List, Tuple

from components.moonraker.moonraker import Moonraker
from components.moonraker.services.moonraker_instance_service import (
    MoonrakerInstanceService,
)
from core.backup_manager.backup_manager import BackupManager
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
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
        Logger.print_status("Installing Spoolman using Docker...")

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        if not self.__handle_existing_installation():
            self.ip: str = get_ipv4_addr()
            self.__run_setup()

            # noinspection HttpUrlsUsage
            Logger.print_dialog(
                DialogType.SUCCESS,
                [
                    "Spoolman successfully installed using Docker!",
                    "You can access Spoolman via the following URL:",
                    f"http://{self.ip}:{self.port}",
                ],
                center_content=True,
            )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating Spoolman Docker container...")

        if not SPOOLMAN_DIR.exists() or not SPOOLMAN_COMPOSE_FILE.exists():
            Logger.print_error("Spoolman installation not found or incomplete.")
            return

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        Logger.print_status("Updating Spoolman container...")
        if not Spoolman.update_container():
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            ["Spoolman Docker container successfully updated!"],
            center_content=True,
        )

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing Spoolman Docker container...")

        if not SPOOLMAN_DIR.exists():
            Logger.print_info("Spoolman is not installed. Nothing to remove.")
            return

        docker_available, docker_compose_available = self.__check_docker_prereqs()
        if not docker_available or not docker_compose_available:
            return

        # remove moonraker integration
        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances: List[Moonraker] = mrsvc.get_all_instances()

        Logger.print_status("Removing Spoolman configuration from moonraker.conf...")
        remove_config_section("spoolman", mr_instances)

        Logger.print_status("Removing Spoolman from moonraker.asvc...")
        self.__remove_from_moonraker_asvc()

        # stop and remove the container if docker-compose exists
        if SPOOLMAN_COMPOSE_FILE.exists():
            Logger.print_status("Stopping and removing Spoolman container...")

            if Spoolman.tear_down_container():
                Logger.print_ok("Spoolman container removed!")
            else:
                Logger.print_error(
                    "Failed to remove Spoolman container! Please remove it manually."
                )

            if Spoolman.remove_image():
                Logger.print_ok("Spoolman container and image removed!")
            else:
                Logger.print_error(
                    "Failed to remove Spoolman image! Please remove it manually."
                )

        # backup Spoolman directory to ~/spoolman_data-<timestamp> before removing it
        try:
            bm = BackupManager()
            result = bm.backup_directory(
                f"{SPOOLMAN_DIR.name}_data",
                source=SPOOLMAN_DIR,
                target=SPOOLMAN_DIR.parent,
            )
            if result:
                Logger.print_ok(f"Spoolman data backed up to {result}")
                Logger.print_status("Removing Spoolman directory...")
                if run_remove_routines(SPOOLMAN_DIR):
                    Logger.print_ok("Spoolman directory removed!")
                else:
                    Logger.print_error(
                        "Failed to remove Spoolman directory! Please remove it manually."
                    )
        except Exception as e:
            Logger.print_error(f"Failed to backup Spoolman directory: {e}")
            Logger.print_info("Skipping Spoolman directory removal...")

        Logger.print_dialog(
            DialogType.SUCCESS,
            ["Spoolman successfully removed!"],
            center_content=True,
        )

    def __run_setup(self) -> None:
        # Create Spoolman directory and data directory
        Logger.print_status("Setting up Spoolman directories...")
        SPOOLMAN_DIR.mkdir(parents=True)
        Logger.print_ok(f"Directory {SPOOLMAN_DIR} created!")
        SPOOLMAN_DATA_DIR.mkdir(parents=True)
        Logger.print_ok(f"Directory {SPOOLMAN_DATA_DIR} created!")

        # Set correct permissions for data directory
        try:
            Logger.print_status("Setting permissions for Spoolman data directory...")
            run(["chown", "1000:1000", str(SPOOLMAN_DATA_DIR)], check=True)
            Logger.print_ok("Permissions set!")
        except CalledProcessError:
            Logger.print_warn(
                "Could not set permissions on data directory. This might cause issues."
            )

        Logger.print_status("Creating Docker Compose file...")
        if Spoolman.create_docker_compose():
            Logger.print_ok("Docker Compose file created!")
        else:
            Logger.print_error("Failed to create Docker Compose file!")

        self.__port_config_prompt()

        Logger.print_status("Spinning up Spoolman container...")
        if Spoolman.start_container():
            Logger.print_ok("Spoolman container started!")
        else:
            Logger.print_error("Failed to start Spoolman container!")

        if self.__add_moonraker_integration():
            Logger.print_ok("Spoolman integration added to Moonraker!")
        else:
            Logger.print_info("Moonraker integration skipped.")

    def __check_docker_prereqs(self) -> Tuple[bool, bool]:
        # check if Docker is available
        is_docker_available = Spoolman.is_docker_available()
        if not is_docker_available:
            Logger.print_error("Docker is not installed or not available.")
            Logger.print_info(
                "Please install Docker first: https://docs.docker.com/engine/install/"
            )

        # check if Docker Compose is available
        is_docker_compose_available = Spoolman.is_docker_compose_available()
        if not is_docker_compose_available:
            Logger.print_error("Docker Compose is not installed or not available.")

        return is_docker_available, is_docker_compose_available

    def __port_config_prompt(self) -> None:
        """Prompt for advanced configuration options"""
        Logger.print_dialog(
            DialogType.INFO,
            [
                "You can configure Spoolman to run on a different port than the default. "
                "Make sure you don't select a port which is already in use by "
                "another application. Your input will not be validated! "
                "The default port is 7912.",
            ],
        )
        if not get_confirm("Continue with default port 7912?", default_choice=True):
            self.__set_port()

    def __set_port(self) -> None:
        """Configure advanced options for Spoolman Docker container"""
        port = get_number_input(
            "Which port should Spoolman run on?",
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

            Logger.print_ok(f"Port set to {port}...")

    def __handle_existing_installation(self) -> bool:
        if not (SPOOLMAN_DIR.exists() and SPOOLMAN_DIR.is_dir()):
            return False

        compose_file_exists = SPOOLMAN_COMPOSE_FILE.exists()
        container_running = Spoolman.is_container_running()

        if container_running and compose_file_exists:
            Logger.print_info("Spoolman is already installed!")
            return True
        elif container_running and not compose_file_exists:
            Logger.print_status(
                "Spoolman container is running but Docker Compose file is missing..."
            )
            if get_confirm(
                "Do you want to recreate the Docker Compose file?",
                default_choice=True,
            ):
                Spoolman.create_docker_compose()
                self.__port_config_prompt()
            return True
        elif not container_running and compose_file_exists:
            Logger.print_status(
                "Docker Compose file exists but container is not running..."
            )
            Spoolman.start_container()
            return True
        return False

    def __add_moonraker_integration(self) -> bool:
        """Enable Moonraker integration for Spoolman Docker container"""
        if not get_confirm("Add Moonraker integration?", default_choice=True):
            return False

        Logger.print_status("Adding Spoolman integration to Moonraker...")

        # read port from the docker-compose file
        port = SPOOLMAN_DEFAULT_PORT
        if SPOOLMAN_COMPOSE_FILE.exists():
            with open(SPOOLMAN_COMPOSE_FILE, "r") as f:
                content = f.read()
                # Extract port from the port mapping
                port_match = re.search(r'"(\d+):8000"', content)
                if port_match:
                    port = port_match.group(1)

        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()

        # noinspection HttpUrlsUsage
        add_config_section(
            section="spoolman",
            instances=mr_instances,
            options=[("server", f"http://{self.ip}:{port}")],
        )

        Logger.print_status("Adding Spoolman to moonraker.asvc...")
        self.__add_to_moonraker_asvc()

        InstanceManager.restart_all(mr_instances)

        return True

    def __add_to_moonraker_asvc(self) -> None:
        """Add Spoolman to moonraker.asvc"""
        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()
        for instance in mr_instances:
            asvc_path = instance.data_dir.joinpath("moonraker.asvc")
            if asvc_path.exists():
                if "Spoolman" in open(asvc_path).read():
                    Logger.print_info(f"Spoolman already in {asvc_path}. Skipping...")
                    continue

                with open(asvc_path, "a") as f:
                    f.write("Spoolman\n")

                Logger.print_ok(f"Spoolman added to {asvc_path}!")

    def __remove_from_moonraker_asvc(self) -> None:
        """Remove Spoolman from moonraker.asvc"""
        mrsvc = MoonrakerInstanceService()
        mrsvc.load_instances()
        mr_instances = mrsvc.get_all_instances()
        for instance in mr_instances:
            asvc_path = instance.data_dir.joinpath("moonraker.asvc")
            if asvc_path.exists():
                if "Spoolman" not in open(asvc_path).read():
                    Logger.print_info(f"Spoolman not in {asvc_path}. Skipping...")
                    continue

                with open(asvc_path, "r") as f:
                    lines = f.readlines()

                new_lines = [line for line in lines if "Spoolman" not in line]

                with open(asvc_path, "w") as f:
                    f.writelines(new_lines)

                Logger.print_ok(f"Spoolman removed from {asvc_path}!")
