# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
import configparser
from configparser import ConfigParser
from typing import Dict, Union
from kiauh import PROJECT_ROOT
from utils.constants import RESET_FORMAT, COLOR_RED
from utils.logger import Logger
from utils.system_utils import kill


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KiauhSettings:
    _instance = None
    _default_cfg = PROJECT_ROOT.joinpath("default_kiauh.cfg")
    _custom_cfg = PROJECT_ROOT.joinpath("kiauh.cfg")

    def __new__(cls, *args, **kwargs) -> "KiauhSettings":
        if cls._instance is None:
            cls._instance = super(KiauhSettings, cls).__new__(cls, *args, **kwargs)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self.__initialized:
            return
        self.__initialized = True
        self.settings: Dict[str, Dict[str, Union[str, int, bool]]] = {}

        self.config = ConfigParser()
        if self._custom_cfg.exists():
            self.config.read(self._custom_cfg)
        elif self._default_cfg.exists():
            self.config.read(self._default_cfg)
        else:
            self._kill()

        sections = self.config.sections()
        for s in sections:
            self.settings[s] = dict(self.config[s])

        self._validate_cfg()

    def get(self, key: str, value: Union[str, int, bool]) -> Union[str, int, bool]:
        return self.settings[key][value]

    def set(self, key: str, value: Union[str, int, bool]) -> None:
        self.settings[key][value] = value

    def save(self) -> None:
        for section, option in self.settings.items():
            self.config[section] = option
        with open(self._custom_cfg, "w") as configfile:
            self.config.write(configfile)

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
        except configparser.NoSectionError:
            err = f"Missing section '{self._v_section}' in config file"
            Logger.print_error(err)
            kill()
        except configparser.NoOptionError:
            err = f"Missing option '{self._v_option}' in section '{self._v_section}'"
            Logger.print_error(err)
            kill()

    def _validate_bool(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        bool(self.config.getboolean(section, option))

    def _validate_int(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        int(self.config.getint(section, option))

    def _validate_str(self, section: str, option: str) -> None:
        self._v_section, self._v_option = (section, option)
        v = self.config.get(section, option)
        if v.isdigit() or v.lower() == "true" or v.lower() == "false":
            raise ValueError

    def _kill(self) -> None:
        l1 = "!!! ERROR !!!"
        l2 = "No KIAUH configuration file found!"
        error = textwrap.dedent(
            f"""
            {COLOR_RED}/=======================================================\\
            | {l1:^53} |
            | {l2:^53} |
            \=======================================================/{RESET_FORMAT}
            """
        )[1:]
        print(error, end="")
        kill()
