# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#  It was modified by Dominik Willner <th33xitus@gmail.com>               #
#                                                                         #
#  The original file is part of Moonraker:                                #
#  https://github.com/Arksine/moonraker                                   #
#  Copyright (C) 2025 Eric Callahan <arksine.code@gmail.com>              #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import logging
import pathlib
import re
import shlex
from typing import Any, Dict, List, Tuple


def _get_distro_info() -> Dict[str, Any]:
    release_file = pathlib.Path("/etc/os-release")
    release_info: Dict[str, str] = {}
    with release_file.open("r") as f:
        lexer = shlex.shlex(f, posix=True)
        lexer.whitespace_split = True
        for item in list(lexer):
            if "=" in item:
                key, val = item.split("=", maxsplit=1)
                release_info[key] = val
    return dict(
        distro_id=release_info.get("ID", ""),
        distro_version=release_info.get("VERSION_ID", ""),
        aliases=release_info.get("ID_LIKE", "").split(),
    )


def _convert_version(version: str) -> Tuple[str | int, ...]:
    version = version.strip()
    ver_match = re.match(r"\d+(\.\d+)*((?:-|\.).+)?", version)
    if ver_match is not None:
        return tuple(
            [
                int(part) if part.isdigit() else part
                for part in re.split(r"\.|-", version)
            ]
        )
    return (version,)


class SysDepsParser:
    def __init__(self, distro_info: Dict[str, Any] | None = None) -> None:
        if distro_info is None:
            distro_info = _get_distro_info()
        self.distro_id: str = distro_info.get("distro_id", "")
        self.aliases: List[str] = distro_info.get("aliases", [])
        self.distro_version: Tuple[int | str, ...] = tuple()
        version = distro_info.get("distro_version")
        if version:
            self.distro_version = _convert_version(version)

    def _parse_spec(self, full_spec: str) -> str | None:
        parts = full_spec.split(";", maxsplit=1)
        if len(parts) == 1:
            return full_spec
        pkg_name = parts[0].strip()
        expressions = re.split(r"( and | or )", parts[1].strip())
        if not len(expressions) & 1:
            # There should always be an odd number of expressions.  Each
            # expression is separated by an "and" or "or" operator
            logging.info(
                f"Requirement specifier is missing an expression "
                f"between logical operators : {full_spec}"
            )
            return None
        last_result: bool = True
        last_logical_op: str | None = "and"
        for idx, exp in enumerate(expressions):
            if idx & 1:
                if last_logical_op is not None:
                    logging.info(
                        "Requirement specifier contains sequential logical "
                        f"operators: {full_spec}"
                    )
                    return None
                logical_op = exp.strip()
                if logical_op not in ("and", "or"):
                    logging.info(
                        f"Invalid logical operator {logical_op} in requirement "
                        f"specifier: {full_spec}"
                    )
                    return None
                last_logical_op = logical_op
                continue
            elif last_logical_op is None:
                logging.info(
                    f"Requirement specifier contains two seqential expressions "
                    f"without a logical operator: {full_spec}"
                )
                return None
            dep_parts = re.split(r"(==|!=|<=|>=|<|>)", exp.strip())
            req_var = dep_parts[0].strip().lower()
            if len(dep_parts) != 3:
                logging.info(f"Invalid comparison, must be 3 parts: {full_spec}")
                return None
            elif req_var == "distro_id":
                left_op: str | Tuple[int | str, ...] = self.distro_id
                right_op = dep_parts[2].strip().strip("\"'")
            elif req_var == "distro_version":
                if not self.distro_version:
                    logging.info(
                        "Distro Version not detected, cannot satisfy requirement: "
                        f"{full_spec}"
                    )
                    return None
                left_op = self.distro_version
                right_op = _convert_version(dep_parts[2].strip().strip("\"'"))
            else:
                logging.info(f"Invalid requirement specifier: {full_spec}")
                return None
            operator = dep_parts[1].strip()
            try:
                compfunc = {
                    "<": lambda x, y: x < y,
                    ">": lambda x, y: x > y,
                    "==": lambda x, y: x == y,
                    "!=": lambda x, y: x != y,
                    ">=": lambda x, y: x >= y,
                    "<=": lambda x, y: x <= y,
                }.get(operator, lambda x, y: False)
                result = compfunc(left_op, right_op)
                if last_logical_op == "and":
                    last_result &= result
                else:
                    last_result |= result
                last_logical_op = None
            except Exception:
                logging.exception(f"Error comparing requirements: {full_spec}")
                return None
        if last_result:
            return pkg_name
        return None

    def parse_dependencies(self, sys_deps: Dict[str, List[str]]) -> List[str]:
        if not self.distro_id:
            logging.info(
                "Failed to detect current distro ID, cannot parse dependencies"
            )
            return []
        all_ids = [self.distro_id] + self.aliases
        for distro_id in all_ids:
            if distro_id in sys_deps:
                if not sys_deps[distro_id]:
                    logging.info(
                        f"Dependency data contains an empty package definition "
                        f"for linux distro '{distro_id}'"
                    )
                    continue
                processed_deps: List[str] = []
                for dep in sys_deps[distro_id]:
                    parsed_dep = self._parse_spec(dep)
                    if parsed_dep is not None:
                        processed_deps.append(parsed_dep)
                return processed_deps
        else:
            logging.info(
                f"Dependency data has no package definition for linux "
                f"distro '{self.distro_id}'"
            )
        return []
