# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

SCENARIOS_DIR = Path(__file__).parent.joinpath("scenarios")


class ScenarioError(Exception):
    pass


def load_scenarios(directory: Path | None = None) -> List[Dict[str, Any]]:
    path = Path(directory or SCENARIOS_DIR)
    if not path.exists():
        return []

    scenarios = []
    for file in sorted(path.glob("*.yaml")):
        data = yaml.safe_load(file.read_text())
        if not isinstance(data, dict):
            raise ScenarioError(f"Scenario {file.name} is not a mapping")
        data.setdefault("file", str(file))
        scenarios.append(data)
    return scenarios


def assert_expected(host, expected: List[Dict[str, Any]]) -> None:
    """Evaluate expected outcomes using Testinfra assertions."""
    failures = []

    for item in expected:
        try:
            _assert_item(host, item)
        except AssertionError as e:
            failures.append(f"{item}: {e}")

    if failures:
        raise AssertionError("\n".join(failures))


def _assert_item(host, item: Dict[str, Any]) -> None:
    assertion_type = item.get("type")

    if assertion_type == "service":
        service = host.service(item["name"])
        state = item.get("state")
        if state == "running":
            assert service.is_running, f"service {item['name']} is not running"
        elif state == "enabled":
            assert service.is_enabled, f"service {item['name']} is not enabled"

    elif assertion_type == "file":
        file = host.file(item["path"])
        if item.get("exists", True):
            assert file.exists, f"file {item['path']} does not exist"
        else:
            assert not file.exists, f"file {item['path']} should not exist"

    elif assertion_type == "package":
        pkg = host.package(item["name"])
        assert pkg.is_installed, f"package {item['name']} is not installed"

    elif assertion_type == "port":
        socket = host.socket(f"tcp://{item['address']}:{item['port']}")
        assert socket.is_listening, f"port {item['port']} is not listening"

    elif assertion_type == "command":
        result = host.run(item["command"])
        assert result.rc == item.get("returncode", 0), (
            f"command {item['command']} returned {result.rc}: {result.stderr}"
        )

    else:
        raise ScenarioError(f"Unknown assertion type: {assertion_type}")
