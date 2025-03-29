# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from copy import copy
from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import List

from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import print_instance_overview
from components.klipper.services.klipper_instance_service import KlipperInstanceService
from components.moonraker import (
    EXIT_MOONRAKER_SETUP,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_REPO_URL,
    MOONRAKER_REQ_FILE,
    MOONRAKER_SPEEDUPS_REQ_FILE,
    POLKIT_FILE,
    POLKIT_LEGACY_FILE,
    POLKIT_SCRIPT,
    POLKIT_USR_FILE,
)
from components.moonraker.moonraker import Moonraker
from components.moonraker.moonraker_dialogs import print_moonraker_overview
from components.moonraker.services.moonraker_instance_service import (
    MoonrakerInstanceService,
)
from components.moonraker.utils.utils import (
    backup_moonraker_dir,
    create_example_moonraker_conf,
    install_moonraker_packages,
    remove_polkit_rules,
)
from components.webui_client.client_utils import (
    enable_mainsail_remotemode,
    get_existing_clients,
)
from components.webui_client.mainsail_data import MainsailData
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.message_service import Message, MessageService
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.common import check_install_dependencies
from utils.fs_utils import check_file_exist, run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import (
    get_confirm,
    get_selection_input,
)
from utils.sys_utils import (
    check_python_version,
    cmd_sysctl_manage,
    cmd_sysctl_service,
    create_python_venv,
    get_ipv4_addr,
    install_python_requirements,
    unit_file_exists,
)


# noinspection PyMethodMayBeStatic
class MoonrakerSetupService:
    __cls_instance = None

    kisvc: KlipperInstanceService
    misvc: MoonrakerInstanceService
    msgsvc = MessageService

    settings: KiauhSettings
    klipper_list: List[Klipper]
    moonraker_list: List[Moonraker]

    def __new__(cls) -> "MoonrakerSetupService":
        if cls.__cls_instance is None:
            cls.__cls_instance = super(MoonrakerSetupService, cls).__new__(cls)
        return cls.__cls_instance

    def __init__(self) -> None:
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True
        self.__init_state()

    def __init_state(self) -> None:
        self.settings = KiauhSettings()

        self.kisvc = KlipperInstanceService()
        self.kisvc.load_instances()
        self.klipper_list = self.kisvc.get_all_instances()

        self.misvc = MoonrakerInstanceService()
        self.misvc.load_instances()
        self.moonraker_list = self.misvc.get_all_instances()

        self.msgsvc = MessageService()

    def __refresh_state(self) -> None:
        self.kisvc.load_instances()
        self.klipper_list = self.kisvc.get_all_instances()

        self.misvc.load_instances()
        self.moonraker_list = self.misvc.get_all_instances()

    def install(self) -> None:
        self.__refresh_state()

        if not self.__check_requirements(self.klipper_list):
            return

        new_instances: List[Moonraker] = []
        selected_option: str | Klipper

        if len(self.klipper_list) == 1:
            suffix: str = self.klipper_list[0].suffix
            new_inst = self.misvc.create_new_instance(suffix)
            new_instances.append(new_inst)

        else:
            print_moonraker_overview(
                self.klipper_list,
                self.moonraker_list,
                show_index=True,
                show_select_all=True,
            )
            options = {str(i + 1): k for i, k in enumerate(self.klipper_list)}
            additional_options = {"a": None, "b": None}
            options = {**options, **additional_options}
            question = "Select Klipper instance to setup Moonraker for"
            selected_option = get_selection_input(question, options)

            if selected_option == "b":
                Logger.print_status(EXIT_MOONRAKER_SETUP)
                return

            if selected_option == "a":
                new_inst_list: List[Moonraker] = [
                    self.misvc.create_new_instance(k.suffix) for k in self.klipper_list
                ]
                new_instances.extend(new_inst_list)
            else:
                klipper_instance: Klipper | None = options.get(selected_option)
                if klipper_instance is None:
                    raise Exception("Error selecting instance!")
                new_inst = self.misvc.create_new_instance(klipper_instance.suffix)
                new_instances.append(new_inst)

        create_example_cfg = get_confirm("Create example moonraker.conf?")

        try:
            self.__run_setup(new_instances, create_example_cfg)
        except Exception as e:
            Logger.print_error(f"Error while installing Moonraker: {e}")
            return

    def update(self) -> None:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Be careful if there are ongoing prints running!",
                "All Moonraker instances will be restarted during the update process and "
                "ongoing prints COULD FAIL.",
            ],
        )

        if not get_confirm("Update Moonraker now?"):
            return

        self.__refresh_state()

        if self.settings.kiauh.backup_before_update:
            backup_moonraker_dir()

        InstanceManager.stop_all(self.moonraker_list)
        git_pull_wrapper(MOONRAKER_DIR)
        install_moonraker_packages()
        install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)
        InstanceManager.start_all(self.moonraker_list)

    def remove(
        self,
        remove_service: bool,
        remove_dir: bool,
        remove_env: bool,
        remove_polkit: bool,
    ) -> None:
        self.__refresh_state()

        completion_msg = Message(
            title="Moonraker Removal Process completed",
            color=Color.GREEN,
        )

        if remove_service:
            Logger.print_status("Removing Moonraker instances ...")
            if self.moonraker_list:
                instances_to_remove = self.__get_instances_to_remove()
                self.__remove_instances(instances_to_remove)
                if instances_to_remove:
                    instance_names = [
                        i.service_file_path.stem for i in instances_to_remove
                    ]
                    txt = f"● Moonraker instances removed: {', '.join(instance_names)}"
                    completion_msg.text.append(txt)
            else:
                Logger.print_info("No Moonraker Services installed! Skipped ...")

        if (remove_polkit or remove_dir or remove_env) and unit_file_exists(
            "moonraker", suffix="service"
        ):
            completion_msg.text = [
                "Some Klipper services are still installed:",
                "● Moonraker PolicyKit rules were not removed, even though selected for removal.",
                f"● '{MOONRAKER_DIR}' was not removed, even though selected for removal.",
                f"● '{MOONRAKER_ENV_DIR}' was not removed, even though selected for removal.",
            ]
        else:
            if remove_polkit:
                Logger.print_status("Removing all Moonraker policykit rules ...")
                if remove_polkit_rules():
                    completion_msg.text.append("● Moonraker policykit rules removed")
            if remove_dir:
                Logger.print_status("Removing Moonraker local repository ...")
                if run_remove_routines(MOONRAKER_DIR):
                    completion_msg.text.append("● Moonraker local repository removed")
            if remove_env:
                Logger.print_status("Removing Moonraker Python environment ...")
                if run_remove_routines(MOONRAKER_ENV_DIR):
                    completion_msg.text.append("● Moonraker Python environment removed")

        if completion_msg.text:
            completion_msg.text.insert(0, "The following actions were performed:")
        else:
            completion_msg.color = Color.YELLOW
            completion_msg.centered = True
            completion_msg.text = ["Nothing to remove."]

        self.msgsvc.set_message(completion_msg)

    def __run_setup(
        self, new_instances: List[Moonraker], create_example_cfg: bool
    ) -> None:
        check_install_dependencies()
        self.__install_deps()

        ports_map = self.misvc.get_instance_port_map()
        for i in new_instances:
            i.create()
            cmd_sysctl_service(i.service_file_path.name, "enable")

            if create_example_cfg:
                # if a webclient and/or it's config is installed, patch
                # its update section to the config
                clients = get_existing_clients()
                create_example_moonraker_conf(i, ports_map, clients)

            cmd_sysctl_service(i.service_file_path.name, "start")

        cmd_sysctl_manage("daemon-reload")

        # if mainsail is installed, and we installed
        # multiple moonraker instances, we enable mainsails remote mode
        if MainsailData().client_dir.exists() and len(self.moonraker_list) > 1:
            enable_mainsail_remotemode()

        self.misvc.load_instances()
        new_instances = [
            self.misvc.get_instance_by_suffix(i.suffix) for i in new_instances
        ]

        ip: str = get_ipv4_addr()
        # noinspection HttpUrlsUsage
        url_list = [
            f"● {i.service_file_path.stem}: http://{ip}:{i.port}"
            for i in new_instances
            if i.port
        ]
        dialog_content = []
        if url_list:
            dialog_content.append("You can access Moonraker via the following URL:")
            dialog_content.extend(url_list)

        Logger.print_dialog(
            DialogType.CUSTOM,
            custom_title="Moonraker successfully installed!",
            custom_color=Color.GREEN,
            content=dialog_content,
        )

    def __check_requirements(self, klipper_list: List[Klipper]) -> bool:
        is_klipper_installed = len(klipper_list) >= 1
        if not is_klipper_installed:
            Logger.print_warn("Klipper not installed!")
            Logger.print_warn("Moonraker cannot be installed! Install Klipper first.")

        is_python_ok = check_python_version(3, 7)

        return is_klipper_installed and is_python_ok

    def __install_deps(self) -> None:
        default_repo = (MOONRAKER_REPO_URL, "master")
        repo = self.settings.moonraker.repositories
        # pull the first repo defined in kiauh.cfg or fallback to the official Moonraker repo
        repo, branch = (repo[0].url, repo[0].branch) if repo else default_repo
        git_clone_wrapper(repo, MOONRAKER_DIR, branch)

        try:
            install_moonraker_packages()
            if create_python_venv(MOONRAKER_ENV_DIR):
                install_python_requirements(MOONRAKER_ENV_DIR, MOONRAKER_REQ_FILE)
                install_python_requirements(
                    MOONRAKER_ENV_DIR, MOONRAKER_SPEEDUPS_REQ_FILE
                )
            self.__install_polkit()
        except Exception:
            Logger.print_error("Error during installation of Moonraker requirements!")
            raise

    def __install_polkit(self) -> None:
        Logger.print_status("Installing Moonraker policykit rules ...")

        legacy_file_exists = check_file_exist(POLKIT_LEGACY_FILE, True)
        polkit_file_exists = check_file_exist(POLKIT_FILE, True)
        usr_file_exists = check_file_exist(POLKIT_USR_FILE, True)

        if legacy_file_exists or (polkit_file_exists and usr_file_exists):
            Logger.print_info("Moonraker policykit rules are already installed.")
            return

        try:
            command = [POLKIT_SCRIPT, "--disable-systemctl"]
            result = run(
                command,
                stderr=PIPE,
                stdout=DEVNULL,
                text=True,
            )
            if result.returncode != 0 or result.stderr:
                Logger.print_error(f"{result.stderr}", False)
                Logger.print_error("Installing Moonraker policykit rules failed!")
                return

            Logger.print_ok("Moonraker policykit rules successfully installed!")
        except CalledProcessError as e:
            log = (
                f"Error while installing Moonraker policykit rules: {e.stderr.decode()}"
            )
            Logger.print_error(log)

    def __get_instances_to_remove(self) -> List[Moonraker] | None:
        start_index = 1
        curr_instances: List[Moonraker] = self.moonraker_list
        instance_count = len(curr_instances)

        options = [str(i + start_index) for i in range(instance_count)]
        options.extend(["a", "b"])
        instance_map = {
            options[i]: self.moonraker_list[i] for i in range(instance_count)
        }

        print_instance_overview(
            self.moonraker_list,
            start_index=start_index,
            show_index=True,
            show_select_all=True,
        )
        selection = get_selection_input("Select Moonraker instance to remove", options)

        if selection == "b":
            return None
        elif selection == "a":
            return copy(self.moonraker_list)

        return [instance_map[selection]]

    def __remove_instances(
        self,
        instance_list: List[Moonraker] | None,
    ) -> None:
        if not instance_list:
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)
            self.__delete_env_file(instance)

        self.__refresh_state()

    def __delete_env_file(self, instance: Moonraker):
        Logger.print_status(f"Remove '{instance.env_file}'")
        if not instance.env_file.exists():
            msg = f"Env file in {instance.base.sysd_dir} not found. Skipped ..."
            Logger.print_info(msg)
            return
        run_remove_routines(instance.env_file)
