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
import tempfile
import traceback
from pathlib import Path
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from components.webui_client import CLIENTS, MODULE_PATH
from components.webui_client.base_data import BaseWebClient, WebClientType
from components.webui_client.client_dialogs import (
    print_install_client_config_dialog,
    print_moonraker_not_found_dialog,
)
from components.webui_client.client_utils import (
    copy_common_vars_nginx_cfg,
    copy_upstream_nginx_cfg,
    create_nginx_cfg,
    detect_client_cfg_conflict,
    enable_mainsail_remotemode,
    get_client_port_selection,
    symlink_webui_nginx_log,
)
from components.webui_client.services.web_client_config_setup_service import (
    WebClientConfigSetupService,
)
from core.constants import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from core.i18n import _tr
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.services.message_service import Message, MessageService
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.common import check_install_dependencies
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_with_sudo, run_remove_routines, unzip
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances
from utils.sys_utils import cmd_sysctl_service, download_file, get_ipv4_addr


class WebClientSetupService:
    """Headless-capable service for installing, updating and removing web clients."""

    CLIENTS = CLIENTS

    def __init__(self, name: str) -> None:
        if name not in self.CLIENTS:
            raise ValueError(f"Unknown web client: {name}")
        self.name = name
        self.client: BaseWebClient = self.CLIENTS[name]()
        self.settings = KiauhSettings()

    def install(
        self,
        reinstall: bool = False,
        interactive: bool = True,
        port: int | None = None,
        install_client_cfg: bool | None = None,
        continue_without_moonraker: bool = False,
    ) -> bool:
        mr_instances: List[Moonraker] = get_instances(Moonraker)

        enable_remotemode = False
        if not mr_instances:
            if interactive:
                print_moonraker_not_found_dialog(self.client.display_name)
                if not get_confirm(
                    _tr("Continue {} installation?").format(self.client.display_name)
                ):
                    return False
            elif not continue_without_moonraker:
                Logger.print_info(
                    _tr("Moonraker not installed; skipping {} installation.").format(
                        self.client.display_name
                    )
                )
                return False

        enable_remotemode = self._should_enable_remote_mode(mr_instances)

        kl_instances: List[Klipper] = get_instances(Klipper)
        install_cfg = False
        client_config = self.client.client_config
        if (
            kl_instances
            and not client_config.config_dir.exists()
            and not detect_client_cfg_conflict(self.client)
        ):
            if interactive:
                print_install_client_config_dialog(self.client)
                question = _tr("Download the recommended {}?").format(
                    client_config.display_name
                )
                install_cfg = get_confirm(question, allow_go_back=False)
            else:
                install_cfg = bool(install_client_cfg)

        default_port: int = int(self.settings.get(self.client.name, "port"))
        if port is not None:
            resolved_port = port
        elif interactive and not reinstall:
            resolved_port = get_client_port_selection(self.client, self.settings)
        else:
            resolved_port = default_port

        check_install_dependencies({"nginx"})

        try:
            _download_client(self.client)
            if enable_remotemode and self.client.client == WebClientType.MAINSAIL:
                enable_mainsail_remotemode()

            BackupService().backup_printer_config_dir()
            add_config_section(
                section=f"update_manager {self.client.name}",
                instances=mr_instances,
                options=[
                    ("persistent_files", ["config.json"]),
                    ("type", "web"),
                    ("channel", "stable"),
                    ("repo", str(self.client.repo_path)),
                    ("path", str(self.client.client_dir)),
                ],
            )
            InstanceManager.restart_all(mr_instances)

            if install_cfg and kl_instances:
                WebClientConfigSetupService(self.name).install(
                    cfg_backup=False, interactive=interactive
                )

            copy_upstream_nginx_cfg()
            copy_common_vars_nginx_cfg()
            create_nginx_cfg(
                display_name=self.client.display_name,
                cfg_name=self.client.name,
                template_src=MODULE_PATH.joinpath("assets/nginx_cfg"),
                PORT=resolved_port,
                ROOT_DIR=self.client.client_dir,
                NAME=self.client.name,
            )

            if kl_instances:
                symlink_webui_nginx_log(self.client, kl_instances)
            cmd_sysctl_service("nginx", "restart")
        except Exception:
            Logger.print_error(traceback.format_exc())
            if interactive:
                Logger.print_dialog(
                    DialogType.ERROR,
                    center_content=True,
                    content=[_tr("{} installation failed!").format(self.client.display_name)],
                )
            return False

        webui_url: str = f"http://{get_ipv4_addr()}{'' if resolved_port == 80 else f':{resolved_port}'}"
        if interactive:
            Logger.print_dialog(
                DialogType.CUSTOM,
                custom_title=_tr("{} installation complete!").format(
                    self.client.display_name
                ),
                custom_color=Color.GREEN,
                center_content=True,
                content=[_tr("Open {} now on: {}").format(self.client.display_name, webui_url)],
            )
        else:
            Logger.print_info(
                _tr("Installation of {} complete! URL: {}").format(
                    self.client.display_name, webui_url
                )
            )

        return True

    def _should_enable_remote_mode(self, mr_instances: List[Moonraker]) -> bool:
        return self.client.client == WebClientType.MAINSAIL and (
            not mr_instances or len(mr_instances) > 1
        )

    def update(self, interactive: bool = True) -> bool:
        Logger.print_status(_tr("Updating {} ...").format(self.client.display_name))
        if not self.client.client_dir.exists():
            Logger.print_info(
                _tr("Unable to update {}. Directory does not exist! Skipping ...").format(
                    self.client.display_name
                )
            )
            return True

        try:
            with tempfile.NamedTemporaryFile(suffix=".json") as tmp_file:
                Logger.print_status(
                    _tr("Creating temporary backup of {} as {} ...").format(
                        self.client.config_file, tmp_file.name
                    )
                )
                shutil.copy(self.client.config_file, tmp_file.name)
                _download_client(self.client)
                shutil.copy(tmp_file.name, self.client.config_file)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Updating {} failed!").format(self.client.display_name))
            return False

        return True

    def remove(
        self,
        remove_client: bool = False,
        remove_client_cfg: bool = False,
        backup_config: bool = True,
        interactive: bool = True,
    ) -> bool:
        try:
            message = self._build_removal_message(
                remove_client=remove_client,
                remove_client_cfg=remove_client_cfg,
                backup_config=backup_config,
                interactive=interactive,
            )
            MessageService().set_message(message)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Error while removing {}!").format(self.client.display_name))
            return False
        return True

    def _build_removal_message(
        self,
        remove_client: bool,
        remove_client_cfg: bool,
        backup_config: bool,
        interactive: bool,
    ) -> Message:
        completion_msg = Message(
            title=_tr("{} Removal Process completed").format(self.client.display_name),
            color=Color.GREEN,
        )
        mr_instances: List[Moonraker] = get_instances(Moonraker)
        kl_instances: List[Klipper] = get_instances(Klipper)
        svc = BackupService()

        if backup_config:
            version = ""
            src = self.client.client_dir
            if src.joinpath(".version").exists():
                with open(src.joinpath(".version"), "r") as v:
                    version = v.readlines()[0]

            target_path = svc.backup_root.joinpath(
                f"{self.client.client_dir.name}_{version}"
            )
            success = svc.backup_file(
                source_path=self.client.config_file,
                target_path=target_path,
            )
            if success:
                completion_msg.text.append(
                    _tr("● {} backup created").format(self.client.config_file.name)
                )

        if remove_client:
            if self._remove_client_dir():
                completion_msg.text.append(
                    _tr("● {} removed").format(self.client.display_name)
                )
            if self._remove_client_nginx_config(self.client.name):
                completion_msg.text.append(_tr("● NGINX config removed"))
            if self._remove_client_nginx_logs(self.client, kl_instances):
                completion_msg.text.append(_tr("● NGINX logs removed"))

            svc.backup_moonraker_conf()
            section = f"update_manager {self.client.name}"
            handled_instances = remove_config_section(section, mr_instances)
            if handled_instances:
                names = [i.service_file_path.stem for i in handled_instances]
                completion_msg.text.append(
                    _tr("● Moonraker config section '{}' removed for instance: {}").format(
                        section, ", ".join(names)
                    )
                )

        if remove_client_cfg:
            cfg_svc = WebClientConfigSetupService(self.name)
            cfg_message = cfg_svc.remove_config(
                kl_instances=kl_instances,
                mr_instances=mr_instances,
                backup_config=backup_config,
                svc=svc,
            )
            if cfg_message.color == Color.GREEN:
                completion_msg.text.extend(cfg_message.text[1:])

        if not completion_msg.text:
            completion_msg.color = Color.YELLOW
            completion_msg.centered = True
            completion_msg.text.append(_tr("Nothing to remove."))
        else:
            completion_msg.text.insert(0, _tr("The following actions were performed:"))

        return completion_msg

    def _remove_client_dir(self) -> bool:
        Logger.print_status(_tr("Removing {} ...").format(self.client.display_name))
        return bool(run_remove_routines(self.client.client_dir))

    def _remove_client_nginx_config(self, name: str) -> bool:
        Logger.print_status(_tr("Removing NGINX config for {} ...").format(name.capitalize()))
        return bool(
            remove_with_sudo([
                NGINX_SITES_AVAILABLE.joinpath(name),
                NGINX_SITES_ENABLED.joinpath(name),
            ])
        )

    def _remove_client_nginx_logs(
        self, client: BaseWebClient, instances: List[Klipper]
    ) -> bool:
        Logger.print_status(_tr("Removing NGINX logs for {} ...").format(client.display_name))
        files = [client.nginx_access_log, client.nginx_error_log]
        if instances:
            for instance in instances:
                files.append(
                    instance.base.log_dir.joinpath(client.nginx_access_log.name)
                )
                files.append(
                    instance.base.log_dir.joinpath(client.nginx_error_log.name)
                )
        return bool(remove_with_sudo(files))


def _download_client(client: BaseWebClient) -> None:
    zipfile = f"{client.name.lower()}.zip"
    target = Path().home().joinpath(zipfile)
    try:
        Logger.print_status(
            _tr("Downloading {} from {} ...").format(
                client.display_name, client.download_url
            )
        )
        download_file(client.download_url, target, True)
        Logger.print_ok(_tr("Download complete!"))

        Logger.print_status(_tr("Extracting {} ...").format(zipfile))
        unzip(target, client.client_dir)
        target.unlink(missing_ok=True)
        Logger.print_ok(_tr("OK!"))
    except Exception:
        Logger.print_error(_tr("Downloading {} failed!").format(client.display_name))
        raise
