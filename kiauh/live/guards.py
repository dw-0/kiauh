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
import socket
from ipaddress import ip_address
from typing import List, Set


class UnsafeTargetError(Exception):
    """Raised when a live test target is considered unsafe."""


LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}
LOCAL_ADDRESSES = {"127.0.0.1", "::1"}


def _local_interface_ips() -> Set[str]:
    """Return all IP addresses assigned to local network interfaces."""
    ips: Set[str] = set()
    try:
        hostname = socket.gethostname()
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            addr = info[4][0]
            ips.add(addr)
    except socket.gaierror:
        pass
    return ips


def _resolve(host: str) -> List[str]:
    """Resolve a hostname to its IP addresses."""
    try:
        infos = socket.getaddrinfo(host, None)
        return [info[4][0] for info in infos]
    except socket.gaierror:
        return []


def is_local_host(host: str) -> bool:
    """Return True if the host refers to the local machine."""
    host_lower = host.lower().strip()

    if host_lower in LOCAL_HOSTNAMES:
        return True

    if host_lower in LOCAL_ADDRESSES:
        return True

    if host_lower == socket.gethostname().lower():
        return True

    resolved = _resolve(host_lower)
    local_ips = _local_interface_ips() | LOCAL_ADDRESSES
    for addr in resolved:
        if addr in local_ips:
            return True
        try:
            if ip_address(addr).is_loopback:
                return True
        except ValueError:
            pass

    return False


def assert_safe_to_run(vm) -> None:
    """Multi-layer safety check before running live tests against a VM."""
    if os.environ.get("KIAUH_LIVE_ALLOW") != "1":
        raise UnsafeTargetError(
            "Live tests disabled. Set KIAUH_LIVE_ALLOW=1 to enable."
        )

    if not vm.host:
        raise UnsafeTargetError("VM host is empty")

    if is_local_host(vm.host):
        raise UnsafeTargetError(
            f"Refusing to run live tests against local host: {vm.host}"
        )

    if os.environ.get("KIAUH_LIVE_TARGET_HOST") != vm.host:
        raise UnsafeTargetError(
            "KIAUH_LIVE_TARGET_HOST must match the selected VM host"
        )
