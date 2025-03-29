# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from subprocess import run
from typing import List

from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.telegram_bot import TG_BOT_REPO, TG_BOT_REQ_FILE
from extensions.telegram_bot.moonraker_telegram_bot import (
    TG_BOT_DIR,
    TG_BOT_ENV,
    MoonrakerTelegramBot,
)
from utils.common import check_install_dependencies
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_file
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
    parse_packages_from_file,
)


# noinspection PyMethodMayBeStatic
class TelegramBotExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing Moonraker Telegram Bot ...")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "No Moonraker instances found!",
                    "Moonraker Telegram Bot requires Moonraker to be installed. "
                    "Please install Moonraker first!",
                ],
            )
            return

        instance_names = [
            f"● {instance.service_file_path.name}" for instance in mr_instances
        ]
        Logger.print_dialog(
            DialogType.INFO,
            [
                "The following Moonraker instances were found:",
                *instance_names,
                "\n\n",
                "The setup will apply the same names to Telegram Bot!",
            ],
        )
        if not get_confirm(
            "Continue Moonraker Telegram Bot installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            return

        create_example_cfg = get_confirm("Create example telegram.conf?")

        try:
            git_clone_wrapper(TG_BOT_REPO, TG_BOT_DIR)
            self._install_dependencies()

            # create and start services / create bot configs
            show_config_dialog = False
            tb_names = [mr_i.suffix for mr_i in mr_instances]
            for name in tb_names:
                instance = MoonrakerTelegramBot(suffix=name)
                instance.create()

                cmd_sysctl_service(instance.service_file_path.name, "enable")

                if create_example_cfg:
                    Logger.print_status(
                        f"Creating Telegram Bot config in {instance.base.cfg_dir} ..."
                    )
                    template = TG_BOT_DIR.joinpath("scripts/base_install_template")
                    target_file = instance.cfg_file
                    if not target_file.exists():
                        show_config_dialog = True
                        run(["cp", template, target_file], check=True)
                    else:
                        Logger.print_info(
                            f"Telegram Bot config in {instance.base.cfg_dir} already exists! Skipped ..."
                        )

                cmd_sysctl_service(instance.service_file_path.name, "start")

            cmd_sysctl_manage("daemon-reload")

            # add to moonraker update manager
            self._patch_bot_update_manager(mr_instances)

            # restart moonraker
            InstanceManager.restart_all(mr_instances)

            if show_config_dialog:
                Logger.print_dialog(
                    DialogType.ATTENTION,
                    [
                        "During the installation of the Moonraker Telegram Bot, "
                        "a basic config was created per instance. You need to edit the "
                        "config file to set up your Telegram Bot. Please refer to the "
                        "following wiki page for further information:",
                        "https://github.com/nlef/moonraker-telegram-bot/wiki",
                    ],
                    margin_bottom=1,
                )

            Logger.print_ok("Telegram Bot installation complete!")
        except Exception as e:
            Logger.print_error(
                f"Error during installation of Moonraker Telegram Bot:\n{e}"
            )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating Moonraker Telegram Bot ...")

        instances = get_instances(MoonrakerTelegramBot)
        InstanceManager.stop_all(instances)

        git_pull_wrapper(TG_BOT_DIR)
        self._install_dependencies()

        InstanceManager.start_all(instances)

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing Moonraker Telegram Bot ...")

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        tb_instances: List[MoonrakerTelegramBot] = get_instances(MoonrakerTelegramBot)

        try:
            self._remove_bot_instances(tb_instances)
            self._remove_bot_dir()
            self._remove_bot_env()
            remove_config_section("update_manager moonraker-telegram-bot", mr_instances)
            self._delete_bot_logs(tb_instances)
        except Exception as e:
            Logger.print_error(f"Error during removal of Moonraker Telegram Bot:\n{e}")

        Logger.print_ok("Moonraker Telegram Bot removed!")

    def _install_dependencies(self) -> None:
        # install dependencies
        script = TG_BOT_DIR.joinpath("scripts/install.sh")
        package_list = parse_packages_from_file(script)

        check_install_dependencies({*package_list})

        # create virtualenv
        if create_python_venv(TG_BOT_ENV, allow_access_to_system_site_packages=True):
            install_python_requirements(TG_BOT_ENV, TG_BOT_REQ_FILE)

    def _patch_bot_update_manager(self, instances: List[Moonraker]) -> None:
        env_py = f"{TG_BOT_ENV}/bin/python"
        add_config_section(
            section="update_manager moonraker-telegram-bot",
            instances=instances,
            options=[
                ("type", "git_repo"),
                ("path", str(TG_BOT_DIR)),
                ("origin", TG_BOT_REPO),
                ("env", env_py),
                ("requirements", "scripts/requirements.txt"),
                ("install_script", "scripts/install.sh"),
            ],
        )

    def _remove_bot_instances(
        self,
        instance_list: List[MoonrakerTelegramBot],
    ) -> None:
        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)

    def _remove_bot_dir(self) -> None:
        if not TG_BOT_DIR.exists():
            Logger.print_info(f"'{TG_BOT_DIR}' does not exist. Skipped ...")
            return

        try:
            shutil.rmtree(TG_BOT_DIR)
        except OSError as e:
            Logger.print_error(f"Unable to delete '{TG_BOT_DIR}':\n{e}")

    def _remove_bot_env(self) -> None:
        if not TG_BOT_ENV.exists():
            Logger.print_info(f"'{TG_BOT_ENV}' does not exist. Skipped ...")
            return

        try:
            shutil.rmtree(TG_BOT_ENV)
        except OSError as e:
            Logger.print_error(f"Unable to delete '{TG_BOT_ENV}':\n{e}")

    def _delete_bot_logs(self, instances: List[MoonrakerTelegramBot]) -> None:
        all_logfiles = []
        for instance in instances:
            all_logfiles = list(instance.base.log_dir.glob("telegram_bot.log*"))
        if not all_logfiles:
            Logger.print_info("No Moonraker Telegram Bot logs found. Skipped ...")
            return

        for log in all_logfiles:
            Logger.print_status(f"Remove '{log}'")
            remove_file(log)
