# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import json
import socket
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Klipper's API server terminates every message with this byte
MESSAGE_END = b"\x03"


class KlipperApiError(Exception):
    pass


def query_klipper(
    uds: Path, method: str, params: Dict[str, Any], timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Send a request to Klipper's API server, like Moonraker does |
    :param uds: The Unix domain socket of the Klipper instance
    :param method: The API method, e.g. 'info'
    :param params: The parameters of the method
    :param timeout: Timeout in seconds for connecting and receiving the response
    :return: The result of the request
    :raises KlipperApiError: If Klipper can't be reached or returns an error
    """
    request = json.dumps({"id": 1, "method": method, "params": params})
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(uds.as_posix())
            sock.sendall(request.encode() + MESSAGE_END)
            data = b""
            while MESSAGE_END not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    raise KlipperApiError("Klipper closed the connection")
                data += chunk
    except OSError as e:
        raise KlipperApiError(f"Klipper can't be reached: {e}") from e

    try:
        response = json.loads(data.split(MESSAGE_END, 1)[0])
    except ValueError as e:
        raise KlipperApiError("Klipper sent an invalid response") from e
    if "error" in response:
        raise KlipperApiError(str(response["error"].get("message", "unknown")))
    result: Dict[str, Any] = response.get("result", {})
    return result


def wait_until_ready(uds: Path, timeout: float = 60.0) -> Tuple[str, str]:
    """
    Wait until Klipper has finished starting up and connecting to its MCUs |
    :param uds: The Unix domain socket of the Klipper instance
    :param timeout: Maximum time to wait, in seconds
    :return: Klipper's state ('ready', 'error', 'shutdown' or 'startup' on timeout)
        and its state message
    """
    deadline = time.monotonic() + timeout
    state, message = "startup", "Klipper didn't start in time"
    while time.monotonic() < deadline:
        try:
            info = query_klipper(uds, "info", {})
            state = info.get("state", "startup")
            message = info.get("state_message", "")
        except KlipperApiError as e:
            # the socket is only created once Klipper is running
            message = str(e)
        if state != "startup":
            break
        time.sleep(1)
    return state, message


def get_mcu_versions(uds: Path, sections: List[str]) -> Dict[str, str]:
    """
    Get the firmware version each MCU reported to Klipper |
    :param uds: The Unix domain socket of the Klipper instance
    :param sections: Config sections of the MCUs, e.g. 'mcu' or 'mcu T0'
    :return: The version of each MCU known to this Klipper instance
    """
    params = {"objects": {section: ["mcu_version"] for section in sections}}
    status = query_klipper(uds, "objects/query", params).get("status", {})
    return {
        section: values["mcu_version"]
        for section, values in status.items()
        if isinstance(values, dict) and values.get("mcu_version")
    }
