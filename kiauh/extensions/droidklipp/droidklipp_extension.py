# ======================================================================= #
#  Copyright (C) 2026 Cody Dixon                                         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from subprocess import CalledProcessError, run

from components.klipperscreen import KLIPPERSCREEN_DIR, KLIPPERSCREEN_ENV_DIR
from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.droidklipp import (
    DROIDKLIPP_APK_URL,
    DROIDKLIPP_DEPLOYED_MONITOR,
    DROIDKLIPP_DIR,
    DROIDKLIPP_INSTALL_SCRIPT,
    DROIDKLIPP_MONITOR_FILE,
    DROIDKLIPP_REPO,
    DROIDKLIPP_REQUIRED_PACKAGES,
    DROIDKLIPP_SERVICE_NAME,
    DROIDKLIPP_UNINSTALL_SCRIPT,
)
from utils.common import check_install_dependencies
from utils.fs_utils import check_file_exist, run_remove_routines
from utils.git_utils import git_clone_wrapper, git_pull_wrapper
from utils.input_utils import get_confirm
from utils.sys_utils import cmd_sysctl_service


# noinspection PyMethodMayBeStatic
class DroidKlippExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing DroidKlipp ...")

        if not self._klipperscreen_exists():
            Logger.print_dialog(
                DialogType.WARNING,
                [
                    "No KIAUH v6 KlipperScreen installation found!",
                    "DroidKlipp expects KlipperScreen at:",
                    f"● {KLIPPERSCREEN_DIR.joinpath('screen.py')}",
                    f"● {KLIPPERSCREEN_ENV_DIR.joinpath('bin/python')}",
                    "Install KlipperScreen first, then run this installer again.",
                ],
            )
            return

        Logger.print_dialog(
            DialogType.INFO,
            [
                "DroidKlipp requires the Android APK to be installed on your Android device:",
                DROIDKLIPP_APK_URL,
                "\n\n",
                "The installer will configure ADB forwarding, udev rules, the DroidKlipp monitor, and WiFi fallback.",
            ],
        )

        if not get_confirm(
            "Continue DroidKlipp installation?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting DroidKlipp installation ...")
            return

        try:
            check_install_dependencies(DROIDKLIPP_REQUIRED_PACKAGES)
            git_clone_wrapper(DROIDKLIPP_REPO, DROIDKLIPP_DIR)
            run(["chmod", "+x", DROIDKLIPP_INSTALL_SCRIPT], check=True)
            run([DROIDKLIPP_INSTALL_SCRIPT], check=True)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["DroidKlipp successfully installed!"],
                center_content=True,
            )
        except CalledProcessError as e:
            Logger.print_error(f"Error during DroidKlipp installation:\n{e}")
        except Exception as e:
            Logger.print_error(f"Error during DroidKlipp installation:\n{e}")

    def update_extension(self, **kwargs) -> None:
        Logger.print_status("Updating DroidKlipp ...")

        if not check_file_exist(DROIDKLIPP_DIR):
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        try:
            cmd_sysctl_service(DROIDKLIPP_SERVICE_NAME, "stop")

            git_pull_wrapper(DROIDKLIPP_DIR)

            if check_file_exist(DROIDKLIPP_MONITOR_FILE):
                run(
                    [
                        "install",
                        "-m",
                        "755",
                        str(DROIDKLIPP_MONITOR_FILE),
                        str(DROIDKLIPP_DEPLOYED_MONITOR),
                    ],
                    check=True,
                )

            cmd_sysctl_service(DROIDKLIPP_SERVICE_NAME, "start")

            Logger.print_dialog(
                DialogType.SUCCESS,
                ["DroidKlipp successfully updated!"],
                center_content=True,
            )
        except CalledProcessError as e:
            Logger.print_error(f"Error during DroidKlipp update:\n{e}")
            cmd_sysctl_service(DROIDKLIPP_SERVICE_NAME, "start")
        except Exception as e:
            Logger.print_error(f"Error during DroidKlipp update:\n{e}")
            cmd_sysctl_service(DROIDKLIPP_SERVICE_NAME, "start")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing DroidKlipp ...")

        if not check_file_exist(DROIDKLIPP_DIR):
            Logger.print_info("Extension does not seem to be installed! Skipping ...")
            return

        if not get_confirm(
            "Do you really want to uninstall DroidKlipp?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("Exiting DroidKlipp uninstallation ...")
            return

        try:
            if check_file_exist(DROIDKLIPP_UNINSTALL_SCRIPT):
                run(["chmod", "+x", DROIDKLIPP_UNINSTALL_SCRIPT], check=True)
                run([DROIDKLIPP_UNINSTALL_SCRIPT], check=True)
            run_remove_routines(DROIDKLIPP_DIR)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["DroidKlipp successfully removed!"],
                center_content=True,
            )
        except CalledProcessError as e:
            Logger.print_error(f"Error during DroidKlipp removal:\n{e}")
        except Exception as e:
            Logger.print_error(f"Error during DroidKlipp removal:\n{e}")

    def _klipperscreen_exists(self) -> bool:
        return bool(
            check_file_exist(KLIPPERSCREEN_DIR.joinpath("screen.py"))
            and check_file_exist(KLIPPERSCREEN_ENV_DIR.joinpath("bin/python"))
        )
