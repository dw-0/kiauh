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
import traceback
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client import CLIENTS
from components.webui_client.base_data import BaseWebClient, BaseWebClientConfig
from components.webui_client.client_dialogs import print_client_already_installed_dialog
from components.webui_client.client_utils import (
    backup_client_config_data,
    create_client_config_symlink,
    detect_client_cfg_conflict,
)
from core.i18n import _tr
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from core.services.backup_service import BackupService
from core.services.message_service import Message, MessageService
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.config_utils import (
    add_config_section,
    add_config_section_at_top,
    remove_config_section,
)
from utils.fs_utils import run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances


class WebClientConfigSetupService:
    """Headless-capable service for installing, updating and removing web client configs."""

    CLIENTS = CLIENTS

    def __init__(self, name: str) -> None:
        if name not in self.CLIENTS:
            raise ValueError(f"Unknown web client: {name}")
        self.name = name
        self.client: BaseWebClient = self.CLIENTS[name]()
        self.settings = KiauhSettings()

    def install(
        self,
        cfg_backup: bool = True,
        interactive: bool = True,
    ) -> bool:
        client_config: BaseWebClientConfig = self.client.client_config
        display_name = client_config.display_name

        if detect_client_cfg_conflict(self.client):
            Logger.print_info(
                _tr("Another Client-Config is already installed! Skipped ...")
            )
            return True

        if client_config.config_dir.exists():
            if interactive:
                print_client_already_installed_dialog(display_name)
                if get_confirm(_tr("Re-install {}?").format(display_name), allow_go_back=True):
                    shutil.rmtree(client_config.config_dir)
                else:
                    return True
            else:
                Logger.print_info(
                    _tr("{} is already installed; skipping non-interactive install.").format(
                        display_name
                    )
                )
                return True

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        kl_instances: List[Klipper] = get_instances(Klipper)

        try:
            self.__download_client_config(client_config)
            create_client_config_symlink(client_config, kl_instances)

            if cfg_backup:
                BackupService().backup_printer_config_dir()

            add_config_section(
                section=f"update_manager {client_config.name}",
                instances=mr_instances,
                options=[
                    ("type", "git_repo"),
                    ("primary_branch", "master"),
                    ("path", str(client_config.config_dir)),
                    ("origin", str(client_config.repo_url)),
                    ("managed_services", "klipper"),
                ],
            )
            add_config_section_at_top(client_config.config_section, kl_instances)
            InstanceManager.restart_all(kl_instances)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("{} installation failed!").format(display_name))
            return False

        Logger.print_ok(_tr("{} installation complete!").format(display_name), start="\n")
        return True

    def update(self, interactive: bool = True) -> bool:
        client_config: BaseWebClientConfig = self.client.client_config

        Logger.print_status(_tr("Updating {} ...").format(client_config.display_name))

        if not client_config.config_dir.exists():
            Logger.print_info(
                _tr("Unable to update {}. Directory does not exist! Skipping ...").format(
                    client_config.display_name
                )
            )
            return True

        if self.settings.kiauh.backup_before_update:
            backup_client_config_data(self.client)

        try:
            git_pull_wrapper(client_config.config_dir)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Updating {} failed!").format(client_config.display_name))
            return False

        Logger.print_ok(_tr("Successfully updated {}.").format(client_config.display_name))
        if interactive:
            Logger.print_info(_tr("Restart Klipper to reload the configuration!"))
        return True

    def remove(
        self,
        backup_config: bool = True,
    ) -> bool:
        client_config: BaseWebClientConfig = self.client.client_config
        try:
            message = self.remove_config(
                kl_instances=get_instances(Klipper),
                mr_instances=get_instances(Moonraker),
                backup_config=backup_config,
            )
            MessageService().set_message(message)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Error while removing {}!").format(client_config.display_name))
            return False
        return True

    def remove_config(
        self,
        kl_instances: List[Klipper],
        mr_instances: List[Moonraker],
        backup_config: bool = True,
        svc: BackupService | None = None,
    ) -> Message:
        client_config: BaseWebClientConfig = self.client.client_config
        completion_msg = Message(
            title=_tr("{} Removal Process completed").format(client_config.display_name),
            color=Color.GREEN,
        )
        Logger.print_status(_tr("Removing {} ...").format(client_config.display_name))
        if run_remove_routines(client_config.config_dir):
            completion_msg.text.append(
                _tr("● {} removed").format(client_config.display_name)
            )

        if svc is None:
            svc = BackupService()

        svc.backup_moonraker_conf()
        self.__remove_moonraker_config_section(
            completion_msg, client_config, mr_instances
        )
        svc.backup_printer_cfg()
        self.__remove_printer_config_section(
            completion_msg, client_config, kl_instances
        )

        if completion_msg.text:
            completion_msg.text.insert(0, _tr("The following actions were performed:"))
        else:
            completion_msg.color = Color.YELLOW
            completion_msg.centered = True
            completion_msg.text = [_tr("Nothing to remove.")]
        return completion_msg

    def __download_client_config(self, client_config: BaseWebClientConfig) -> None:
        Logger.print_status(_tr("Downloading {} ...").format(client_config.display_name))
        git_clone_wrapper(client_config.repo_url, client_config.config_dir)

    @staticmethod
    def __update_msg(instances: list, message: Message, text: str) -> Message:
        if not instances:
            return message
        instance_names = [i.service_file_path.stem for i in instances]
        message.text.append(_tr("● {}: {}").format(text, ", ".join(instance_names)))
        return message

    def __remove_printer_config_section(
        self,
        message: Message,
        client_config: BaseWebClientConfig,
        kl_instances: List[Klipper],
    ) -> None:
        kl_section = client_config.config_section
        handled = remove_config_section(kl_section, kl_instances)
        self.__update_msg(
            handled,
            message,
            _tr("Klipper config section '{}' removed for instance").format(kl_section),
        )

    def __remove_moonraker_config_section(
        self,
        message: Message,
        client_config: BaseWebClientConfig,
        mr_instances: List[Moonraker],
    ) -> None:
        mr_section = f"update_manager {client_config.name}"
        handled = remove_config_section(mr_section, mr_instances)
        self.__update_msg(
            handled,
            message,
            _tr("Moonraker config section '{}' removed for instance").format(mr_section),
        )
