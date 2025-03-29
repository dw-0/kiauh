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
from typing import Dict, List, Tuple

from components.klipper import (
    EXIT_KLIPPER_SETUP,
    KLIPPER_DIR,
    KLIPPER_ENV_DIR,
    KLIPPER_REPO_URL,
    KLIPPER_REQ_FILE,
)
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import (
    print_instance_overview,
    print_select_custom_name_dialog,
)
from components.klipper.klipper_utils import (
    assign_custom_name,
    backup_klipper_dir,
    check_user_groups,
    create_example_printer_cfg,
    get_install_count,
    handle_disruptive_system_packages,
    install_klipper_packages,
)
from components.klipper.services.klipper_instance_service import KlipperInstanceService
from components.moonraker.moonraker import Moonraker
from components.moonraker.services.moonraker_instance_service import (
    MoonrakerInstanceService,
)
from components.webui_client.client_utils import (
    get_existing_clients,
)
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.message_service import Message, MessageService
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color
from utils.fs_utils import run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm, get_selection_input
from utils.sys_utils import (
    cmd_sysctl_manage,
    create_python_venv,
    install_python_requirements,
    unit_file_exists,
)


# noinspection PyMethodMayBeStatic
class KlipperSetupService:
    __cls_instance = None

    kisvc: KlipperInstanceService
    misvc: MoonrakerInstanceService
    msgsvc = MessageService

    settings: KiauhSettings
    klipper_list: List[Klipper]
    moonraker_list: List[Moonraker]

    def __new__(cls) -> "KlipperSetupService":
        if cls.__cls_instance is None:
            cls.__cls_instance = super(KlipperSetupService, cls).__new__(cls)
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

        Logger.print_status("Installing Klipper ...")

        match_moonraker: bool = False

        # if there are more moonraker instances than klipper instances, ask the user to
        # match the klipper instance count to the count of moonraker instances with the same suffix
        if len(self.moonraker_list) > len(self.klipper_list):
            is_confirmed = self.__display_moonraker_info()
            if not is_confirmed:
                Logger.print_status(EXIT_KLIPPER_SETUP)
                return
            match_moonraker = True

        install_count, name_dict = self.__get_install_count_and_name_dict()

        if install_count == 0:
            Logger.print_status(EXIT_KLIPPER_SETUP)
            return

        is_multi_install = install_count > 1 or (
            len(name_dict) >= 1 and install_count >= 1
        )
        if not name_dict and install_count == 1:
            name_dict = {0: ""}
        elif is_multi_install and not match_moonraker:
            custom_names = self.__use_custom_names_or_go_back()
            if custom_names is None:
                Logger.print_status(EXIT_KLIPPER_SETUP)
                return

            self.__handle_instance_names(install_count, name_dict, custom_names)

        create_example_cfg = get_confirm("Create example printer.cfg?")
        # run the actual installation
        try:
            self.__run_setup(name_dict, create_example_cfg)
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Klipper installation failed!")
            return

    def update(self) -> None:
        Logger.print_dialog(
            DialogType.WARNING,
            [
                "Do NOT continue if there are ongoing prints running!",
                "All Klipper instances will be restarted during the update process and "
                "ongoing prints WILL FAIL.",
            ],
        )

        if not get_confirm("Update Klipper now?"):
            return

        self.__refresh_state()

        if self.settings.kiauh.backup_before_update:
            backup_klipper_dir()

        InstanceManager.stop_all(self.klipper_list)
        git_pull_wrapper(KLIPPER_DIR)
        install_klipper_packages()
        install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
        InstanceManager.start_all(self.klipper_list)

    def remove(
        self,
        remove_service: bool,
        remove_dir: bool,
        remove_env: bool,
    ) -> None:
        self.__refresh_state()

        completion_msg = Message(
            title="Klipper Removal Process completed",
            color=Color.GREEN,
        )

        if remove_service:
            Logger.print_status("Removing Klipper instances ...")
            if self.klipper_list:
                instances_to_remove = self.__get_instances_to_remove()
                self.__remove_instances(instances_to_remove)
                if instances_to_remove:
                    instance_names = [
                        i.service_file_path.stem for i in instances_to_remove
                    ]
                    txt = f"● Klipper instances removed: {', '.join(instance_names)}"
                    completion_msg.text.append(txt)
            else:
                Logger.print_info("No Klipper Services installed! Skipped ...")

        if (remove_dir or remove_env) and unit_file_exists("klipper", suffix="service"):
            completion_msg.text = [
                "Some Klipper services are still installed:",
                f"● '{KLIPPER_DIR}' was not removed, even though selected for removal.",
                f"● '{KLIPPER_ENV_DIR}' was not removed, even though selected for removal.",
            ]
        else:
            if remove_dir:
                Logger.print_status("Removing Klipper local repository ...")
                if run_remove_routines(KLIPPER_DIR):
                    completion_msg.text.append("● Klipper local repository removed")
            if remove_env:
                Logger.print_status("Removing Klipper Python environment ...")
                if run_remove_routines(KLIPPER_ENV_DIR):
                    completion_msg.text.append("● Klipper Python environment removed")

        if completion_msg.text:
            completion_msg.text.insert(0, "The following actions were performed:")
        else:
            completion_msg.color = Color.YELLOW
            completion_msg.centered = True
            completion_msg.text = ["Nothing to remove."]

        self.msgsvc.set_message(completion_msg)

    def __get_install_count_and_name_dict(self) -> Tuple[int, Dict[int, str]]:
        install_count: int | None
        if len(self.moonraker_list) > len(self.klipper_list):
            install_count = len(self.moonraker_list)
            name_dict = {
                i: moonraker.suffix for i, moonraker in enumerate(self.moonraker_list)
            }
        else:
            install_count = get_install_count()
            name_dict = {
                i: klipper.suffix for i, klipper in enumerate(self.klipper_list)
            }

            if install_count is None:
                Logger.print_status(EXIT_KLIPPER_SETUP)
                return 0, {}

        return install_count, name_dict

    def __run_setup(self, name_dict: Dict[int, str], create_example_cfg: bool) -> None:
        if not self.klipper_list:
            self.__install_deps()

        for i in name_dict:
            # skip this iteration if there is already an instance with the name
            if name_dict[i] in [n.suffix for n in self.klipper_list]:
                continue

            instance = Klipper(suffix=name_dict[i])
            instance.create()
            InstanceManager.enable(instance)

            if create_example_cfg:
                # if a client-config is installed, include it in the new example cfg
                clients = get_existing_clients()
                create_example_printer_cfg(instance, clients)

            InstanceManager.start(instance)

        cmd_sysctl_manage("daemon-reload")

        # step 4: check/handle conflicting packages/services
        handle_disruptive_system_packages()

        # step 5: check for required group membership
        check_user_groups()

    def __install_deps(self) -> None:
        default_repo = (KLIPPER_REPO_URL, "master")
        repo = self.settings.klipper.repositories
        # pull the first repo defined in kiauh.cfg or fallback to the official Klipper repo
        repo, branch = (repo[0].url, repo[0].branch) if repo else default_repo
        git_clone_wrapper(repo, KLIPPER_DIR, branch)

        try:
            install_klipper_packages()
            if create_python_venv(KLIPPER_ENV_DIR):
                install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
        except Exception:
            Logger.print_error("Error during installation of Klipper requirements!")
            raise

    def __display_moonraker_info(self) -> bool:
        # todo: only show the klipper instances that are not already installed
        Logger.print_dialog(
            DialogType.INFO,
            [
                "Existing Moonraker instances detected:",
                *[f"● {m.service_file_path.stem}" for m in self.moonraker_list],
                "\n\n",
                "The following Klipper instances will be installed:",
                *[f"● klipper-{m.suffix}" for m in self.moonraker_list],
            ],
        )
        _input: bool = get_confirm("Proceed with installation?")
        return _input

    def __handle_instance_names(
        self, install_count: int, name_dict: Dict[int, str], custom_names: bool
    ) -> None:
        for i in range(install_count):  # 3
            key: int = len(name_dict.keys()) + 1
            if custom_names:
                assign_custom_name(key, name_dict)
            else:
                name_dict[key] = str(len(name_dict) + 1)

    def __use_custom_names_or_go_back(self) -> bool | None:
        print_select_custom_name_dialog()
        _input: bool | None = get_confirm(
            "Assign custom names?",
            False,
            allow_go_back=True,
        )
        return _input

    def __get_instances_to_remove(self) -> List[Klipper] | None:
        start_index = 1
        curr_instances: List[Klipper] = self.klipper_list
        instance_count = len(curr_instances)

        options = [str(i + start_index) for i in range(instance_count)]
        options.extend(["a", "b"])
        instance_map = {options[i]: self.klipper_list[i] for i in range(instance_count)}

        print_instance_overview(
            self.klipper_list,
            start_index=start_index,
            show_index=True,
            show_select_all=True,
        )
        selection = get_selection_input("Select Klipper instance to remove", options)

        if selection == "b":
            return None
        elif selection == "a":
            return copy(self.klipper_list)

        return [instance_map[selection]]

    def __remove_instances(
        self,
        instance_list: List[Klipper] | None,
    ) -> None:
        if not instance_list:
            return

        for instance in instance_list:
            Logger.print_status(
                f"Removing instance {instance.service_file_path.stem} ..."
            )
            InstanceManager.remove(instance)
            self.__delete_klipper_env_file(instance)

        self.__refresh_state()

    def __delete_klipper_env_file(self, instance: Klipper):
        Logger.print_status(f"Remove '{instance.env_file}'")
        if not instance.env_file.exists():
            msg = f"Env file in {instance.base.sysd_dir} not found. Skipped ..."
            Logger.print_info(msg)
            return
        run_remove_routines(instance.env_file)
