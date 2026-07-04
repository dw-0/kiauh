from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from live.inventory import VM, get_vm
from live.runner import LiveRunner, revert_vm_snapshot
from live.scenarios import load_scenarios


@pytest.fixture(autouse=True)
def silence_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "print_info",
        "print_ok",
        "print_warn",
        "print_error",
        "print_status",
        "print_dialog",
    ):
        monkeypatch.setattr(f"core.logger.Logger.{name}", lambda *a, **k: None)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live: tests that run against a real VM (isolated, never local)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: List[pytest.Item]) -> None:
    skip_live = pytest.mark.skip(reason="live tests skipped by default; use -m live")
    for item in items:
        if item.get_closest_marker("live") and not config.getoption("-m"):
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def live_vm() -> VM:
    """Single VM used for live tests."""
    vm_name = os.environ.get("KIAUH_LIVE_VM", "debian12-kiauh")
    return get_vm(vm_name)


@pytest.fixture(scope="function")
def live_runner(live_vm: VM) -> Generator[LiveRunner, None, None]:
    runner = LiveRunner(live_vm)
    yield runner
    runner.close()


@pytest.fixture(scope="function")
def fresh_vm(live_vm: VM) -> VM:
    """Revert the VM to its clean snapshot before each scenario."""
    revert_vm_snapshot(live_vm)
    return live_vm


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "scenario" in metafunc.fixturenames:
        scenarios = load_scenarios()
        metafunc.parametrize(
            "scenario",
            scenarios,
            ids=[s.get("name", s.get("file", "unknown")) for s in scenarios],
        )
