from __future__ import annotations

import socket

import pytest
from live.guards import UnsafeTargetError, assert_safe_to_run, is_local_host
from live.inventory import VM


class TestIsLocalHost:
    def test_localhost_is_local(self) -> None:
        assert is_local_host("localhost") is True

    def test_127_is_local(self) -> None:
        assert is_local_host("127.0.0.1") is True
        assert is_local_host("::1") is True

    def test_current_hostname_is_local(self) -> None:
        assert is_local_host(socket.gethostname()) is True

    def test_remote_host_is_not_local(self) -> None:
        assert is_local_host("192.168.122.10") is False
        assert is_local_host("example.com") is False


class TestAssertSafeToRun:
    def test_requires_live_allow_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KIAUH_LIVE_ALLOW", raising=False)
        vm = VM(name="vm", host="192.168.122.10", user="u", key_file="k", os="debian-12")

        with pytest.raises(UnsafeTargetError, match="disabled"):
            assert_safe_to_run(vm)

    def test_blocks_localhost(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KIAUH_LIVE_ALLOW", "1")
        monkeypatch.setenv("KIAUH_LIVE_TARGET_HOST", "localhost")
        vm = VM(name="vm", host="localhost", user="u", key_file="k", os="debian-12")

        with pytest.raises(UnsafeTargetError, match="local host"):
            assert_safe_to_run(vm)

    def test_requires_matching_target_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KIAUH_LIVE_ALLOW", "1")
        monkeypatch.setenv("KIAUH_LIVE_TARGET_HOST", "192.168.122.10")
        vm = VM(name="vm", host="192.168.122.11", user="u", key_file="k", os="debian-12")

        with pytest.raises(UnsafeTargetError, match="must match"):
            assert_safe_to_run(vm)

    def test_passes_for_safe_remote_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KIAUH_LIVE_ALLOW", "1")
        monkeypatch.setenv("KIAUH_LIVE_TARGET_HOST", "192.168.122.10")
        vm = VM(name="vm", host="192.168.122.10", user="u", key_file="k", os="debian-12")

        assert assert_safe_to_run(vm) is None
