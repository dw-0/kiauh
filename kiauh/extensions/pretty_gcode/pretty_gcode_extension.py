# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from pathlib import Path

from components.webui_client.client_utils import create_nginx_cfg
from core.constants import NGINX_SITES_AVAILABLE, NGINX_SITES_ENABLED
from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from utils.common import check_install_dependencies
from utils.fs_utils import (
    remove_file,
)
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_number_input
from utils.sys_utils import cmd_sysctl_service, get_ipv4_addr

MODULE_PATH = Path(__file__).resolve().parent
PGC_DIR = Path.home().joinpath("pgcode")
PGC_REPO = "https://github.com/Kragrathea/pgcode"
PGC_CONF = "pgcode.local.conf"


# noinspection PyMethodMayBeStatic
class PrettyGcodeExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing PrettyGCode for Klipper ...")
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Make sure you don't select a port which is already in use by "
                "another application. Your input will not be validated! Choosing a port "
                "which is already in use by another application may cause issues!",
                "The default port is 7136.",
            ],
        )

        port = get_number_input(
            "On which port should PrettyGCode run",
            min_value=0,
            default=7136,
            allow_go_back=True,
        )

        check_install_dependencies({"nginx"})

        try:
            if PGC_DIR.exists():
                shutil.rmtree(PGC_DIR)

            git_clone_wrapper(PGC_REPO, PGC_DIR)

            create_nginx_cfg(
                "PrettyGCode for Klipper",
                cfg_name=PGC_CONF,
                template_src=MODULE_PATH.joinpath(f"assets/{PGC_CONF}"),
                ROOT_DIR=PGC_DIR,
                PORT=port,
            )

            cmd_sysctl_service("nginx", "restart")

            log = f"Open PrettyGCode now on: http://{get_ipv4_addr()}:{port}"
            Logger.print_ok("PrettyGCode installation complete!", start="\n")
            Logger.print_ok(log, prefix=False, end="\n\n")

        except Exception as e:
            Logger.print_error(
                f"Error during PrettyGCode for Klipper installation: {e}"
            )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating PrettyGCode for Klipper ...")
        try:
            git_pull_wrapper(PGC_DIR)

        except Exception as e:
            Logger.print_error(f"Error during PrettyGCode for Klipper update: {e}")

    def remove_extension(self, **kwargs) -> None:
        try:
            Logger.print_status("Removing PrettyGCode for Klipper ...")

            # remove pgc dir
            shutil.rmtree(PGC_DIR)
            # remove nginx config
            remove_file(NGINX_SITES_AVAILABLE.joinpath(PGC_CONF), True)
            remove_file(NGINX_SITES_ENABLED.joinpath(PGC_CONF), True)
            # restart nginx
            cmd_sysctl_service("nginx", "restart")

            Logger.print_ok("PrettyGCode for Klipper removed!")

        except Exception as e:
            Logger.print_error(f"Error during PrettyGCode for Klipper removal: {e}")
