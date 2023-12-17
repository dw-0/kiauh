#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import configparser
from typing import Union

from kiauh.utils.logger import Logger


# noinspection PyMethodMayBeStatic
class ConfigManager:
    def __init__(self, cfg_file: str):
        self.config_file = cfg_file
        self.config = configparser.ConfigParser()

    def read_config(self) -> None:
        if not self.config_file:
            Logger.print_error("Unable to read config file. File not found.")
            return

        self.config.read_file(open(self.config_file, "r"))

    def write_config(self) -> None:
        with open(self.config_file, "w") as cfg:
            self.config.write(cfg)

    def get_value(self, section: str, key: str, silent=False) -> Union[str, bool, None]:
        if not self.config.has_section(section):
            if not silent:
                log = f"Section not defined. Unable to read section: [{section}]."
                Logger.print_error(log)
            return None

        if not self.config.has_option(section, key):
            if not silent:
                log = f"Option not defined in section [{section}]. Unable to read option: '{key}'."
                Logger.print_error(log)
            return None

        value = self.config.get(section, key)
        if value == "True" or value == "true":
            return True
        elif value == "False" or value == "false":
            return False
        else:
            return value

    def set_value(self, section: str, key: str, value: str):
        self.config.set(section, key, value)
