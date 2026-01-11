# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from typing import Dict, List

from components.moonraker.moonraker import Moonraker
from utils.instance_utils import get_instances


class MoonrakerInstanceService:
    __cls_instance = None
    __instances: List[Moonraker] = []

    def __new__(cls) -> "MoonrakerInstanceService":
        if cls.__cls_instance is None:
            cls.__cls_instance = super(MoonrakerInstanceService, cls).__new__(cls)
        return cls.__cls_instance

    def __init__(self) -> None:
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True

    def load_instances(self) -> None:
        self.__instances = get_instances(Moonraker)

    def create_new_instance(self, suffix: str) -> Moonraker:
        instance = Moonraker(suffix)
        self.__instances.append(instance)
        return instance

    def get_all_instances(self) -> List[Moonraker]:
        return self.__instances

    def get_instance_by_suffix(self, suffix: str) -> Moonraker | None:
        instances: List[Moonraker] = [i for i in self.__instances if i.suffix == suffix]
        return instances[0] if instances else None

    def get_instance_port_map(self) -> Dict[str, int]:
        return {i.suffix: i.port for i in self.__instances}
