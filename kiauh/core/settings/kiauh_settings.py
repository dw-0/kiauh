# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import configparser
import textwrap
from typing import Dict, Union

from core.config_manager.config_manager import CustomConfigParser
from utils.constants import COLOR_RED, RESET_FORMAT
from utils.logger import Logger
from utils.sys_utils import kill

from kiauh import PROJECT_ROOT


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
        self.config = CustomConfigParser()
        self.settings: Dict[str, Dict[str, Union[str, int, bool]]] = {}
        self._load_settings()

    def get(self, section: str, option: str) -> Union[str, int, bool]:
        return self.settings[section][option]

    def set(self, section: str, option: str, value: Union[str, int, bool]) -> None:
        self.settings[section][option] = value

    def save(self) -> None:
        for section, option in self.settings.items():
            self.config[section] = option
        with open(self._custom_cfg, "w") as configfile:
            self.config.write(configfile)
        self._load_settings()

    def _load_settings(self) -> None:
        if self._custom_cfg.exists():
            self.config.read(self._custom_cfg)
        elif self._default_cfg.exists():
            self.config.read(self._default_cfg)
        else:
            self._kill()
        self._validate_cfg()
        self._parse_settings()

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

    def _parse_settings(self):
        for s in self.config.sections():
            self.settings[s] = {}
            for o, v in self.config.items(s):
                if v.lower() == "true":
                    self.settings[s][o] = True
                elif v.lower() == "false":
                    self.settings[s][o] = False
                elif v.isdigit():
                    self.settings[s][o] = int(v)
                else:
                    self.settings[s][o] = v

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
