# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
from subprocess import run
from typing import List

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from extensions.base_extension import BaseExtension
from extensions.obico.moonraker_obico import (
    OBICO_DIR,
    OBICO_ENV,
    OBICO_REPO,
    MoonrakerObico,
)
from utils.common import check_install_dependencies, moonraker_exists
from utils.config_utils import add_config_section, remove_config_section
from utils.fs_utils import remove_file
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm, get_selection_input, get_string_input
from utils.logger import DialogType, Logger
from utils.sys_utils import (
    cmd_sysctl_manage,
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
        obico_im = InstanceManager(MoonrakerObico)
        obico_instances: List[MoonrakerObico] = obico_im.instances
        if obico_instances:
            self._print_is_already_installed()
            options = ["l", "L", "r", "R", "b", "B"]
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

        # let the user confirm installation
        kl_im = InstanceManager(Klipper)
        kl_instances: List[Klipper] = kl_im.instances
        mr_im = InstanceManager(Moonraker)
        mr_instances: List[Moonraker] = mr_im.instances
        self._print_moonraker_instances(mr_instances)
        if not get_confirm(
            "Continue Obico for Klipper installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            return

        try:
            git_clone_wrapper(OBICO_REPO, OBICO_DIR)
            self._install_dependencies()

            # ask the user for the obico server url
            self._get_server_url()

            # create obico instances
            for moonraker in mr_instances:
                current_instance = MoonrakerObico(suffix=moonraker.suffix)

                obico_im.current_instance = current_instance
                obico_im.create_instance()
                obico_im.enable_instance()

                # create obico config
                self._create_obico_cfg(current_instance, moonraker)

                # create obico macros
                self._create_obico_macros_cfg(moonraker)

                obico_im.start_instance()

            cmd_sysctl_manage("daemon-reload")

            # add to klippers config
            self._patch_obico_macros(kl_instances)
            kl_im.restart_all_instance()

            # add to moonraker update manager
            self._patch_update_manager(mr_instances)
            mr_im.restart_all_instance()

            # check linking of / ask for linking instances
            self._check_and_opt_link_instances()

            Logger.print_dialog(
                DialogType.SUCCESS,
                ["Obico for Klipper successfully installed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper installation: {e}")

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating Obico for Klipper ...")
        try:
            tb_im = InstanceManager(MoonrakerObico)
            tb_im.stop_all_instance()

            git_pull_wrapper(OBICO_REPO, OBICO_DIR)
            self._install_dependencies()

            tb_im.start_all_instance()
            Logger.print_ok("Obico for Klipper successfully updated!")

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper update: {e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing Obico for Klipper ...")
        kl_im = InstanceManager(Klipper)
        kl_instances: List[Klipper] = kl_im.instances
        mr_im = InstanceManager(Moonraker)
        mr_instances: List[Moonraker] = mr_im.instances
        ob_im = InstanceManager(MoonrakerObico)
        ob_instances: List[MoonrakerObico] = ob_im.instances

        try:
            self._remove_obico_instances(ob_im, ob_instances)
            self._remove_obico_dir()
            self._remove_obico_env()
            remove_config_section("include moonraker_obico_macros.cfg", kl_instances)
            remove_config_section("update_manager moonraker-obico", mr_instances)
            remove_config_section("include moonraker-obico-update.cfg", mr_instances)
            self._delete_obico_logs(ob_instances)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["Obico for Klipper successfully removed!"],
                center_content=True,
            )

        except Exception as e:
            Logger.print_error(f"Error during Obico for Klipper removal: {e}")

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
            end="",
        )

    def _print_moonraker_instances(self, mr_instances) -> None:
        mr_names = [f"● {moonraker.data_dir_name}" for moonraker in mr_instances]
        if len(mr_names) > 1:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "The following Moonraker instances were found:",
                    *mr_names,
                    "\n\n",
                    "The setup will apply the same names to Obico!",
                ],
                end="",
            )

    def _print_is_already_installed(self) -> None:
        Logger.print_dialog(
            DialogType.INFO,
            [
                "Obico is already installed!",
                "It is save to run the installer again to link your "
                "printer or repair any issues.",
                "\n\n",
                "You can perform the following actions:",
                "L) Link printer to the Obico server",
                "R) Repair installation",
            ],
            end="",
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
        check_install_dependencies(package_list)

        # create virtualenv
        create_python_venv(OBICO_ENV)
        requirements = OBICO_DIR.joinpath("requirements.txt")
        install_python_requirements(OBICO_ENV, requirements)

    def _create_obico_macros_cfg(self, moonraker) -> None:
        macros_cfg = OBICO_DIR.joinpath("include_cfgs/moonraker_obico_macros.cfg")
        macros_target = moonraker.cfg_dir.joinpath("moonraker_obico_macros.cfg")
        if not macros_target.exists():
            run(["cp", macros_cfg, macros_target], check=True)
        else:
            Logger.print_info(
                f"Obico macros in {moonraker.cfg_dir} already exists! Skipped ..."
            )

    def _create_obico_cfg(self, current_instance, moonraker) -> None:
        cfg_template = OBICO_DIR.joinpath("moonraker-obico.cfg.sample")
        cfg_target_file = current_instance.cfg_file
        if not cfg_target_file.exists():
            run(["cp", cfg_template, cfg_target_file], check=True)
            self._patch_obico_cfg(moonraker, current_instance)
        else:
            Logger.print_info(
                f"Obico config in {current_instance.cfg_dir} already exists! Skipped ..."
            )

    def _patch_obico_cfg(self, moonraker: Moonraker, obico: MoonrakerObico) -> None:
        cm = ConfigManager(obico.cfg_file)
        cm.set_value("server", "url", self.server_url)
        cm.set_value("moonraker", "port", str(moonraker.port))
        cm.set_value("logging", "path", str(obico.log))
        cm.write_config()

    def _patch_obico_macros(self, klipper: List[Klipper]) -> None:
        add_config_section(
            section="include moonraker_obico_macros.cfg",
            instances=klipper,
        )

    def _patch_update_manager(self, instances: List[Moonraker]) -> None:
        env_py = f"{OBICO_ENV}/bin/python"
        add_config_section(
            section="update_manager moonraker-obico",
            instances=instances,
            options=[
                ("type", "git_repo"),
                ("path", str(OBICO_DIR)),
                ("orgin", OBICO_REPO),
                ("env", env_py),
                ("requirements", "requirements.txt"),
                ("install_script", "install.sh"),
                ("managed_services", "moonraker-obico"),
            ],
        )

    def _link_obico_instances(self, unlinked_instances):
        for obico in unlinked_instances:
            obico.link()

    def _check_and_opt_link_instances(self):
        Logger.print_status("Checking link status of Obico instances ...")
        ob_im = InstanceManager(MoonrakerObico)
        ob_instances: List[MoonrakerObico] = ob_im.instances
        unlinked_instances: List[MoonrakerObico] = [
            obico for obico in ob_instances if not obico.is_linked
        ]
        if unlinked_instances:
            Logger.print_dialog(
                DialogType.INFO,
                [
                    "The Obico instances for the following printers are not "
                    "linked to the server:",
                    *[f"● {obico.data_dir_name}" for obico in unlinked_instances],
                    "\n\n",
                    "It will take only 10 seconds to link the printer to the Obico server.",
                    "For more information visit:",
                    "https://www.obico.io/docs/user-guides/klipper-setup/",
                    "\n\n",
                    "If you don't want to link the printer now, you can restart the "
                    "linking process later by running this installer again.",
                ],
                end="",
            )
            if not get_confirm("Do you want to link the printers now?"):
                self._link_obico_instances(unlinked_instances)
            else:
                Logger.print_info("Linking to server skipped ...")

    def _remove_obico_instances(
        self,
        instance_manager: InstanceManager,
        instance_list: List[MoonrakerObico],
    ) -> None:
        if not instance_list:
            Logger.print_info("No Obico instances found. Skipped ...")
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.get_service_file_name()} ..."
            )
            instance_manager.current_instance = instance
            instance_manager.stop_instance()
            instance_manager.disable_instance()
            instance_manager.delete_instance()

        cmd_sysctl_manage("daemon-reload")

    def _remove_obico_dir(self) -> None:
        if not OBICO_DIR.exists():
            Logger.print_info(f"'{OBICO_DIR}' does not exist. Skipped ...")
            return

        try:
            shutil.rmtree(OBICO_DIR)
        except OSError as e:
            Logger.print_error(f"Unable to delete '{OBICO_DIR}':\n{e}")

    def _remove_obico_env(self) -> None:
        if not OBICO_ENV.exists():
            Logger.print_info(f"'{OBICO_ENV}' does not exist. Skipped ...")
            return

        try:
            shutil.rmtree(OBICO_ENV)
        except OSError as e:
            Logger.print_error(f"Unable to delete '{OBICO_ENV}':\n{e}")

    def _delete_obico_logs(self, instances: List[MoonrakerObico]) -> None:
        Logger.print_status("Removing Obico logs ...")
        all_logfiles = []
        for instance in instances:
            all_logfiles = list(instance.log_dir.glob("moonraker-obico.log*"))
        if not all_logfiles:
            Logger.print_info("No Obico logs found. Skipped ...")
            return

        for log in all_logfiles:
            Logger.print_status(f"Remove '{log}'")
            remove_file(log)
