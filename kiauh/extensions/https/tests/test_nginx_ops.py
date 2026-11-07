# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from pathlib import Path
from unittest.mock import MagicMock, patch

from extensions.https.nginx_ops import (
    backup_site,
    discard_backup,
    nginx_config_test,
    reload_nginx,
    restore_site,
    write_site,
)

SITE = Path("/etc/nginx/sites-available/mainsail")
BACKUP = Path("/etc/nginx/sites-available/mainsail.kiauh.bak")


def test_backup_site_copies_with_sudo():
    with patch("extensions.https.nginx_ops.run") as run:
        backup = backup_site(SITE)
    assert backup == BACKUP
    assert run.call_args.args[0] == ["sudo", "cp", str(SITE), str(BACKUP)]


def test_write_site_passes_content_via_tee_stdin():
    with patch("extensions.https.nginx_ops.run") as run:
        write_site(SITE, "server {}\n")
    assert run.call_args.args[0] == ["sudo", "tee", str(SITE)]
    assert run.call_args.kwargs["input"] == b"server {}\n"


def test_restore_site_copies_backup_back():
    with patch("extensions.https.nginx_ops.run") as run:
        restore_site(BACKUP, SITE)
    assert run.call_args.args[0] == ["sudo", "cp", str(BACKUP), str(SITE)]


def test_discard_backup_removes_with_sudo():
    with patch("extensions.https.nginx_ops.run") as run:
        discard_backup(BACKUP)
    assert run.call_args.args[0] == ["sudo", "rm", "-f", str(BACKUP)]


def test_nginx_config_test_returns_true_on_zero_exit():
    result = MagicMock(returncode=0, stderr=b"")
    with patch("extensions.https.nginx_ops.run", return_value=result):
        assert nginx_config_test() is True


def test_nginx_config_test_returns_false_and_logs_error_on_nonzero_exit():
    result = MagicMock(returncode=1, stderr=b"nginx: [emerg] cert not found")
    with patch("extensions.https.nginx_ops.run", return_value=result):
        with patch("extensions.https.nginx_ops.Logger") as logger:
            assert nginx_config_test() is False
    logged = " ".join(str(c) for c in logger.print_error.call_args_list)
    assert "cert not found" in logged


def test_reload_nginx_uses_systemctl_reload():
    with patch("extensions.https.nginx_ops.cmd_sysctl_service") as svc:
        reload_nginx()
    svc.assert_called_once_with("nginx", "reload")
