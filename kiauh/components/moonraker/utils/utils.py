# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from components.moonraker import (
    MODULE_PATH,
    MOONRAKER_BACKUP_DIR,
    MOONRAKER_DB_BACKUP_DIR,
    MOONRAKER_DEFAULT_PORT,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
)
from components.moonraker.moonraker import Moonraker
from components.webui_client.base_data import BaseWebClient
from core.backup_manager.backup_manager import BackupManager
from core.logger import Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.instance_utils import get_instances
from utils.sys_utils import (
    get_ipv4_addr,
)


def get_moonraker_status() -> ComponentStatus:
    return get_install_status(MOONRAKER_DIR, MOONRAKER_ENV_DIR, Moonraker)


def create_example_moonraker_conf(
    instance: Moonraker,
    ports_map: Dict[str, int],
    clients: Optional[List[BaseWebClient]] = None,
) -> None:
    Logger.print_status(f"Creating example moonraker.conf in '{instance.base.cfg_dir}'")
    if instance.cfg_file.is_file():
        Logger.print_info(f"'{instance.cfg_file}' already exists.")
        return

    source = MODULE_PATH.joinpath("assets/moonraker.conf")
    target = instance.cfg_file
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
        port = max(ports) + 1 if ports else MOONRAKER_DEFAULT_PORT
    else:
        port = ports_map.get(instance.suffix)

    ports_map[instance.suffix] = port

    ip = get_ipv4_addr().split(".")[:2]
    ip.extend(["0", "0/16"])
    uds = instance.base.comms_dir.joinpath("klippy.sock")

    scp = SimpleConfigParser()
    scp.read_file(target)
    trusted_clients: List[str] = [
        f"    {'.'.join(ip)}\n",
        *scp.getval("authorization", "trusted_clients"),
    ]

    scp.set_option("server", "port", str(port))
    scp.set_option("server", "klippy_uds_address", str(uds))
    scp.set_option("authorization", "trusted_clients", trusted_clients)

    # add existing client and client configs in the update section
    if clients is not None and len(clients) > 0:
        for c in clients:
            # client part
            c_section = f"update_manager {c.name}"
            c_options = [
                ("type", "web"),
                ("channel", "stable"),
                ("repo", c.repo_path),
                ("path", c.client_dir),
            ]
            scp.add_section(section=c_section)
            for option in c_options:
                scp.set_option(c_section, option[0], option[1])

            # client config part
            c_config = c.client_config
            if c_config.config_dir.exists():
                c_config_section = f"update_manager {c_config.name}"
                c_config_options = [
                    ("type", "git_repo"),
                    ("primary_branch", "master"),
                    ("path", c_config.config_dir),
                    ("origin", c_config.repo_url),
                    ("managed_services", "klipper"),
                ]
                scp.add_section(section=c_config_section)
                for option in c_config_options:
                    scp.set_option(c_config_section, option[0], option[1])

    scp.write_file(target)
    Logger.print_ok(f"Example moonraker.conf created in '{instance.base.cfg_dir}'")


def backup_moonraker_dir() -> None:
    bm = BackupManager()
    bm.backup_directory("moonraker", source=MOONRAKER_DIR, target=MOONRAKER_BACKUP_DIR)
    bm.backup_directory(
        "moonraker-env", source=MOONRAKER_ENV_DIR, target=MOONRAKER_BACKUP_DIR
    )


def backup_moonraker_db_dir() -> None:
    instances: List[Moonraker] = get_instances(Moonraker)
    bm = BackupManager()

    for instance in instances:
        name = f"database-{instance.data_dir.name}"
        bm.backup_directory(
            name, source=instance.db_dir, target=MOONRAKER_DB_BACKUP_DIR
        )


def load_sysdeps_json(file: Path) -> Dict[str, List[str]]:
    try:
        sysdeps: Dict[str, List[str]] = json.loads(file.read_bytes())
    except json.JSONDecodeError as e:
        Logger.print_error(f"Unable to parse {file.name}:\n{e}")
        return {}
    else:
        return sysdeps
