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
import tempfile
from pathlib import Path
from typing import List, Tuple

from core.logger import Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from utils.instance_type import InstanceType

ConfigOption = Tuple[str, str]


def add_config_section(
    section: str,
    instances: List[InstanceType],
    options: List[ConfigOption] | None = None,
) -> None:
    if not instances:
        return

    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Add section '[{section}]' to '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            continue

        scp = SimpleConfigParser()
        scp.read_file(cfg_file)
        if scp.has_section(section):
            Logger.print_info("Section already exist. Skipped ...")
            continue

        scp.add_section(section)

        if options is not None:
            for option in reversed(options):
                scp.set_option(section, option[0], option[1])

        scp.write_file(cfg_file)

        Logger.print_ok("OK!")


def add_config_section_at_top(section: str, instances: List[InstanceType]) -> None:
    # TODO: this could be implemented natively in SimpleConfigParser
    for instance in instances:
        tmp_cfg = tempfile.NamedTemporaryFile(mode="w", delete=False)
        tmp_cfg_path = Path(tmp_cfg.name)
        scp = SimpleConfigParser()
        scp.read_file(tmp_cfg_path)
        scp.add_section(section)
        scp.write_file(tmp_cfg_path)
        tmp_cfg.close()

        cfg_file = instance.cfg_file
        with open(cfg_file, "r") as org:
            org_content = org.readlines()
        with open(tmp_cfg_path, "a") as tmp:
            tmp.writelines(org_content)

        cfg_file.unlink()
        shutil.move(tmp_cfg_path, cfg_file)

        Logger.print_ok("OK!")


def remove_config_section(
    section: str, instances: List[InstanceType]
) -> List[InstanceType]:
    removed_from: List[instances] = []
    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(f"Remove section '[{section}]' from '{cfg_file}' ...")

        if not Path(cfg_file).exists():
            Logger.print_warn(f"'{cfg_file}' not found!")
            continue

        scp = SimpleConfigParser()
        scp.read_file(cfg_file)
        if not scp.has_section(section):
            Logger.print_info("Section does not exist. Skipped ...")
            continue

        scp.remove_section(section)
        scp.write_file(cfg_file)

        removed_from.append(instance)
        Logger.print_ok("OK!")

    return removed_from
