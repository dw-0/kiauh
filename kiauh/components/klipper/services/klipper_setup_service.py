# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import traceback
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
from core.i18n import _tr
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

    def _refresh_state(self) -> None:
        self.kisvc.load_instances()
        self.klipper_list = self.kisvc.get_all_instances()

        self.misvc.load_instances()
        self.moonraker_list = self.misvc.get_all_instances()

    def install(
        self,
        count: int | None = None,
        custom_names: Dict[int, str] | None = None,
        create_example_cfg: bool | None = None,
        match_moonraker: bool = False,
        interactive: bool = True,
    ) -> bool:
        """Install Klipper.

        When called without arguments from the TUI, all choices are prompted
        interactively. The CLI passes explicit values and ``interactive=False``.

        Returns ``True`` on success and ``False`` when installation cannot proceed.
        """
        self._refresh_state()

        Logger.print_status(_tr("Installing Klipper ..."))

        name_dict: Dict[int, str] = {}

        if custom_names is not None:
            name_dict = custom_names
        elif match_moonraker and len(self.moonraker_list) > len(self.klipper_list):
            if interactive:
                if not self._display_moonraker_info():
                    Logger.print_status(EXIT_KLIPPER_SETUP())
                    return True
            name_dict = {
                i: moonraker.suffix for i, moonraker in enumerate(self.moonraker_list)
            }
        elif count is not None:
            name_dict = {i: "" for i in range(count)}
        elif interactive:
            install_count, name_dict = self.__get_install_count_and_name_dict()

            if install_count == 0:
                Logger.print_status(EXIT_KLIPPER_SETUP())
                return True

            is_multi_install = install_count > 1 or (
                len(name_dict) >= 1 and install_count >= 1
            )
            if not name_dict and install_count == 1:
                name_dict = {0: ""}
            elif is_multi_install and not self.__count_from_moonraker_match(
                install_count, name_dict
            ):
                use_custom_names = self.__use_custom_names_or_go_back()
                if use_custom_names is None:
                    Logger.print_status(EXIT_KLIPPER_SETUP())
                    return True

                self.__handle_instance_names(install_count, name_dict, use_custom_names)
        else:
            name_dict = {0: ""}

        if not name_dict:
            Logger.print_status(EXIT_KLIPPER_SETUP())
            return True

        if create_example_cfg is None:
            create_example_cfg = (
                get_confirm(_tr("Create example printer.cfg?")) if interactive else False
            )

        try:
            self.__run_setup(name_dict, create_example_cfg, interactive=interactive)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Klipper installation failed!"))
            return False

        return True

    def update(self, interactive: bool = True) -> bool:
        """Update Klipper.

        When called from the TUI, a warning and confirmation are shown. The CLI
        passes ``interactive=False`` to run silently.

        Returns ``True`` on success and ``False`` if the update could not be completed.
        """
        if interactive:
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    _tr("Do NOT continue if there are ongoing prints running!"),
                    _tr("All Klipper instances will be restarted during the update process and ongoing prints WILL FAIL."),
                ],
            )

            if not get_confirm(_tr("Update Klipper now?")):
                return False

        self._refresh_state()

        try:
            if self.settings.kiauh.backup_before_update:
                backup_klipper_dir()

            InstanceManager.stop_all(self.klipper_list)
            git_pull_wrapper(KLIPPER_DIR)
            install_klipper_packages()
            install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
            InstanceManager.start_all(self.klipper_list)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Error while updating Klipper!"))
            return False

        return True

    def remove(
        self,
        remove_service: bool,
        remove_dir: bool,
        remove_env: bool,
        *,
        remove_all: bool = False,
        instance_suffixes: List[str] | None = None,
        interactive: bool = True,
    ) -> bool:
        """Remove Klipper.

        When called from the TUI, the user selects instances interactively. In
        headless mode (``interactive=False``) the caller MUST express explicit
        intent: pass ``remove_all=True`` to wipe every instance or
        ``instance_suffixes=[...]`` to remove a named subset. Without explicit
        intent the service refuses and removes nothing so a CLI user can never
        accidentally destroy every Klipper instance on the machine.

        Returns ``True`` on success and ``False`` if removal could not be completed.
        """
        self._refresh_state()

        try:
            if interactive:
                completion_msg = Message(
                    title=_tr("Klipper Removal Process completed"),
                    color=Color.GREEN,
                )

                if remove_service:
                    Logger.print_status(_tr("Removing Klipper instances ..."))
                    if self.klipper_list:
                        instances_to_remove = self._get_instances_to_remove()
                        self.__remove_instances(instances_to_remove)
                        if instances_to_remove:
                            instance_names = [
                                i.service_file_path.stem for i in instances_to_remove
                            ]
                            txt = _tr("● Klipper instances removed: {}").format(
                                ", ".join(instance_names)
                            )
                            completion_msg.text.append(txt)
                    else:
                        Logger.print_info(
                            _tr("No Klipper Services installed! Skipped ...")
                        )

                if (remove_dir or remove_env) and unit_file_exists(
                    "klipper", suffix="service"
                ):
                    completion_msg.text = [
                        _tr("Some Klipper services are still installed:"),
                        _tr("● '{}' was not removed, even though selected for removal.").format(
                            KLIPPER_DIR
                        ),
                        _tr("● '{}' was not removed, even though selected for removal.").format(
                            KLIPPER_ENV_DIR
                        ),
                    ]
                else:
                    if remove_dir:
                        Logger.print_status(_tr("Removing Klipper local repository ..."))
                        if run_remove_routines(KLIPPER_DIR):
                            completion_msg.text.append(
                                _tr("● Klipper local repository removed")
                            )
                    if remove_env:
                        Logger.print_status(_tr("Removing Klipper Python environment ..."))
                        if run_remove_routines(KLIPPER_ENV_DIR):
                            completion_msg.text.append(
                                _tr("● Klipper Python environment removed")
                            )

                if completion_msg.text:
                    completion_msg.text.insert(
                        0, _tr("The following actions were performed:")
                    )
                else:
                    completion_msg.color = Color.YELLOW
                    completion_msg.centered = True
                    completion_msg.text = [_tr("Nothing to remove.")]

                self.msgsvc.set_message(completion_msg)
            else:
                if remove_service and self.klipper_list:
                    selected = self._select_instances_for_headless_removal(
                        remove_all, instance_suffixes
                    )
                    if selected is None:
                        Logger.print_error(
                            _tr("Refusing to remove Klipper instances: no explicit intent. Pass remove_all=True or instance_suffixes.")
                        )
                        return False
                    self.__remove_instances(selected)

                if (remove_dir or remove_env) and unit_file_exists(
                    "klipper", suffix="service"
                ):
                    Logger.print_info(
                        _tr("Klipper services still installed; skipping repository/env removal.")
                    )
                    return True

                if remove_dir:
                    run_remove_routines(KLIPPER_DIR)
                if remove_env:
                    run_remove_routines(KLIPPER_ENV_DIR)
        except Exception:
            Logger.print_error(traceback.format_exc())
            Logger.print_error(_tr("Error while removing Klipper!"))
            return False

        return True

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
                Logger.print_status(EXIT_KLIPPER_SETUP())
                return 0, {}

        return install_count, name_dict

    def __run_setup(
        self,
        name_dict: Dict[int, str],
        create_example_cfg: bool,
        interactive: bool = True,
    ) -> None:
        if not self.klipper_list:
            # Only create a fresh venv when none exists; existing venvs are
            # preserved in both TUI and CLI modes.
            self.__install_deps(interactive=interactive)

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
        check_user_groups(interactive=interactive)

    def __install_deps(self, interactive: bool = True) -> None:
        default_repo = (KLIPPER_REPO_URL, "master")
        repo = self.settings.klipper.repositories
        # pull the first repo defined in kiauh.cfg or fallback to the official Klipper repo
        repo, branch = (repo[0].url, repo[0].branch) if repo else default_repo
        git_clone_wrapper(repo, KLIPPER_DIR, branch)

        try:
            install_klipper_packages()
            if create_python_venv(
                KLIPPER_ENV_DIR,
                force=False,
                allow_access_to_system_site_packages=False,
                use_python_binary=self.settings.klipper.use_python_binary,
                interactive=interactive,
            ):
                install_python_requirements(KLIPPER_ENV_DIR, KLIPPER_REQ_FILE)
        except Exception:
            Logger.print_error(_tr("Error during installation of Klipper requirements!"))
            raise

    def _display_moonraker_info(self) -> bool:
        # todo: only show the klipper instances that are not already installed
        Logger.print_dialog(
            DialogType.INFO,
            [
                _tr("Existing Moonraker instances detected:"),
                *[_tr("● {}").format(m.service_file_path.stem) for m in self.moonraker_list],
                "\n\n",
                _tr("The following Klipper instances will be installed:"),
                *[_tr("● klipper-{}").format(m.suffix) for m in self.moonraker_list],
            ],
        )
        _input: bool = get_confirm(_tr("Proceed with installation?"))
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

    def __count_from_moonraker_match(
        self, install_count: int, name_dict: Dict[int, str]
    ) -> bool:
        """Return True when the count/names came from matching Moonraker instances."""
        if len(self.moonraker_list) <= len(self.klipper_list):
            return False
        if install_count != len(self.moonraker_list):
            return False
        expected = [m.suffix for m in self.moonraker_list]
        return list(name_dict.values()) == expected

    def __use_custom_names_or_go_back(self) -> bool | None:
        print_select_custom_name_dialog()
        _input: bool | None = get_confirm(
            _tr("Assign custom names?"),
            False,
            allow_go_back=True,
        )
        return _input

    def _get_instances_to_remove(self) -> List[Klipper] | None:
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
        selection = get_selection_input(_tr("Select Klipper instance to remove"), options)

        if selection == "b":
            return None
        elif selection == "a":
            return copy(self.klipper_list)

        return [instance_map[selection]]

    def _select_instances_for_headless_removal(
        self,
        remove_all: bool,
        instance_suffixes: List[str] | None,
    ) -> List[Klipper] | None:
        """Resolve which instances to remove in headless mode.

        Returns the list of instances to remove, or ``None`` when the caller did
        not express explicit intent (no ``remove_all`` and no ``instance_suffixes``).
        A ``None`` return is the "refuse to wipe everything" signal the CLI path
        relies on. Kept as a single-public-seam helper (no name mangling) so
        tests can patch it without brittle ``_Class__method`` access.
        """
        if remove_all:
            return list(self.klipper_list)
        if instance_suffixes:
            wanted = set(instance_suffixes)
            return [i for i in self.klipper_list if i.suffix in wanted]
        return None

    def __remove_instances(
        self,
        instance_list: List[Klipper] | None,
    ) -> None:
        if not instance_list:
            return

        for instance in instance_list:
            Logger.print_status(
                _tr("Removing instance {} ...").format(instance.service_file_path.stem)
            )
            InstanceManager.remove(instance)
            self._delete_klipper_env_file(instance)

        self._refresh_state()

    def _delete_klipper_env_file(self, instance: Klipper):
        Logger.print_status(_tr("Remove '{}'").format(instance.env_file))
        if not instance.env_file.exists():
            msg = _tr("Env file in {} not found. Skipped ...").format(
                instance.base.sysd_dir
            )
            Logger.print_info(msg)
            return
        run_remove_routines(instance.env_file)
