from __future__ import annotations

from pathlib import Path

import pytest
from live.inventory import InventoryError, VM, load_inventory


class TestLoadInventory:
    def test_loads_vm_from_inventory(self, tmp_path: Path) -> None:
        inv = tmp_path / "inv.yaml"
        inv.write_text(
            "vms:\n"
            "  - name: debian12\n"
            "    host: 10.0.0.5\n"
            "    user: kiauh\n"
            "    key_file: /key\n"
            "    os: debian-12\n"
        )
        vms = load_inventory(inv)
        assert len(vms) == 1
        assert vms[0].host == "10.0.0.5"
        assert vms[0].key_file == "/key"

    def test_env_overrides_host_and_key_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KIAUH_LIVE_DEBIAN12_HOST", "192.168.1.50")
        monkeypatch.setenv("KIAUH_LIVE_DEBIAN12_KEY_FILE", "/secret/key")

        inv = tmp_path / "inv.yaml"
        inv.write_text(
            "vms:\n"
            "  - name: debian12\n"
            "    host: 10.0.0.5\n"
            "    user: kiauh\n"
            "    key_file: /key\n"
            "    os: debian-12\n"
        )
        vms = load_inventory(inv)
        assert vms[0].host == "192.168.1.50"
        assert vms[0].key_file == "/secret/key"

    def test_missing_host_raises(self, tmp_path: Path) -> None:
        inv = tmp_path / "inv.yaml"
        inv.write_text(
            "vms:\n"
            "  - name: debian12\n"
            "    user: kiauh\n"
            "    key_file: /key\n"
            "    os: debian-12\n"
        )
        with pytest.raises(InventoryError, match="missing 'host'"):
            load_inventory(inv)
