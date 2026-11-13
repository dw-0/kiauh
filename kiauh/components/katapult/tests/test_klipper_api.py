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
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List

import pytest
from components.katapult import klipper_api
from components.katapult.klipper_api import (
    KlipperApiError,
    get_mcu_versions,
    query_klipper,
    wait_until_ready,
)

Handler = Callable[[Dict[str, Any]], Dict[str, Any]]


class _FakeKlipper:
    """Answers requests on a Unix socket like Klipper's API server"""

    def __init__(self, uds: Path, handler: Handler) -> None:
        self.requests: List[Dict[str, Any]] = []
        self._handler = handler
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(uds.as_posix())
        self._server.listen()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self._server.accept()
            except OSError:
                return
            with conn:
                data = b""
                while not data.endswith(b"\x03"):
                    data += conn.recv(4096)
                request = json.loads(data[:-1])
                self.requests.append(request)
                response = {"id": request["id"], **self._handler(request)}
                conn.sendall(json.dumps(response).encode() + b"\x03")

    def close(self) -> None:
        self._server.close()


@pytest.fixture
def uds() -> Iterator[Path]:
    # Unix socket paths are limited to about 100 characters
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        yield Path(tmp, "klippy.sock")


@pytest.fixture
def klipper(uds: Path) -> Iterator[Callable[[Handler], _FakeKlipper]]:
    servers: List[_FakeKlipper] = []

    def start(handler: Handler) -> _FakeKlipper:
        servers.append(_FakeKlipper(uds, handler))
        return servers[-1]

    yield start
    for server in servers:
        server.close()


class TestQueryKlipper:
    def test_returns_the_result(self, uds: Path, klipper) -> None:
        server = klipper(lambda request: {"result": {"state": "ready"}})

        assert query_klipper(uds, "info", {}) == {"state": "ready"}
        assert server.requests == [{"id": 1, "method": "info", "params": {}}]

    def test_raises_on_errors(self, uds: Path, klipper) -> None:
        klipper(lambda request: {"error": {"message": "Unknown method"}})

        with pytest.raises(KlipperApiError, match="Unknown method"):
            query_klipper(uds, "nope", {})

    def test_raises_when_klipper_isnt_running(self, uds: Path) -> None:
        with pytest.raises(KlipperApiError, match="can't be reached"):
            query_klipper(uds, "info", {})


class TestWaitUntilReady:
    def test_waits_while_starting_up(self, uds: Path, klipper, monkeypatch) -> None:
        states = iter(["startup", "startup", "ready"])
        klipper(lambda request: {"result": {"state": next(states)}})
        monkeypatch.setattr(klipper_api.time, "sleep", lambda seconds: None)

        assert wait_until_ready(uds) == ("ready", "")

    def test_returns_errors(self, uds: Path, klipper) -> None:
        klipper(
            lambda request: {
                "result": {"state": "error", "state_message": "Unable to connect"}
            }
        )

        assert wait_until_ready(uds) == ("error", "Unable to connect")

    def test_times_out(self, uds: Path, monkeypatch) -> None:
        monkeypatch.setattr(klipper_api.time, "sleep", lambda seconds: None)

        state, message = wait_until_ready(uds, timeout=0.01)

        assert state == "startup"
        assert "can't be reached" in message


class TestGetMcuVersions:
    def test_returns_known_mcus(self, uds: Path, klipper) -> None:
        server = klipper(
            lambda request: {
                "result": {
                    "status": {
                        "mcu": {"mcu_version": "v0.13.0"},
                        # Klipper returns an empty status for unknown objects
                        "mcu T9": {},
                    }
                }
            }
        )

        assert get_mcu_versions(uds, ["mcu", "mcu T9"]) == {"mcu": "v0.13.0"}
        assert server.requests[0]["params"] == {
            "objects": {"mcu": ["mcu_version"], "mcu T9": ["mcu_version"]}
        }
