from __future__ import annotations

from typing import Any, Dict, List

import pytest

from live.inventory import VM
from live.runner import LiveRunner
from live.scenarios import assert_expected


@pytest.mark.live
def test_scenario(fresh_vm: VM, live_runner: LiveRunner, scenario: Dict[str, Any]) -> None:
    """Run a live scenario against the VM and verify expected outcomes."""
    steps: List[Dict[str, Any]] = scenario.get("steps", [])
    expected = scenario.get("expected", [])

    for step in steps:
        command = step["command"]
        timeout = step.get("timeout", 120)
        result = live_runner.run(command, timeout=timeout)
        assert result.returncode == 0, (
            f"Step failed: {' '.join(command)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    host = live_runner.get_host()
    assert_expected(host, expected)
