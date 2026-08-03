# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from typing import List, Tuple, Union

from core.i18n import _tr
from core.logger import Logger
from core.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from utils.instance_type import InstanceType

ConfigOption = Tuple[str, Union[str, List[str]]]


def add_config_section(
    section: str,
    instances: List[InstanceType],
    options: List[ConfigOption] | None = None,
) -> None:
    if not instances:
        return

    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(_tr("Add section '[{}]' to '{}' ...").format(section, cfg_file))

        if not Path(cfg_file).exists():
            Logger.print_warn(_tr("'{}' not found!").format(cfg_file))
            continue

        scp = SimpleConfigParser()
        scp.read_file(cfg_file)
        if scp.has_section(section):
            Logger.print_info(_tr("Section already exist. Skipped ..."))
            continue

        scp.add_section(section)

        if options is not None:
            for option in reversed(options):
                opt_name = option[0]
                opt_value = option[1]
                scp.set_option(section, opt_name, opt_value)

        scp.write_file(cfg_file)

        Logger.print_ok()


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
        shutil.move(tmp_cfg_path.as_posix(), cfg_file)

        Logger.print_ok()


def remove_config_section(
    section: str, instances: List[InstanceType]
) -> List[InstanceType]:
    removed_from: List[InstanceType] = []
    for instance in instances:
        cfg_file = instance.cfg_file
        Logger.print_status(_tr("Remove section '[{}]' from '{}' ...").format(section, cfg_file))

        if not Path(cfg_file).exists():
            Logger.print_warn(_tr("'{}' not found!").format(cfg_file))
            continue

        scp = SimpleConfigParser()
        scp.read_file(cfg_file)
        if not scp.has_section(section):
            Logger.print_info(_tr("Section does not exist. Skipped ..."))
            continue

        scp.remove_section(section)
        scp.write_file(cfg_file)

        removed_from.append(instance)
        Logger.print_ok()

    return removed_from
