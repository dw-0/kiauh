# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
from typing import Dict, Literal, List, Union, Optional

from components.moonraker import (
    DEFAULT_MOONRAKER_PORT,
    MODULE_PATH,
    MOONRAKER_DIR,
    MOONRAKER_ENV_DIR,
    MOONRAKER_BACKUP_DIR,
    MOONRAKER_DB_BACKUP_DIR,
)
from components.moonraker.moonraker import Moonraker
from components.webui_client import MAINSAIL_DIR, ClientData
from components.webui_client.client_utils import enable_mainsail_remotemode
from core.backup_manager.backup_manager import BackupManager
from core.config_manager.config_manager import ConfigManager
from core.instance_manager.instance_manager import InstanceManager
from core.repo_manager.repo_manager import RepoManager
from utils.common import get_install_status_common
from utils.logger import Logger
from utils.system_utils import (
    get_ipv4_addr,
)


def get_moonraker_status() -> Dict[
    Literal["status", "status_code", "instances", "repo", "local", "remote"],
    Union[str, int],
]:
    status = get_install_status_common(Moonraker, MOONRAKER_DIR, MOONRAKER_ENV_DIR)
    return {
        "status": status.get("status"),
        "status_code": status.get("status_code"),
        "instances": status.get("instances"),
        "repo": RepoManager.get_repo_name(MOONRAKER_DIR),
        "local": RepoManager.get_local_commit(MOONRAKER_DIR),
        "remote": RepoManager.get_remote_commit(MOONRAKER_DIR),
    }


def create_example_moonraker_conf(
    instance: Moonraker,
    ports_map: Dict[str, int],
    clients: Optional[List[ClientData]] = None,
) -> None:
    Logger.print_status(f"Creating example moonraker.conf in '{instance.cfg_dir}'")
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
        port = max(ports) + 1 if ports else DEFAULT_MOONRAKER_PORT
    else:
        port = ports_map.get(instance.suffix)

    ports_map[instance.suffix] = port

    ip = get_ipv4_addr().split(".")[:2]
    ip.extend(["0", "0/16"])
    uds = instance.comms_dir.joinpath("klippy.sock")

    cm = ConfigManager(target)
    trusted_clients = f"\n{'.'.join(ip)}"
    trusted_clients += cm.get_value("authorization", "trusted_clients")

    cm.set_value("server", "port", str(port))
    cm.set_value("server", "klippy_uds_address", str(uds))
    cm.set_value("authorization", "trusted_clients", trusted_clients)

    # add existing client and client configs in the update section
    if clients is not None and len(clients) > 0:
        for c in clients:
            # client part
            c_section = f"update_manager {c.get('name')}"
            c_options = [
                ("type", "web"),
                ("channel", "stable"),
                ("repo", c.get("mr_conf_repo")),
                ("path", c.get("mr_conf_path")),
            ]
            cm.config.add_section(section=c_section)
            for option in c_options:
                cm.config.set(c_section, option[0], option[1])

            # client config part
            c_config = c.get("client_config")
            if c_config.get("dir").exists():
                c_config_section = f"update_manager {c_config.get('name')}"
                c_config_options = [
                    ("type", "git_repo"),
                    ("primary_branch", "master"),
                    ("path", c_config.get("mr_conf_path")),
                    ("origin", c_config.get("mr_conf_origin")),
                    ("managed_services", "klipper"),
                ]
                cm.config.add_section(section=c_config_section)
                for option in c_config_options:
                    cm.config.set(c_config_section, option[0], option[1])

    cm.write_config()
    Logger.print_ok(f"Example moonraker.conf created in '{instance.cfg_dir}'")


def moonraker_to_multi_conversion(new_name: str) -> None:
    """
    Converts the first instance in the List of Moonraker instances to an instance
    with a new name. This method will be called when converting from a single Klipper
    instance install to a multi instance install when Moonraker is also already
    installed with a single instance.
    :param new_name: new name the previous single instance is renamed to
    :return: None
    """
    im = InstanceManager(Moonraker)
    instances: List[Moonraker] = im.instances
    if not instances:
        return

    # in case there are multiple Moonraker instances, we don't want to do anything
    if len(instances) > 1:
        Logger.print_info("More than a single Moonraker instance found. Skipped ...")
        return

    Logger.print_status("Convert Moonraker single to multi instance ...")

    # remove the old single instance
    im.current_instance = im.instances[0]
    im.stop_instance()
    im.disable_instance()
    im.delete_instance()

    # create a new moonraker instance with the new name
    new_instance = Moonraker(suffix=new_name)
    im.current_instance = new_instance

    # patch the server sections klippy_uds_address value to match the new printer_data foldername
    cm = ConfigManager(new_instance.cfg_file)
    if cm.config.has_section("server"):
        cm.set_value(
            "server",
            "klippy_uds_address",
            str(new_instance.comms_dir.joinpath("klippy.sock")),
        )
        cm.write_config()

    # create, enable and start the new moonraker instance
    im.create_instance()
    im.enable_instance()
    im.start_instance()

    # if mainsail is installed, we enable mainsails remote mode
    if MAINSAIL_DIR.exists() and len(im.instances) > 1:
        enable_mainsail_remotemode()


def backup_moonraker_dir():
    bm = BackupManager()
    bm.backup_directory("moonraker", source=MOONRAKER_DIR, target=MOONRAKER_BACKUP_DIR)
    bm.backup_directory(
        "moonraker-env", source=MOONRAKER_ENV_DIR, target=MOONRAKER_BACKUP_DIR
    )


def backup_moonraker_db_dir() -> None:
    im = InstanceManager(Moonraker)
    instances: List[Moonraker] = im.instances
    bm = BackupManager()

    for instance in instances:
        name = f"database-{instance.data_dir_name}"
        bm.backup_directory(
            name, source=instance.db_dir, target=MOONRAKER_DB_BACKUP_DIR
        )
