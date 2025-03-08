# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from typing import List

from components.klipper.klipper import Klipper
from utils.instance_utils import get_instances


class KlipperInstanceService:
    __cls_instance = None
    __instances: List[Klipper] = []

    def __new__(cls) -> "KlipperInstanceService":
        if cls.__cls_instance is None:
            cls.__cls_instance = super(KlipperInstanceService, cls).__new__(cls)
        return cls.__cls_instance

    def __init__(self) -> None:
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True

    def load_instances(self) -> None:
        self.__instances = get_instances(Klipper)

    def create_new_instance(self, suffix: str) -> Klipper:
        instance = Klipper(suffix)
        self.__instances.append(instance)
        return instance

    def get_all_instances(self) -> List[Klipper]:
        return self.__instances

    def get_instance_by_suffix(self, suffix: str) -> Klipper | None:
        instances: List[Klipper] = [i for i in self.__instances if i.suffix == suffix]
        return instances[0] if instances else None
