# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import CalledProcessError, run

from components.moonraker.moonraker import Moonraker
from core.instance_manager.base_instance import BaseInstance
from core.i18n import _tr
from core.logger import Logger
from extensions.spoolman import (
    MODULE_PATH,
    SPOOLMAN_COMPOSE_FILE,
    SPOOLMAN_DIR,
    SPOOLMAN_DOCKER_IMAGE,
)
from utils.sys_utils import get_system_timezone


@dataclass
class Spoolman:
    suffix: str
    base: BaseInstance = field(init=False, repr=False)
    dir: Path = SPOOLMAN_DIR
    data_dir: Path = field(init=False)

    def __post_init__(self):
        self.base: BaseInstance = BaseInstance(Moonraker, self.suffix)
        self.data_dir = self.base.data_dir

    @staticmethod
    def is_container_running() -> bool:
        try:
            result = run(
                ["docker", "compose", "-f", str(SPOOLMAN_COMPOSE_FILE), "ps", "-q"],
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except CalledProcessError:
            return False

    @staticmethod
    def is_docker_available() -> bool:
        try:
            run(["docker", "--version"], capture_output=True, check=True)
            return True
        except (CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def is_docker_compose_available() -> bool:
        try:
            run(["docker", "compose", "version"], capture_output=True, check=True)
            return True
        except (CalledProcessError, FileNotFoundError):
            try:
                run(["docker-compose", "--version"], capture_output=True, check=True)
                return True
            except (CalledProcessError, FileNotFoundError):
                return False

    @staticmethod
    def create_docker_compose() -> bool:
        try:
            shutil.copy(
                MODULE_PATH.joinpath("assets/docker-compose.yml"),
                SPOOLMAN_COMPOSE_FILE,
            )

            timezone = get_system_timezone()

            with open(SPOOLMAN_COMPOSE_FILE, "r") as f:
                content = f.read()

            content = content.replace("TZ=Europe/Stockholm", f"TZ={timezone}")

            with open(SPOOLMAN_COMPOSE_FILE, "w") as f:
                f.write(content)

            return True
        except Exception as e:
            Logger.print_error(_tr("Error creating Docker Compose file: {}").format(e))
            return False

    @staticmethod
    def start_container() -> bool:
        try:
            run(
                ["docker", "compose", "-f", str(SPOOLMAN_COMPOSE_FILE), "up", "-d"],
                check=True,
            )
            return True
        except CalledProcessError as e:
            Logger.print_error(_tr("Failed to start Spoolman container: {}").format(e))
            return False

    @staticmethod
    def update_container() -> bool:

        def __get_image_id() -> str:
            try:
                result = run(
                    ["docker", "images", "-q", SPOOLMAN_DOCKER_IMAGE],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except CalledProcessError:
                raise Exception(_tr("Failed to get Spoolman Docker image ID"))

        try:
            old_image_id = __get_image_id()
            Logger.print_status(_tr("Pulling latest Spoolman image..."))
            Spoolman.pull_image()
            new_image_id = __get_image_id()
            Logger.print_status(_tr("Tearing down old Spoolman container..."))
            Spoolman.tear_down_container()
            Logger.print_status(_tr("Spinning up new Spoolman container..."))
            Spoolman.start_container()
            if old_image_id != new_image_id:
                Logger.print_status(_tr("Removing old Spoolman image..."))
                run(["docker", "rmi", old_image_id], check=True)
            return True

        except CalledProcessError as e:
            Logger.print_error(_tr("Failed to update Spoolman container: {}").format(e))
            return False

    @staticmethod
    def tear_down_container() -> bool:
        try:
            run(
                ["docker", "compose", "-f", str(SPOOLMAN_COMPOSE_FILE), "down"],
                check=True,
            )
            return True
        except CalledProcessError as e:
            Logger.print_error(_tr("Failed to tear down Spoolman container: {}").format(e))
            return False

    @staticmethod
    def pull_image() -> bool:
        try:
            run(["docker", "pull", SPOOLMAN_DOCKER_IMAGE], check=True)
            return True
        except CalledProcessError as e:
            Logger.print_error(_tr("Failed to pull Spoolman Docker image: {}").format(e))
            return False

    @staticmethod
    def remove_image() -> bool:
        try:
            image_exists = run(
                ["docker", "images", "-q", SPOOLMAN_DOCKER_IMAGE],
                capture_output=True,
                text=True,
            ).stdout.strip()
            if not image_exists:
                Logger.print_info(_tr("Spoolman Docker image not found. Nothing to remove."))
                return False

            run(["docker", "rmi", SPOOLMAN_DOCKER_IMAGE], check=True)
            return True
        except CalledProcessError as e:
            Logger.print_error(_tr("Failed to remove Spoolman Docker image: {}").format(e))
            return False
