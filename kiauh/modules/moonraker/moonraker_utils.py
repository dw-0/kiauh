#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import shutil
from typing import List, Dict

from kiauh.core.config_manager.config_manager import ConfigManager
from kiauh.modules.moonraker import (
    DEFAULT_MOONRAKER_PORT,
    MODULE_PATH,
)
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import (
    get_ipv4_addr,
)


def create_example_moonraker_conf(
    instance: Moonraker, ports_map: Dict[str, int]
) -> None:
    Logger.print_status(f"Creating example moonraker.conf in '{instance.cfg_dir}'")
    if instance.cfg_file is not None:
        Logger.print_info(f"moonraker.conf in '{instance.cfg_dir}' already exists.")
        return

    source = os.path.join(MODULE_PATH, "res", "moonraker.conf")
    target = os.path.join(instance.cfg_dir, "moonraker.conf")
    try:
        shutil.copy(source, target)
    except OSError as e:
        Logger.print_error(f"Unable to create example moonraker.conf:\n{e}")
        return

    ports = [
        ports_map.get(instance)
        for instance in ports_map
        if ports_map.get(instance) is not None
    ]
    if ports_map.get(instance.suffix) is None:
        # this could be improved to not increment the max value of the ports list and assign it as the port
        # as it can lead to situation where the port for e.g. instance moonraker-2 becomes 7128 if the port
        # of moonraker-1 is 7125 and moonraker-3 is 7127 and there are moonraker.conf files for moonraker-1
        # and moonraker-3 already. though, there does not seem to be a very reliable way of always assigning
        # the correct port to each instance and the user will likely be required to correct the value manually.
        port = max(ports) + 1 if ports else DEFAULT_MOONRAKER_PORT
    else:
        port = ports_map.get(instance.suffix)

    ports_map[instance.suffix] = port

    ip = get_ipv4_addr().split(".")[:2]
    ip.extend(["0", "0/16"])
    uds = f"{instance.comms_dir}/klippy.sock"

    cm = ConfigManager(target)
    trusted_clients = f"\n{'.'.join(ip)}"
    trusted_clients += cm.get_value("authorization", "trusted_clients")

    cm.set_value("server", "port", str(port))
    cm.set_value("server", "klippy_uds_address", uds)
    cm.set_value("authorization", "trusted_clients", trusted_clients)

    cm.write_config()
    Logger.print_ok(f"Example moonraker.conf created in '{instance.cfg_dir}'")
