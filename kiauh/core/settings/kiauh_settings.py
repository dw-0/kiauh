# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from core.backup_manager.backup_manager import BackupManager
from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    NoOptionError,
    NoSectionError,
    SimpleConfigParser,
)
from utils.input_utils import get_confirm
from utils.sys_utils import kill

from kiauh import PROJECT_ROOT

DEFAULT_CFG = PROJECT_ROOT.joinpath("default.kiauh.cfg")
CUSTOM_CFG = PROJECT_ROOT.joinpath("kiauh.cfg")


class NoValueError(Exception):
    """Raised when a required value is not defined for an option"""

    def __init__(self, section: str, option: str):
        msg = f"Missing value for option '{option}' in section '{section}'"
        super().__init__(msg)


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
class RepoSettings:
    repositories: List[Repository] | None = field(default=None)


@dataclass
class WebUiSettings:
    port: int | None = field(default=None)
    unstable_releases: bool | None = field(default=None)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KiauhSettings:
    __instance = None

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
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True
        self.config = SimpleConfigParser()
        self.kiauh = AppSettings()
        self.klipper = RepoSettings()
        self.moonraker = RepoSettings()
        self.mainsail = WebUiSettings()
        self.fluidd = WebUiSettings()

        self._load_config()

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
        self._set_config_options_state()
        self.config.write_file(CUSTOM_CFG)
        self._load_config()

    def _load_config(self) -> None:
        if not CUSTOM_CFG.exists() and not DEFAULT_CFG.exists():
            self.__kill()

        cfg = CUSTOM_CFG if CUSTOM_CFG.exists() else DEFAULT_CFG
        self.config.read_file(cfg)

        needs_migration = self._check_deprecated_repo_config()
        if needs_migration:
            self._prompt_migration_dialog()
            return
        else:
            # Only validate if no migration was needed
            self._validate_cfg()
            self.__set_internal_state()

    def _validate_cfg(self) -> None:
        def __err_and_kill(error: str) -> None:
            Logger.print_error(f"Error validating kiauh.cfg: {error}")
            kill()

        try:
            self._validate_bool("kiauh", "backup_before_update")

            self._validate_repositories("klipper", "repositories")
            self._validate_repositories("moonraker", "repositories")

            self._validate_int("mainsail", "port")
            self._validate_bool("mainsail", "unstable_releases")

            self._validate_int("fluidd", "port")
            self._validate_bool("fluidd", "unstable_releases")

        except ValueError:
            err = f"Invalid value for option '{self._v_option}' in section '{self._v_section}'"
            __err_and_kill(err)
        except NoSectionError:
            err = f"Missing section '{self._v_section}' in config file"
            __err_and_kill(err)
        except NoOptionError:
            err = f"Missing option '{self._v_option}' in section '{self._v_section}'"
            __err_and_kill(err)
        except NoValueError:
            err = f"Missing value for option '{self._v_option}' in section '{self._v_section}'"
            __err_and_kill(err)

    def _validate_bool(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        (bool(self.config.getboolean(section, option)))

    def _validate_int(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        int(self.config.getint(section, option))

    def _validate_str(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        v = self.config.getval(section, option)

        if not v:
            raise ValueError

    def _validate_repositories(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        repos = self.config.getval(section, option)
        if not repos:
            raise NoValueError(section, option)

        for repo in repos:
            if repo.strip().startswith("#") or repo.strip().startswith(";"):
                continue
            try:
                if "," in repo:
                    url, branch = repo.strip().split(",")
                    if not url:
                        raise InvalidValueError(section, option, repo)
                else:
                    url = repo.strip()
                    if not url:
                        raise InvalidValueError(section, option, repo)
            except ValueError:
                raise InvalidValueError(section, option, repo)

    def __set_internal_state(self) -> None:
        self.kiauh.backup_before_update = self.config.getboolean(
            "kiauh", "backup_before_update"
        )

        kl_repos = self.config.getval("klipper", "repositories")
        self.klipper.repositories = self.__set_repo_state(kl_repos)

        mr_repos = self.config.getval("moonraker", "repositories")
        self.moonraker.repositories = self.__set_repo_state(mr_repos)

        self.mainsail.port = self.config.getint("mainsail", "port")
        self.mainsail.unstable_releases = self.config.getboolean(
            "mainsail", "unstable_releases"
        )
        self.fluidd.port = self.config.getint("fluidd", "port")
        self.fluidd.unstable_releases = self.config.getboolean(
            "fluidd", "unstable_releases"
        )

    def __set_repo_state(self, repos: List[str]) -> List[Repository]:
        _repos: List[Repository] = []
        for repo in repos:
            if repo.strip().startswith("#") or repo.strip().startswith(";"):
                continue
            if "," in repo:
                url, branch = repo.strip().split(",")
                if not branch:
                    branch = "master"
            else:
                url = repo.strip()
                branch = "master"
            _repos.append(Repository(url.strip(), branch.strip()))
        return _repos

    def _set_config_options_state(self) -> None:
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
            "The old 'repo_url' and 'branch' options are now combined under 'repositories'.",
            "\n\n",
            "Example format:",
            "[klipper]",
            "repositories:",
            "    https://github.com/Klipper3d/klipper, master",
            "\n\n",
            "[moonraker]",
            "repositories:",
            "    https://github.com/Arksine/moonraker, master",
        ]
        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                "Deprecated repository configuration found!",
                "KAIUH can now attempt to automatically migrate your configuration.",
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
                    "Please update your configuration file manually.",
                ],
                center_content=True,
            )
            kill()

    def _migrate_repo_config(self) -> None:
        bm = BackupManager()
        if not bm.backup_file(CUSTOM_CFG):
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

            # Validate the migrated config
            self._validate_cfg()
            self.__set_internal_state()

        except Exception as e:
            Logger.print_error(f"Error migrating configuration: {e}")
            Logger.print_error("Please migrate manually.")
            kill()

    def __kill(self) -> None:
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
