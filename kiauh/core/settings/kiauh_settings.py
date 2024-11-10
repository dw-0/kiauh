# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    NoOptionError,
    NoSectionError,
    SimpleConfigParser,
)
from utils.sys_utils import kill

from kiauh import PROJECT_ROOT

DEFAULT_CFG = PROJECT_ROOT.joinpath("default.kiauh.cfg")
CUSTOM_CFG = PROJECT_ROOT.joinpath("kiauh.cfg")


@dataclass
class AppSettings:
    backup_before_update: bool | None = field(default=None)


@dataclass
class RepoSettings:
    repo_url: str | None = field(default=None)
    branch: str | None = field(default=None)


@dataclass
class WebUiSettings:
    port: str | None = field(default=None)
    unstable_releases: bool | None = field(default=None)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KiauhSettings:
    _instance = None

    def __new__(cls, *args, **kwargs) -> "KiauhSettings":
        if cls._instance is None:
            cls._instance = super(KiauhSettings, cls).__new__(cls, *args, **kwargs)
        return cls._instance

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
            self._kill()

        cfg = CUSTOM_CFG if CUSTOM_CFG.exists() else DEFAULT_CFG
        self.config.read_file(cfg)

        self._validate_cfg()
        self._apply_settings_from_file()

    def _validate_cfg(self) -> None:
        try:
            self._validate_bool("kiauh", "backup_before_update")

            self._validate_str("klipper", "repo_url")
            self._validate_str("klipper", "branch")

            self._validate_int("mainsail", "port")
            self._validate_bool("mainsail", "unstable_releases")

            self._validate_int("fluidd", "port")
            self._validate_bool("fluidd", "unstable_releases")

        except ValueError:
            err = f"Invalid value for option '{self._v_option}' in section '{self._v_section}'"
            Logger.print_error(err)
            kill()
        except NoSectionError:
            err = f"Missing section '{self._v_section}' in config file"
            Logger.print_error(err)
            kill()
        except NoOptionError:
            err = f"Missing option '{self._v_option}' in section '{self._v_section}'"
            Logger.print_error(err)
            kill()

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

    def _apply_settings_from_file(self) -> None:
        self.kiauh.backup_before_update = self.config.getboolean(
            "kiauh", "backup_before_update"
        )
        self.klipper.repo_url = self.config.getval("klipper", "repo_url")
        self.klipper.branch = self.config.getval("klipper", "branch")
        self.moonraker.repo_url = self.config.getval("moonraker", "repo_url")
        self.moonraker.branch = self.config.getval("moonraker", "branch")
        self.mainsail.port = self.config.getint("mainsail", "port")
        self.mainsail.unstable_releases = self.config.getboolean(
            "mainsail", "unstable_releases"
        )
        self.fluidd.port = self.config.getint("fluidd", "port")
        self.fluidd.unstable_releases = self.config.getboolean(
            "fluidd", "unstable_releases"
        )

    def _set_config_options_state(self) -> None:
        self.config.set_option(
            "kiauh",
            "backup_before_update",
            str(self.kiauh.backup_before_update),
        )
        self.config.set_option("klipper", "repo_url", self.klipper.repo_url)
        self.config.set_option("klipper", "branch", self.klipper.branch)
        self.config.set_option("moonraker", "repo_url", self.moonraker.repo_url)
        self.config.set_option("moonraker", "branch", self.moonraker.branch)
        self.config.set_option("mainsail", "port", str(self.mainsail.port))
        self.config.set_option(
            "mainsail",
            "unstable_releases",
            str(self.mainsail.unstable_releases),
        )
        self.config.set_option("fluidd", "port", str(self.fluidd.port))
        self.config.set_option(
            "fluidd", "unstable_releases", str(self.fluidd.unstable_releases)
        )

    def _kill(self) -> None:
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
