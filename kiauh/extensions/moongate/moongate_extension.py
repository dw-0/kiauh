# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Paul Sharman <github.com/PEEKYPAUL>                 #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  It integrates Moongate for Klipper:                                    #
#  https://github.com/PEEKYPAUL/Moongate                                  #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import os
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Dict, List

from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.i18n import _tr
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from extensions.base_extension import BaseExtension
from extensions.moongate import (
    MOONGATE_CONFIG_SECTION,
    MOONGATE_DEFAULT_PORT,
    MOONGATE_DIR,
    MOONGATE_INSTALL_SCRIPT,
    MOONGATE_REPO,
    MOONGATE_REPO_URL,
    MOONGATE_UNINSTALL_SCRIPT,
    MOONGATE_UPDATE_SCRIPT,
    MOONGATE_UPDATER_NAME,
)
from utils.config_utils import remove_config_section
from utils.fs_utils import check_file_exist
from utils.git_utils import GitException, git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm, get_number_input
from utils.instance_utils import get_instances


# noinspection PyMethodMayBeStatic
class MoongateExtension(BaseExtension):
    """
    Moongate ships a substantial, security-sensitive and idempotent installer
    (cloudflared, two systemd services, an EdDSA auth proxy, a Moonraker host
    rebind and a tightly-scoped Avahi sudoers entry). Rather than mirror all
    of that in Python — where it would drift out of sync with upstream — this
    extension does the KIAUH-idiomatic parts natively (instance discovery,
    confirmation, moonraker.conf backup, the repo clone wired to the update
    manager) and delegates the heavy lifting to Moongate's own scripts.
    """

    def install_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Installing Moongate for Klipper ..."))

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if not mr_instances:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    _tr("No Moonraker instances found!"),
                    _tr("Moongate is a Moonraker component and needs Moonraker to be installed first. Please install Moonraker, then try again."),
                ],
            )
            return

        moonraker = mr_instances[0]
        if len(mr_instances) > 1:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    _tr("Multiple Moonraker instances detected."),
                    _tr("Moongate currently supports a single-printer setup. The instance '{}' will be used.").format(
                        moonraker.data_dir.name
                    ),
                ],
            )

        if not self._confirm_install():
            Logger.print_info(_tr("Installation aborted."))
            return

        port = get_number_input(
            _tr("HTTP port your Mainsail/Fluidd UI is served on"),
            min_value=1,
            max_value=65535,
            default=MOONGATE_DEFAULT_PORT,
        )
        if port is None:
            return

        lan_only = get_confirm(
            _tr("Install in LAN-only mode (no cloud tunnel, LAN/VPN access only)?"),
            default_choice=False,
            allow_go_back=True,
        )
        if lan_only is None:
            return

        try:
            self._clone_or_update_repo()

            BackupService().backup_moonraker_conf()

            self._run_script(
                MOONGATE_INSTALL_SCRIPT,
                moonraker,
                extra_env={
                    "MOONGATE_PORT": str(port),
                    "MOONGATE_LAN_ONLY": "1" if lan_only else "0",
                },
            )
        except (GitException, CalledProcessError, OSError) as e:
            Logger.print_error(_tr("Error during Moongate installation:\n{}").format(e))
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            [
                _tr("Moongate installed successfully!"),
                "\n\n",
                _tr("Next steps:"),
                _tr("● Install the Moongate app on your Android device."),
                (
                    _tr("● In the app: Add printer > Direct (LAN/VPN), then run MOONGATE_PAIR in the Klipper console and scan the QR (or type the printer's address).")
                    if lan_only
                    else _tr("● Run MOONGATE_PAIR in the Klipper console (or open the pair page printed above) and scan the QR code.")
                ),
                _tr("● Updates from now on: Mainsail/Fluidd > Software Updates > Moongate."),
            ],
            margin_bottom=1,
        )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Updating Moongate for Klipper ..."))

        if not check_file_exist(MOONGATE_DIR.joinpath(".git")):
            Logger.print_info(_tr("Moongate does not seem to be installed. Skipping ..."))
            return

        mr_instances: List[Moonraker] = get_instances(Moonraker)
        if not mr_instances:
            Logger.print_warn(_tr("No Moonraker instance found. Skipping ..."))
            return

        try:
            git_pull_wrapper(MOONGATE_DIR)
            self._run_script(MOONGATE_UPDATE_SCRIPT, mr_instances[0])
            InstanceManager.restart_all(mr_instances)
        except (GitException, CalledProcessError, OSError) as e:
            Logger.print_error(_tr("Error during Moongate update:\n{}").format(e))
            return

        Logger.print_ok(_tr("Moongate updated successfully."), end="\n\n")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status(_tr("Removing Moongate for Klipper ..."))

        mr_instances: List[Moonraker] = get_instances(Moonraker)

        if not get_confirm(
            _tr("This removes Moongate, cloudflared, both systemd services and all Moongate config. Continue?"),
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info(_tr("Removal aborted."))
            return

        if check_file_exist(MOONGATE_UNINSTALL_SCRIPT):
            try:
                BackupService().backup_moonraker_conf()
                target = mr_instances[0] if mr_instances else None
                self._run_script(
                    MOONGATE_UNINSTALL_SCRIPT,
                    target,
                    extra_env={"MOONGATE_YES": "1"},
                )
                Logger.print_ok(_tr("Moongate removed successfully."))
                return
            except (CalledProcessError, OSError) as e:
                Logger.print_error(_tr("Error during Moongate removal:\n{}").format(e))

        Logger.print_warn(
            _tr("Moongate uninstaller not found — doing a best-effort cleanup. You may need to remove cloudflared and the moongate-* systemd services manually.")
        )
        if mr_instances:
            BackupService().backup_moonraker_conf()
            remove_config_section(MOONGATE_UPDATER_NAME, mr_instances)
            remove_config_section(MOONGATE_CONFIG_SECTION, mr_instances)
            InstanceManager.restart_all(mr_instances)
        Logger.print_ok(_tr("Moongate configuration removed."))

    # ------------------------------------------------------------------ #
    #  helpers                                                            #
    # ------------------------------------------------------------------ #
    def _confirm_install(self) -> bool:
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                _tr("Moongate pairs this printer with the Moongate Android app for secure remote access and print monitoring."),
                "\n\n",
                _tr("This is a heavier install than most extensions. It will:"),
                _tr("● clone the Moongate repo to ~/moongate"),
                _tr("● add the Moongate component to Moonraker and register it with the update manager"),
                _tr("● install cloudflared and open a Cloudflare quick-tunnel"),
                _tr("● add two systemd services: moongate-authproxy + moongate-tunnel"),
                _tr("● bind Moonraker to 127.0.0.1 (the auth proxy fronts the tunnel)"),
                _tr("● add a tightly-scoped Avahi sudoers entry for LAN discovery"),
                "\n\n",
                _tr("Prefer no cloud at all? A LAN-only option is offered after this dialog - it skips the tunnel, the auth proxy and the Moonraker rebind, and the printer stays reachable over your LAN or your own VPN only."),
                "\n\n",
                _tr("Remote access relies on cloud infrastructure operated by the Moongate author. Moongate is licensed under PolyForm Noncommercial 1.0.0 (non-commercial use only)."),
                MOONGATE_REPO_URL,
            ],
            margin_bottom=1,
        )
        return bool(
            get_confirm(
                _tr("Continue Moongate installation?"),
                default_choice=True,
                allow_go_back=True,
            )
        )

    def _clone_or_update_repo(self) -> None:
        if check_file_exist(MOONGATE_DIR.joinpath(".git")):
            git_pull_wrapper(MOONGATE_DIR)
        else:
            git_clone_wrapper(MOONGATE_REPO, MOONGATE_DIR)

    def _run_script(
        self,
        script: Path,
        moonraker: Moonraker | None,
        extra_env: Dict[str, str] | None = None,
    ) -> None:
        env = os.environ.copy()
        if moonraker is not None:
            env["MOONRAKER_DIR"] = moonraker.moonraker_dir.as_posix()
            env["PRINTER_DATA"] = moonraker.data_dir.as_posix()
        if extra_env:
            env.update(extra_env)
        run(["bash", script.as_posix()], env=env, check=True)
