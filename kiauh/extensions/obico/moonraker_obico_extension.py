# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.instance_manager.base_instance import SUFFIX_BLACKLIST
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from extensions.obico import (
    OBICO_CFG_SAMPLE_NAME,
    OBICO_DIR,
    OBICO_ENV_DIR,
    OBICO_MACROS_CFG_NAME,
    OBICO_REPO,
    OBICO_REQ_FILE,
    OBICO_UPDATE_CFG_NAME,
    OBICO_UPDATE_CFG_SAMPLE_NAME,
)
from extensions.obico.moonraker_obico import (
    MoonrakerObico,
)
from utils.common import check_install_dependencies, moonraker_exists
from utils.config_utils import (
    add_config_section,
    remove_config_section,
)
from utils.fs_utils import run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm, get_selection_input, get_string_input
from utils.instance_utils import get_instances
from utils.sys_utils import (
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    install_python_requirements,
    parse_packages_from_file,
)


# noinspection PyMethodMayBeStatic
class ObicoExtension(BaseExtension):
    server_url: str

    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing Obico for Klipper ...")

        # check if moonraker is installed. if not, notify the user and exit
        if not moonraker_exists():
            return

        # if obico is already installed, ask if the user wants to repair an
        # incomplete installation or link to the obico server
        force_clone = False
        obico_instances: List[MoonrakerObico] = get_instances(MoonrakerObico)
        if obico_instances:
            self._print_is_already_installed()
            options = ["l", "r", "b"]
            action = get_selection_input("Perform action", option_list=options)
            if action.lower() == "b":
                Logger.print_info("Exiting Obico for Klipper installation ...")
                return
            elif action.lower() == "l":
                unlinked_instances: List[MoonrakerObico] = [
                    obico for obico in obico_instances if not obico.is_linked
                ]
                self._link_obico_instances(unlinked_instances)
                return
            else:
                Logger.print_status("Re-Installing Obico for Klipper ...")
                force_clone = True

        # let the user confirm installation
        kl_instances: List[Klipper] = get_instances(Klipper)
        mr_instances: List[Moonraker] = get_instances(Moonraker)
        self._print_moonraker_instances(mr_instances)
        if not get_confirm(
            "Continue Obico for Klipper installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            return

        try:
            git_clone_wrapper(OBICO_REPO, OBICO_DIR, force=force_clone)
            self._install_dependencies()

            # ask the user for the obico server url
            self._get_server_url()

            # create obico instances
            for moonraker in mr_instances:
                instance = MoonrakerObico(suffix=moonraker.suffix)
                instance.create()

                cmd_sysctl_service(instance.service_file_path.name, "enable")

                # create obico config
                self._create_obico_cfg(instance, moonraker)

                # create obico macros
                self._create_obico_macros_cfg(moonraker)

                # create obico update manager
                self._create_obico_update_manager_cfg(moonraker)

                cmd_sysctl_service(instance.service_file_path.name, "start")

            cmd_sysctl_manage("daemon-reload")

            # add to klippers config
            self._patch_printer_cfg(kl_instances)
            InstanceManager.restart_all(kl_instances)

            # add to moonraker update manager
            self._patch_moonraker_conf(mr_instances)
            InstanceManager.restart_all(mr_instances)

            # check linking of / ask for linking instances
            self._check_and_opt_link_instances()

            Logger.print_dialog(
                DialogType.SUCCESS,
                ["Obico for Klipper successfully installed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper installation:\n{e}")

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating Obico for Klipper ...")
        try:
            instances = get_instances(MoonrakerObico)
            InstanceManager.stop_all(instances)

            git_pull_wrapper(OBICO_DIR)
            self._install_dependencies()

            InstanceManager.start_all(instances)
            Logger.print_ok("Obico for Klipper successfully updated!")

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper update:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing Obico for Klipper ...")

        kl_instances: List[Klipper] = get_instances(Klipper)
        mr_instances: List[Moonraker] = get_instances(Moonraker)
        ob_instances: List[MoonrakerObico] = get_instances(MoonrakerObico)

        try:
            self._remove_obico_instances(ob_instances)
            self._remove_obico_dir()
            self._remove_obico_env()
            remove_config_section(f"include {OBICO_MACROS_CFG_NAME}", kl_instances)
            remove_config_section(f"include {OBICO_UPDATE_CFG_NAME}", mr_instances)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["Obico for Klipper successfully removed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper removal:\n{e}")

    def _obico_server_url_prompt(self) -> None:
        Logger.print_dialog(
            DialogType.CUSTOM,
            custom_title="Obico Server URL",
            content=[
                "You can use a self-hosted Obico Server or the Obico Cloud. "
                "For more information, please visit:",
                "https://obico.io.",
                "\n\n",
                "For the Obico Cloud, leave it as the default:",
                "https://app.obico.io.",
                "\n\n",
                "For self-hosted server, specify:",
                "http://server_ip:port",
                "For instance, 'http://192.168.0.5:3334'.",
            ],
        )

    def _print_moonraker_instances(self, mr_instances: List[Moonraker]) -> None:
        mr_names = [f"● {moonraker.data_dir.name}" for moonraker in mr_instances]
        if len(mr_names) > 1:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "The following Moonraker instances were found:",
                    *mr_names,
                    "\n\n",
                    "The setup will apply the same names to Obico!",
                ],
            )

    def _print_is_already_installed(self) -> None:
        Logger.print_dialog(
            DialogType.INFO,
            [
                "Obico is already installed!",
                "It is safe to run the installer again to link your "
                "printer or repair any issues.",
                "\n\n",
                "You can perform the following actions:",
                "L) Link printer to the Obico server",
                "R) Repair installation",
            ],
        )

    def _get_server_url(self) -> None:
        self._obico_server_url_prompt()
        pattern = r"^(http|https)://[a-zA-Z0-9./?=_%:-]*$"
        self.server_url = get_string_input(
            "Obico Server URL",
            regex=pattern,
            default="https://app.obico.io",
        )

    def _install_dependencies(self) -> None:
        # install dependencies
        script = OBICO_DIR.joinpath("install.sh")
        package_list = parse_packages_from_file(script)
        check_install_dependencies({*package_list})

        # create virtualenv
        if create_python_venv(OBICO_ENV_DIR):
            install_python_requirements(OBICO_ENV_DIR, OBICO_REQ_FILE)

    def _create_obico_macros_cfg(self, moonraker: Moonraker) -> None:
        macros_cfg = OBICO_DIR.joinpath(f"include_cfgs/{OBICO_MACROS_CFG_NAME}")
        macros_target = moonraker.base.cfg_dir.joinpath(OBICO_MACROS_CFG_NAME)
        if not macros_target.exists():
            shutil.copy(macros_cfg, macros_target)
        else:
            Logger.print_info(
                f"Obico's '{OBICO_MACROS_CFG_NAME}' in {moonraker.base.cfg_dir} already exists! Skipped ..."
            )

    def _create_obico_update_manager_cfg(self, moonraker: Moonraker) -> None:
        update_cfg = OBICO_DIR.joinpath(OBICO_UPDATE_CFG_SAMPLE_NAME)
        update_cfg_target = moonraker.base.cfg_dir.joinpath(OBICO_UPDATE_CFG_NAME)
        if not update_cfg_target.exists():
            shutil.copy(update_cfg, update_cfg_target)
        else:
            Logger.print_info(
                f"Obico's '{OBICO_UPDATE_CFG_NAME}' in {moonraker.base.cfg_dir} already exists! Skipped ..."
            )

    def _create_obico_cfg(
        self, current_instance: MoonrakerObico, moonraker: Moonraker
    ) -> None:
        cfg_template = OBICO_DIR.joinpath(OBICO_CFG_SAMPLE_NAME)
        cfg_target_file = current_instance.cfg_file

        if not cfg_template.exists():
            Logger.print_error(
                f"Obico config template file {cfg_target_file} does not exist!"
            )
            return

        if not cfg_target_file.exists():
            shutil.copy(cfg_template, cfg_target_file)
            self._patch_obico_cfg(moonraker, current_instance)
        else:
            Logger.print_info(
                f"Obico config in {current_instance.base.cfg_dir} already exists! Skipped ..."
            )

    def _patch_obico_cfg(self, moonraker: Moonraker, obico: MoonrakerObico) -> None:
        scp = SimpleConfigParser()
        scp.read_file(obico.cfg_file)
        scp.set_option("server", "url", self.server_url)
        scp.set_option("moonraker", "port", str(moonraker.port))
        scp.set_option(
            "logging",
            "path",
            obico.base.log_dir.joinpath(obico.log_file_name).as_posix(),
        )
        scp.write_file(obico.cfg_file)

    def _patch_printer_cfg(self, klipper: List[Klipper]) -> None:
        add_config_section(
            section=f"include {OBICO_MACROS_CFG_NAME}", instances=klipper
        )

    def _patch_moonraker_conf(self, instances: List[Moonraker]) -> None:
        add_config_section(
            section=f"include {OBICO_UPDATE_CFG_NAME}", instances=instances
        )

    def _link_obico_instances(self, unlinked_instances) -> None:
        for obico in unlinked_instances:
            obico.link()

    def _check_and_opt_link_instances(self) -> None:
        Logger.print_status("Checking link status of Obico instances ...")

        suffix_blacklist: List[str] = [
            suffix for suffix in SUFFIX_BLACKLIST if suffix != "obico"
        ]
        ob_instances: List[MoonrakerObico] = get_instances(
            MoonrakerObico, suffix_blacklist=suffix_blacklist
        )
        unlinked_instances: List[MoonrakerObico] = [
            obico for obico in ob_instances if not obico.is_linked
        ]
        if unlinked_instances:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "The Obico instances for the following printers are not "
                    "linked to the server:",
                    *[f"● {obico.data_dir.name}" for obico in unlinked_instances],
                    "\n\n",
                    "It will take only 10 seconds to link the printer to the Obico server.",
                    "For more information visit:",
                    "https://www.obico.io/docs/user-guides/klipper-setup/",
                    "\n\n",
                    "If you don't want to link the printer now, you can restart the "
                    "linking process later by running this installer again.",
                ],
            )
            if not get_confirm("Do you want to link the printers now?"):
                Logger.print_info("Linking to Obico server skipped ...")
                return

            self._link_obico_instances(unlinked_instances)

    def _remove_obico_instances(
        self,
        instance_list: List[MoonrakerObico],
    ) -> None:
        if not instance_list:
            Logger.print_info("No Obico instances found. Skipped ...")
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)

    def _remove_obico_dir(self) -> None:
        Logger.print_status("Removing Obico for Klipper directory ...")

        if not OBICO_DIR.exists():
            Logger.print_info(f"'{OBICO_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OBICO_DIR)

    def _remove_obico_env(self) -> None:
        Logger.print_status("Removing Obico for Klipper environment ...")

        if not OBICO_ENV_DIR.exists():
            Logger.print_info(f"'{OBICO_ENV_DIR}' does not exist. Skipped ...")
            return

        run_remove_routines(OBICO_ENV_DIR)
