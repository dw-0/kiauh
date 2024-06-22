# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import shutil
import textwrap
from pathlib import Path
from typing import Optional, Tuple, Type

from components.klipper import KLIPPER_DIR
from components.klipper.klipper import Klipper
from components.moonraker import MOONRAKER_DIR
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings
from utils.constants import COLOR_CYAN, COLOR_GREEN, RESET_FORMAT
from utils.git_utils import git_clone_wrapper
from utils.input_utils import get_confirm, get_string_input
from utils.logger import DialogType, Logger


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class SettingsMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu
        self.klipper_repo = None
        self.moonraker_repo = None
        self.mainsail_unstable = None
        self.fluidd_unstable = None
        self.auto_backups_enabled = None
        self._load_settings()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.set_klipper_repo, menu=True),
            "2": Option(method=self.set_moonraker_repo, menu=True),
            "3": Option(method=self.toggle_mainsail_release, menu=True),
            "4": Option(method=self.toggle_fluidd_release, menu=False),
            "5": Option(method=self.toggle_backup_before_update, menu=False),
        }

    def print_menu(self):
        header = " [ KIAUH Settings ] "
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_GREEN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.mainsail_unstable else unchecked
        o2 = checked if self.fluidd_unstable else unchecked
        o3 = checked if self.auto_backups_enabled else unchecked
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            ║ Klipper source repository:                            ║
            ║   ● {self.klipper_repo:<67} ║
            ║                                                       ║
            ║ Moonraker source repository:                          ║
            ║   ● {self.moonraker_repo:<67} ║
            ║                                                       ║
            ║ Install unstable Webinterface releases:               ║
            ║  {o1} Mainsail                                         ║
            ║  {o2} Fluidd                                           ║
            ║                                                       ║
            ║ Auto-Backup:                                          ║
            ║  {o3} Automatic backup before update                   ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Set Klipper source repository                      ║
            ║ 2) Set Moonraker source repository                    ║
            ║                                                       ║
            ║ 3) Toggle unstable Mainsail releases                  ║
            ║ 4) Toggle unstable Fluidd releases                    ║
            ║                                                       ║
            ║ 5) Toggle automatic backups before updates            ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def _load_settings(self):
        self.settings = KiauhSettings()

        self._format_repo_str("klipper")
        self._format_repo_str("moonraker")

        self.auto_backups_enabled = self.settings.kiauh.backup_before_update
        self.mainsail_unstable = self.settings.mainsail.unstable_releases
        self.fluidd_unstable = self.settings.fluidd.unstable_releases

    def _format_repo_str(self, repo_name: str) -> None:
        repo = self.settings.get(repo_name, "repo_url")
        repo = f"{'/'.join(repo.rsplit('/', 2)[-2:])}"
        branch = self.settings.get(repo_name, "branch")
        branch = f"({COLOR_CYAN}@ {branch}{RESET_FORMAT})"
        setattr(self, f"{repo_name}_repo", f"{COLOR_CYAN}{repo}{RESET_FORMAT} {branch}")

    def _gather_input(self) -> Tuple[str, str]:
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "There is no input validation in place! Make sure your"
                " input is valid and has no typos! For any change to"
                " take effect, the repository must be cloned again. "
                "Make sure you don't have any ongoing prints running, "
                "as the services will be restarted!"
            ],
        )
        repo = get_string_input(
            "Enter new repository URL",
            allow_special_chars=True,
        )
        branch = get_string_input(
            "Enter new branch name",
            allow_special_chars=True,
        )

        return repo, branch

    def _set_repo(self, repo_name: str):
        repo_url, branch = self._gather_input()
        display_name = repo_name.capitalize()
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                f"New {display_name} repository URL:",
                f"● {repo_url}",
                f"New {display_name} repository branch:",
                f"● {branch}",
            ],
            end="",
        )

        if get_confirm("Apply changes?", allow_go_back=True):
            self.settings.set(repo_name, "repo_url", repo_url)
            self.settings.set(repo_name, "branch", branch)
            self.settings.save()
            self._load_settings()
            Logger.print_ok("Changes saved!")
        else:
            Logger.print_info(
                f"Skipping change of {display_name} source repository  ..."
            )
            return

        Logger.print_status(f"Switching to {display_name}'s new source repository ...")
        self._switch_repo(repo_name)
        Logger.print_ok(f"Switched to {repo_url} at branch {branch}!")

    def _switch_repo(self, name: str) -> None:
        target_dir: Path
        if name == "klipper":
            target_dir = KLIPPER_DIR
            _type = Klipper
        elif name == "moonraker":
            target_dir = MOONRAKER_DIR
            _type = Moonraker
        else:
            Logger.print_error("Invalid repository name!")
            return

        if target_dir.exists():
            shutil.rmtree(target_dir)

        im = InstanceManager(_type)
        im.stop_all_instance()

        repo = self.settings.get(name, "repo_url")
        branch = self.settings.get(name, "branch")
        git_clone_wrapper(repo, target_dir, branch)

        im.start_all_instance()

    def set_klipper_repo(self, **kwargs):
        self._set_repo("klipper")

    def set_moonraker_repo(self, **kwargs):
        self._set_repo("moonraker")

    def toggle_mainsail_release(self, **kwargs):
        self.mainsail_unstable = not self.mainsail_unstable
        self.settings.mainsail.unstable_releases = self.mainsail_unstable
        self.settings.save()

    def toggle_fluidd_release(self, **kwargs):
        self.fluidd_unstable = not self.fluidd_unstable
        self.settings.fluidd.unstable_releases = self.fluidd_unstable
        self.settings.save()

    def toggle_backup_before_update(self, **kwargs):
        self.auto_backups_enabled = not self.auto_backups_enabled
        self.settings.kiauh.backup_before_update = self.auto_backups_enabled
        self.settings.save()
