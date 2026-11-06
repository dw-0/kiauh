# ======================================================================= #
#  Copyright (C) 2026 umeiko                                               #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from subprocess import CalledProcessError, run
from tempfile import TemporaryDirectory

from core.logger import DialogType, Logger
from extensions.base_extension import BaseExtension
from extensions.klipperscreen_esp import (
    KLIPPERSCREEN_ESP_BACKEND_DROP_IN,
    KLIPPERSCREEN_ESP_INSTALL_DIR,
    KLIPPERSCREEN_ESP_MIRRORS,
    KLIPPERSCREEN_ESP_PACKAGE_ARCHES,
    KLIPPERSCREEN_ESP_RELEASE_BASE,
    KLIPPERSCREEN_ESP_SERVICE_NAME,
    KLIPPERSCREEN_ESP_UNINSTALL_SCRIPT,
)
from utils.fs_utils import check_file_exist
from utils.input_utils import get_confirm


# noinspection PyMethodMayBeStatic
class KlipperScreenEspExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("Installing KlipperScreen-esp ...")
        if not get_confirm(
            "Install the lightweight multi-printer KlipperScreen-esp display?",
            default_choice=True,
            allow_go_back=True,
        ):
            return

        service = get_confirm(
            "Install as a dedicated display service instead of a desktop app?",
            default_choice=True,
            allow_go_back=True,
        )
        if service is None:
            return

        x11 = False
        if service:
            backend = get_confirm(
                "Use X11 instead of the recommended Wayland backend?",
                default_choice=False,
                allow_go_back=True,
            )
            if backend is None:
                return
            x11 = backend

        env = {
            "SERVICE": "y" if service else "n",
            "KR_BACKEND": "X" if x11 else "W",
        }
        try:
            if service:
                self._prepare_service()
            self._install_release(env)
            if service:
                self._finish_service()
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["KlipperScreen-esp successfully installed!"],
                center_content=True,
            )
        except (CalledProcessError, OSError) as e:
            Logger.print_error(f"Error during KlipperScreen-esp installation:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("Removing KlipperScreen-esp ...")
        if not check_file_exist(KLIPPERSCREEN_ESP_INSTALL_DIR):
            Logger.print_info(
                "KlipperScreen-esp does not seem to be installed! Skipping ..."
            )
            return
        if not get_confirm(
            "Do you really want to uninstall KlipperScreen-esp?",
            default_choice=True,
            allow_go_back=True,
        ):
            return

        try:
            self._prepare_service()
            self._run_upstream(KLIPPERSCREEN_ESP_UNINSTALL_SCRIPT)
            self._privileged(["systemctl", "daemon-reload"], True)
            Logger.print_dialog(
                DialogType.SUCCESS,
                ["KlipperScreen-esp successfully removed!"],
                center_content=True,
            )
        except (CalledProcessError, OSError) as e:
            Logger.print_error(f"Error during KlipperScreen-esp removal:\n{e}")

    def _privileged(self, args: list[str], check: bool) -> None:
        use_askpass = os.environ.get("SUDO_ASKPASS") and not sys.stdin.isatty()
        run(["sudo"] + (["-A"] if use_askpass else []) + args, check=check)

    def _prepare_service(self) -> None:
        self._privileged(["systemctl", "stop", KLIPPERSCREEN_ESP_SERVICE_NAME], False)

    def _finish_service(self) -> None:
        self._privileged(["rm", "-f", KLIPPERSCREEN_ESP_BACKEND_DROP_IN], True)
        self._privileged(["systemctl", "daemon-reload"], True)
        self._privileged(["systemctl", "restart", KLIPPERSCREEN_ESP_SERVICE_NAME], True)

    def _install_release(self, extra_env: dict[str, str]) -> None:
        machine = platform.machine().lower()
        package_arch = KLIPPERSCREEN_ESP_PACKAGE_ARCHES.get(machine)
        if package_arch is None:
            raise OSError(f"Unsupported architecture: {machine}")

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root.joinpath("release.tar.gz")
            url = (
                f"{KLIPPERSCREEN_ESP_RELEASE_BASE}/desktop-linux-{package_arch}.tar.gz"
            )
            self._download(url, archive)
            run(["tar", "-xzf", archive.as_posix(), "-C", tmp], check=True)
            self._run_script(root.joinpath("install.sh"), extra_env)

    def _run_upstream(self, url: str) -> None:
        with TemporaryDirectory() as tmp:
            script = Path(tmp).joinpath("upstream.sh")
            self._download(url, script)
            self._run_script(script)

    def _download(self, url: str, target: Path) -> None:
        candidates = [url] + [f"{prefix}{url}" for prefix in KLIPPERSCREEN_ESP_MIRRORS]
        for candidate in candidates:
            result = run(
                [
                    "curl",
                    "-fSL",
                    "--connect-timeout",
                    "15",
                    "--max-time",
                    "60",
                    "--retry",
                    "2",
                    candidate,
                    "-o",
                    target.as_posix(),
                ],
                check=False,
            )
            if result.returncode == 0 and target.exists():
                return
            if target.exists():
                target.unlink()
        raise OSError(f"Unable to download {url} directly or through mirrors")

    def _run_script(
        self, script: Path, extra_env: dict[str, str] | None = None
    ) -> None:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        run(["bash", script.as_posix()], env=env, check=True)
