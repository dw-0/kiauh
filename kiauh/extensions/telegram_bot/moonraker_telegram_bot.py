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

from core.instance_manager.base_instance import BaseInstance
from utils.constants import SYSTEMD
from utils.logger import Logger

MODULE_PATH = Path(__file__).resolve().parent

TELEGRAM_BOT_DIR = Path.home().joinpath("moonraker-telegram-bot")
TELEGRAM_BOT_ENV = Path.home().joinpath("moonraker-telegram-bot-env")
TELEGRAM_BOT_REPO = "https://github.com/nlef/moonraker-telegram-bot.git"


# noinspection PyMethodMayBeStatic
# todo: make this to a dataclass
class MoonrakerTelegramBot(BaseInstance):
    @classmethod
    def blacklist(cls) -> List[str]:
        return ["None", "mcu"]

    def __init__(self, suffix: str = ""):
        super().__init__(instance_type=self, suffix=suffix)
        self.bot_dir: Path = TELEGRAM_BOT_DIR
        self.env_dir: Path = TELEGRAM_BOT_ENV
        self._cfg_file = self.cfg_dir.joinpath("telegram.conf")
        self._log = self.log_dir.joinpath("telegram.log")
        self._assets_dir = MODULE_PATH.joinpath("assets")

    @property
    def cfg_file(self) -> Path:
        return self._cfg_file

    @property
    def log(self) -> Path:
        return self._log

    def create(self) -> None:
        Logger.print_status("Creating new Moonraker Telegram Bot Instance ...")
        service_template_path = MODULE_PATH.joinpath(
            "assets/moonraker-telegram-bot.service"
        )
        service_file_name = self.get_service_file_name(extension=True)
        service_file_target = SYSTEMD.joinpath(service_file_name)
        env_template_file_path = MODULE_PATH.joinpath(
            "assets/moonraker-telegram-bot.env"
        )
        env_file_target = self.sysd_dir.joinpath("moonraker-telegram-bot.env")

        try:
            self.create_folders()
            self.write_service_file(
                service_template_path, service_file_target, env_file_target
            )
            self.write_env_file(env_template_file_path, env_file_target)

        except CalledProcessError as e:
            Logger.print_error(
                f"Error creating service file {service_file_target}: {e}"
            )
            raise
        except OSError as e:
            Logger.print_error(f"Error creating env file {env_file_target}: {e}")
            raise

    def delete(self) -> None:
        service_file = self.get_service_file_name(extension=True)
        service_file_path = self.get_service_file_path()

        Logger.print_status(f"Deleting Moonraker Telegram Bot Instance: {service_file}")

        try:
            command = ["sudo", "rm", "-f", service_file_path]
            run(command, check=True)
            Logger.print_ok(f"Service file deleted: {service_file_path}")
        except CalledProcessError as e:
            Logger.print_error(f"Error deleting service file: {e}")
            raise

    def write_service_file(
        self,
        service_template_path: Path,
        service_file_target: Path,
        env_file_target: Path,
    ) -> None:
        service_content = self._prep_service_file(
            service_template_path, env_file_target
        )
        command = ["sudo", "tee", service_file_target.as_posix()]
        run(
            command,
            input=service_content.encode(),
            stdout=DEVNULL,
            check=True,
        )
        Logger.print_ok(f"Service file created: {service_file_target}")

    def write_env_file(
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
            "%TELEGRAM_BOT_DIR%",
            str(self.bot_dir),
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
            "%TELEGRAM_BOT_DIR%",
            str(self.bot_dir),
        )
        env_file_content = env_file_content.replace(
            "%CFG%",
            f"{self.cfg_dir}/printer.cfg",
        )
        env_file_content = env_file_content.replace("%LOG%", str(self.log))
        return env_file_content
