# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parents[2].joinpath(".env"))
except ImportError:
    load_dotenv = None

DEFAULT_INVENTORY_PATH = Path(__file__).parent.joinpath("inventory.yaml")


@dataclass
class VM:
    name: str
    host: str
    user: str
    key_file: str
    os: str
    domain: str | None = None
    snapshot: str | None = None


class InventoryError(Exception):
    pass


def _env_var_name(vm_name: str, suffix: str) -> str:
    safe_name = vm_name.replace("-", "_").upper()
    return f"KIAUH_LIVE_{safe_name}_{suffix.upper()}"


def load_inventory(path: Path | None = None) -> List[VM]:
    inventory_path = Path(path or os.environ.get("KIAUH_LIVE_INVENTORY", DEFAULT_INVENTORY_PATH))
    if not inventory_path.exists():
        raise InventoryError(f"Inventory file not found: {inventory_path}")

    data = yaml.safe_load(inventory_path.read_text())
    if not data or "vms" not in data:
        raise InventoryError("Inventory must contain a 'vms' list")

    vms = []
    for item in data["vms"]:
        for required in ("name", "user", "os"):
            if required not in item:
                raise InventoryError(f"VM '{item.get('name', '?')}' missing '{required}'")

        name = item["name"]
        host = os.environ.get(_env_var_name(name, "host"), item.get("host"))
        key_file = os.environ.get(_env_var_name(name, "key_file"), item.get("key_file"))

        if not host:
            raise InventoryError(f"VM '{name}' missing 'host' (inventory or env)")
        if not key_file:
            raise InventoryError(f"VM '{name}' missing 'key_file' (inventory or env)")

        vms.append(
            VM(
                name=name,
                host=host,
                user=item["user"],
                key_file=key_file,
                os=item["os"],
                domain=item.get("domain"),
                snapshot=item.get("snapshot"),
            )
        )
    return vms


def get_vm(name: str, path: Path | None = None) -> VM:
    for vm in load_inventory(path):
        if vm.name == name:
            return vm
    raise InventoryError(f"VM '{name}' not found in inventory")
