# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import tempfile
from pathlib import Path
from typing import List, TypeVar, Tuple, Optional

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.config_manager.config_manager import ConfigManager
from utils.logger import Logger

B = TypeVar("B", Klipper, Moonraker)
ConfigOption = Tuple[str, str]


def add_config_section(
    section: str,
    instances: List[B],
    options: Optional[List[ConfigOption]] = None,
) -> None:
    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Add section '[{section}]' to '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            continue

        cm = ConfigManager(cfg_file)
        if cm.config.has_section(section):
            Logger.print_info("Section already exist. Skipped ...")
            continue

        cm.config.add_section(section)

        if options is not None:
            for option in options:
                cm.config.set(section, option[0], option[1])

        cm.write_config()


def add_config_section_at_top(section: str, instances: List[B]):
    for instance in instances:
        tmp_cfg = tempfile.NamedTemporaryFile(mode="w", delete=False)
        tmp_cfg_path = Path(tmp_cfg.name)
        cmt = ConfigManager(tmp_cfg_path)
        cmt.config.add_section(section)
        cmt.write_config()
        tmp_cfg.close()

        cfg_file = instance.cfg_file
        with open(cfg_file, "r") as org:
            org_content = org.readlines()
        with open(tmp_cfg_path, "a") as tmp:
            tmp.writelines(org_content)

        cfg_file.unlink()
        tmp_cfg_path.rename(cfg_file)


def remove_config_section(section: str, instances: List[B]) -> None:
    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Remove section '[{section}]' from '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            continue

        cm = ConfigManager(cfg_file)
        if not cm.config.has_section(section):
            Logger.print_info("Section does not exist. Skipped ...")
            continue

        cm.config.remove_section(section)
        cm.write_config()
