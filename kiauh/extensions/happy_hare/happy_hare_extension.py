# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from subprocess import CalledProcessError

from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.happy_hare import (
    HAPPY_HARE_DIR,
    HAPPY_HARE_INSTALL_SCRIPT,
    HAPPY_HARE_REPO,
)
from utils.fs_utils import check_file_exist, run, run_remove_routines
from utils.git_utils import GitException, git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm


# noinspection PyMethodMayBeStatic
class HappyHareExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing Happy Hare ...")

        if not self._is_supported_version():
            return

        try:
            if check_file_exist(HAPPY_HARE_DIR.joinpath(".git")):
                git_pull_wrapper(HAPPY_HARE_DIR)
            elif check_file_exist(HAPPY_HARE_DIR):
                Logger.print_warn(
                    f"'{HAPPY_HARE_DIR}' exists but is not a Git checkout. "
                    "It was left untouched to preserve any .mmu_config files."
                )
                return
            else:
                git_clone_wrapper(HAPPY_HARE_REPO, HAPPY_HARE_DIR)
            if not self._is_supported_version():
                return
            self._run_installer("-z", "-f", "--last")
        except (GitException, CalledProcessError, OSError) as e:
            Logger.print_error(f"Error during Happy Hare installation:\n{e}")
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            ["Happy Hare links installed successfully!"],
            center_content=True,
        )

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating Happy Hare ...")

        if not self._is_supported_version():
            return

        if not check_file_exist(HAPPY_HARE_DIR.joinpath(".git")):
            Logger.print_info(
                "Happy Hare does not seem to be installed. Use Install first."
            )
            return

        try:
            git_pull_wrapper(HAPPY_HARE_DIR)
            if not self._is_supported_version():
                return
            self._run_installer("-z", "-f", "--last")
        except (CalledProcessError, OSError) as e:
            Logger.print_error(f"Error during Happy Hare update:\n{e}")
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            ["Happy Hare updated successfully!"],
            center_content=True,
        )

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing Happy Hare ...")

        if not self._is_supported_version():
            return

        if not check_file_exist(HAPPY_HARE_INSTALL_SCRIPT):
            Logger.print_warn(
                "Happy Hare's installer was not found, so it cannot be safely "
                "uninstalled. The Happy Hare directory was left untouched."
            )
            return

        if not get_confirm(
            "Uninstall Happy Hare and remove its repository?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Removal aborted.")
            return

        try:
            self._run_installer("--yes", "-z", "-d")
        except (CalledProcessError, OSError) as e:
            Logger.print_error(f"Error during Happy Hare removal:\n{e}")
            return

        if not run_remove_routines(HAPPY_HARE_DIR):
            Logger.print_error(
                "Happy Hare was uninstalled, but its repository could not be removed."
            )
            return

        Logger.print_dialog(
            DialogType.SUCCESS,
            ["Happy Hare successfully removed!"],
            center_content=True,
        )

    def _run_installer(self, *options: str) -> None:
        run(
            [HAPPY_HARE_INSTALL_SCRIPT.as_posix(), *options],
            cwd=HAPPY_HARE_DIR,
            check=True,
        )

    def _is_supported_version(self) -> bool:
        if not check_file_exist(HAPPY_HARE_INSTALL_SCRIPT):
            return True

        try:
            supported = "Happy Hare v4" in HAPPY_HARE_INSTALL_SCRIPT.read_text()
        except OSError:
            supported = False

        if not supported:
            Logger.print_error("Kiauh only supports Happy Hare version 4")

        return supported
