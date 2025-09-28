# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import Any, Callable, List, TypeVar

from components.klipper import KLIPPER_REPO_URL
from components.moonraker import MOONRAKER_REPO_URL
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from utils.input_utils import get_confirm
from utils.sys_utils import kill

from kiauh import PROJECT_ROOT

DEFAULT_CFG = PROJECT_ROOT.joinpath("default.kiauh.cfg")
CUSTOM_CFG = PROJECT_ROOT.joinpath("kiauh.cfg")

T = TypeVar("T")


class InvalidValueError(Exception):
    """Raised when a value is invalid for an option"""

    def __init__(self, section: str, option: str, value: str):
        msg = f"Invalid value '{value}' for option '{option}' in section '{section}'"
        super().__init__(msg)


@dataclass
class AppSettings:
    backup_before_update: bool | None = field(default=None)


@dataclass
class Repository:
    url: str
    branch: str


@dataclass
class KlipperSettings:
    repositories: List[Repository] | None = field(default=None)
    use_python_binary: str | None = field(default=None)


@dataclass
class MoonrakerSettings:
    optional_speedups: bool | None = field(default=None)
    repositories: List[Repository] | None = field(default=None)
    use_python_binary: str | None = field(default=None)


@dataclass
class WebUiSettings:
    port: int | None = field(default=None)
    unstable_releases: bool | None = field(default=None)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KiauhSettings:
    __instance = None
    __initialized = False

    def __new__(cls, *args, **kwargs) -> "KiauhSettings":
        if cls.__instance is None:
            cls.__instance = super(KiauhSettings, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __repr__(self) -> str:
        return (
            f"KiauhSettings(kiauh={self.kiauh}, klipper={self.klipper},"
            f" moonraker={self.moonraker}, mainsail={self.mainsail},"
            f" fluidd={self.fluidd})"
        )

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __init__(self) -> None:
        if self.__initialized:
            return
        self.__initialized = True

        self.config = SimpleConfigParser()
        self.kiauh = AppSettings()
        self.klipper = KlipperSettings()
        self.moonraker = MoonrakerSettings()
        self.mainsail = WebUiSettings()
        self.fluidd = WebUiSettings()

        self.__read_config_set_internal_state()

    # todo: refactor this, at least rename to something else!
    def get(self, section: str, option: str) -> str | int | bool:
        """
        Get a value from the settings state by providing the section and option name as
        strings. Prefer direct access to the properties, as it is usually safer!
        :param section: The section name as string.
        :param option: The option name as string.
        :return: The value of the option as string, int or bool.
        """

        try:
            section = getattr(self, section)
            value = getattr(section, option)
            return value  # type: ignore
        except AttributeError:
            raise

    def save(self) -> None:
        self.__write_internal_state_to_cfg()
        self.__read_config_set_internal_state()

    def __read_config_set_internal_state(self) -> None:
        if not CUSTOM_CFG.exists() and not DEFAULT_CFG.exists():
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "No KIAUH configuration file found! Please make sure you have at least "
                    "one of the following configuration files in KIAUH's root directory:",
                    "● default.kiauh.cfg",
                    "● kiauh.cfg",
                ],
            )
            kill()

        # copy default config to custom config if it does not exist
        if not CUSTOM_CFG.exists():
            shutil.copyfile(DEFAULT_CFG, CUSTOM_CFG)

        self.config.read_file(CUSTOM_CFG)

        # check if there are deprecated repo_url and branch options in the kiauh.cfg
        if self._check_deprecated_repo_config():
            self._prompt_migration_dialog()

        self.__set_internal_state()

    def __set_internal_state(self) -> None:
        # parse Kiauh options
        self.kiauh.backup_before_update = self.__read_from_cfg(
            "kiauh",
            "backup_before_update",
            self.config.getboolean,
            False,
        )

        # parse Klipper options
        self.klipper.use_python_binary = self.__read_from_cfg(
            "klipper",
            "use_python_binary",
            self.config.getval,
            None,
            True,
        )
        kl_repos: List[str] = self.__read_from_cfg(
            "klipper",
            "repositories",
            self.config.getvals,
            [KLIPPER_REPO_URL],
        )
        self.klipper.repositories = self.__set_repo_state("klipper", kl_repos)

        # parse Moonraker options
        self.moonraker.use_python_binary = self.__read_from_cfg(
            "moonraker",
            "use_python_binary",
            self.config.getval,
            None,
            True,
        )
        self.moonraker.optional_speedups = self.__read_from_cfg(
            "moonraker",
            "optional_speedups",
            self.config.getboolean,
            True,
        )
        mr_repos: List[str] = self.__read_from_cfg(
            "moonraker",
            "repositories",
            self.config.getvals,
            [MOONRAKER_REPO_URL],
        )
        self.moonraker.repositories = self.__set_repo_state("moonraker", mr_repos)

        # parse Mainsail options
        self.mainsail.port = self.__read_from_cfg(
            "mainsail",
            "port",
            self.config.getint,
            80,
        )
        self.mainsail.unstable_releases = self.__read_from_cfg(
            "mainsail",
            "unstable_releases",
            self.config.getboolean,
            False,
        )

        # parse Fluidd options
        self.fluidd.port = self.__read_from_cfg(
            "fluidd",
            "port",
            self.config.getint,
            80,
        )
        self.fluidd.unstable_releases = self.__read_from_cfg(
            "fluidd",
            "unstable_releases",
            self.config.getboolean,
            False,
        )

    def __check_option_exists(
        self, section: str, option: str, fallback: Any, silent: bool = False
    ) -> bool:
        has_section = self.config.has_section(section)
        has_option = self.config.has_option(section, option)

        if not (has_section and has_option):
            if not silent:
                Logger.print_warn(
                    f"Option '{option}' in section '{section}' not defined. Falling back to '{fallback}'."
                )
            return False
        return True

    def __read_bool_from_cfg(
        self,
        section: str,
        option: str,
        fallback: bool | None = None,
        silent: bool = False,
    ) -> bool | None:
        if not self.__check_option_exists(section, option, fallback, silent):
            return fallback
        return self.config.getboolean(section, option, fallback)

    def __read_from_cfg(
        self,
        section: str,
        option: str,
        getter: Callable[[str, str, T | None], T],
        fallback: T = None,
        silent: bool = False,
    ) -> T:
        if not self.__check_option_exists(section, option, fallback, silent):
            return fallback
        return getter(section, option, fallback)

    def __set_repo_state(self, section: str, repos: List[str]) -> List[Repository]:
        _repos: List[Repository] = []
        for repo in repos:
            try:
                if repo.strip().startswith("#") or repo.strip().startswith(";"):
                    continue
                if "," in repo:
                    url, branch = repo.strip().split(",")

                    if not branch:
                        branch = "master"
                else:
                    url = repo.strip()
                    branch = "master"

                # url must not be empty otherwise it's considered
                # as an unrecoverable, invalid configuration
                if not url:
                    raise InvalidValueError(section, "repositories", repo)

                _repos.append(Repository(url.strip(), branch.strip()))

            except InvalidValueError as e:
                Logger.print_error(f"Error parsing kiauh.cfg: {e}")
                kill()

        return _repos

    def __write_internal_state_to_cfg(self) -> None:
        """Updates the config with current settings, preserving values that haven't been modified"""
        if self.kiauh.backup_before_update is not None:
            self.config.set_option(
                "kiauh",
                "backup_before_update",
                str(self.kiauh.backup_before_update),
            )

        # Handle repositories
        if self.klipper.repositories is not None:
            repos = [f"{repo.url}, {repo.branch}" for repo in self.klipper.repositories]
            self.config.set_option("klipper", "repositories", repos)

        if self.moonraker.repositories is not None:
            repos = [
                f"{repo.url}, {repo.branch}" for repo in self.moonraker.repositories
            ]
            self.config.set_option("moonraker", "repositories", repos)

        # Handle Mainsail settings
        if self.mainsail.port is not None:
            self.config.set_option("mainsail", "port", str(self.mainsail.port))
        if self.mainsail.unstable_releases is not None:
            self.config.set_option(
                "mainsail",
                "unstable_releases",
                str(self.mainsail.unstable_releases),
            )

        # Handle Fluidd settings
        if self.fluidd.port is not None:
            self.config.set_option("fluidd", "port", str(self.fluidd.port))
        if self.fluidd.unstable_releases is not None:
            self.config.set_option(
                "fluidd", "unstable_releases", str(self.fluidd.unstable_releases)
            )

        self.config.write_file(CUSTOM_CFG)

    def _check_deprecated_repo_config(self) -> bool:
        # repo_url and branch are deprecated - 2025.03.23
        for section in ["klipper", "moonraker"]:
            if self.config.has_option(section, "repo_url") or self.config.has_option(
                section, "branch"
            ):
                return True
        return False

    def _prompt_migration_dialog(self) -> None:
        migration_1: List[str] = [
            "Options 'repo_url' and 'branch' are now combined into a 'repositories' option.",
            "\n\n",
            "● Old format:",
            "  [klipper]",
            "  repo_url: https://github.com/Klipper3d/klipper",
            "  branch: master",
            "\n\n",
            "● New format:",
            "  [klipper]",
            "  repositories:",
            "      https://github.com/Klipper3d/klipper, master",
        ]
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Deprecated kiauh.cfg configuration found!",
                "KAIUH can now attempt to automatically migrate the configuration.",
                "\n\n",
                *migration_1,
            ],
        )
        if get_confirm("Migrate to the new format?"):
            self._migrate_repo_config()
        else:
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Please update the configuration file manually.",
                ],
                center_content=True,
            )
            kill()

    def _migrate_repo_config(self) -> None:
        svc = BackupService()
        if not svc.backup_file(CUSTOM_CFG):
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    "Failed to create backup of kiauh.cfg. Aborting migration. Please migrate manually."
                ],
            )
            kill()

        # run migrations
        try:
            # migrate deprecated repo_url and branch options - 2025.03.23
            for section in ["klipper", "moonraker"]:
                if not self.config.has_section(section):
                    continue

                repo_url = self.config.getval(section, "repo_url", fallback="")
                branch = self.config.getval(section, "branch", fallback="master")

                if repo_url:
                    # create repositories option with the old values
                    repositories = [f"{repo_url}, {branch}\n"]
                    self.config.set_option(section, "repositories", repositories)

                    # remove deprecated options
                    self.config.remove_option(section, "repo_url")
                    self.config.remove_option(section, "branch")

                    Logger.print_ok(f"Successfully migrated {section} configuration")

            self.config.write_file(CUSTOM_CFG)
            self.config.read_file(CUSTOM_CFG)  # reload config

        except Exception as e:
            Logger.print_error(f"Error migrating configuration: {e}")
            Logger.print_error("Please migrate manually.")
            kill()
