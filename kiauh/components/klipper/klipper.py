# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, run
from typing import List

from components.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR, MODULE_PATH
from core.instance_manager.base_instance import BaseInstance
from utils.constants import SYSTEMD
from utils.logger import Logger


# noinspection PyMethodMayBeStatic
class Klipper(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu"]

    def __init__(self, suffix: str = ""):
        super().__init__(instance_type=self, suffix=suffix)
        self.klipper_dir: Path = KLIPPER_DIR
        self.env_dir: Path = KLIPPER_ENV_DIR
        self._cfg_file = self.cfg_dir.joinpath("printer.cfg")
        self._log = self.log_dir.joinpath("klippy.log")
        self._serial = self.comms_dir.joinpath("klippy.serial")
        self._uds = self.comms_dir.joinpath("klippy.sock")

    @property
    def cfg_file(self) -> Path:
        return self._cfg_file

    @property
    def log(self) -> Path:
        return self._log

    @property
    def serial(self) -> Path:
        return self._serial

    @property
    def uds(self) -> Path:
        return self._uds

    def create(self) -> None:
        Logger.print_status("Creating new Klipper Instance ...")

        service_template_path = MODULE_PATH.joinpath("assets/klipper.service")
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = SYSTEMD.joinpath(service_file_name)

        env_template_file_path = MODULE_PATH.joinpath("assets/klipper.env")
        env_file_target = self.sysd_dir.joinpath("klipper.env")

        try:
            self.create_folders()
            self._write_service_file(
                service_template_path,
                service_file_target,
                env_file_target,
            )
            self._write_env_file(env_template_file_path, env_file_target)

        except CalledProcessError as e:
            Logger.print_error(f"Error creating instance: {e}")
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file: {e}")
            raise

    def delete(self) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(f"Removing Klipper Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            run(command, check=True)
            self._delete_logfiles()
            Logger.print_ok("Instance successfully removed!")
        except CalledProcessError as e:
            Logger.print_error(f"Error removing instance: {e}")
            raise

    def _write_service_file(
        self,
        service_template_path: Path,
        service_file_target: Path,
        env_file_target: Path,
    ) -> None:
        service_content = self._prep_service_file(
            service_template_path, env_file_target
        )
        command = ["sudo", "tee", service_file_target]
        run(
            command,
            input=service_content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {service_file_target}")

    def _write_env_file(
        self, env_template_file_path: Path, env_file_target: Path
    ) -> None:
        env_file_content = self._prep_env_file(env_template_file_path)
        with open(env_file_target, "w") as env_file:
            env_file.write(env_file_content)
        Logger.print_ok(f"Env file created: {env_file_target}")

    def _prep_service_file(
        self, service_template_path: Path, env_file_path: Path
    ) -> str:
        try:
            with open(service_template_path, "r") as template_file:
                template_content = template_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {service_template_path} - File not found"
            )
            raise
        service_content = template_content.replace("%USER%", self.user)
        service_content = service_content.replace(
            "%KLIPPER_DIR%", str(self.klipper_dir)
        )
        service_content = service_content.replace("%ENV%", str(self.env_dir))
        service_content = service_content.replace("%ENV_FILE%", str(env_file_path))
        return service_content

    def _prep_env_file(self, env_template_file_path: Path) -> str:
        try:
            with open(env_template_file_path, "r") as env_file:
                env_template_file_content = env_file.read()
        except FileNotFoundError:
            Logger.print_error(
                f"Unable to open {env_template_file_path} - File not found"
            )
            raise
        env_file_content = env_template_file_content.replace(
            "%KLIPPER_DIR%", str(self.klipper_dir)
        )
        env_file_content = env_file_content.replace(
            "%CFG%", f"{self.cfg_dir}/printer.cfg"
        )
        env_file_content = env_file_content.replace("%SERIAL%", str(self.serial))
        env_file_content = env_file_content.replace("%LOG%", str(self.log))
        env_file_content = env_file_content.replace("%UDS%", str(self.uds))
        return env_file_content

    def _delete_logfiles(self) -> None:
        from utils.fs_utils import run_remove_routines

        for log in list(self.log_dir.glob("klippy.log*")):
        files = self.log_dir.iterdir()
        logs = [f for f in files if f.name.startswith(KLIPPER_LOG_NAME)]
        for log in logs:
            Logger.print_status(f"Remove '{log}'")
            run_remove_routines(log)
