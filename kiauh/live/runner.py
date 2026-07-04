# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

import paramiko
import testinfra

from live.guards import assert_safe_to_run, is_local_host
from live.inventory import VM


class LiveRunnerError(Exception):
    pass


class LiveRunner:
    """SSH runner for live VM tests."""

    def __init__(self, vm: VM) -> None:
        assert_safe_to_run(vm)
        self.vm = vm
        self._ssh: paramiko.SSHClient | None = None

    def connect(self) -> paramiko.SSHClient:
        if self._ssh is not None:
            return self._ssh

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_file = Path(self.vm.key_file).expanduser()
        client.connect(
            self.vm.host,
            username=self.vm.user,
            key_filename=str(key_file),
            look_for_keys=False,
            timeout=30,
        )
        self._ssh = client
        return client

    def run(self, command: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
        client = self.connect()
        cmd = " ".join(command) if isinstance(command, list) else command
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        rc = stdout.channel.recv_exit_status()
        return subprocess.CompletedProcess(
            args=command,
            returncode=rc,
            stdout=stdout.read().decode("utf-8", errors="replace"),
            stderr=stderr.read().decode("utf-8", errors="replace"),
        )

    def get_host(self) -> testinfra.host.Host:
        """Return a Testinfra host for assertions."""
        key_file = Path(self.vm.key_file).expanduser()
        return testinfra.get_host(
            f"paramiko://{self.vm.user}@{self.vm.host}",
            ssh_identity_file=str(key_file),
        )

    def close(self) -> None:
        if self._ssh is not None:
            self._ssh.close()
            self._ssh = None


def revert_vm_snapshot(vm: VM) -> None:
    """Revert a VM to the configured snapshot before a scenario."""
    if not vm.domain or not vm.snapshot:
        raise LiveRunnerError("VM inventory missing domain or snapshot")

    if is_local_host(vm.host):
        raise LiveRunnerError("Refusing to revert a local VM snapshot")

    result = subprocess.run(
        ["virsh", "snapshot-revert", vm.domain, vm.snapshot, "--running"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise LiveRunnerError(
            f"Failed to revert snapshot: {result.stderr.strip() or result.stdout.strip()}"
        )
