# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from types import SimpleNamespace

import components.webui_client.client_utils as cu
from components.webui_client.client_utils import get_existing_clients


def _client(installed: bool) -> SimpleNamespace:
    return SimpleNamespace(client_dir=SimpleNamespace(exists=lambda: installed))


def test_get_existing_clients_returns_only_installed(monkeypatch) -> None:
    mainsail = _client(installed=True)
    fluidd = _client(installed=False)
    monkeypatch.setattr(cu, "MainsailData", lambda: mainsail)
    monkeypatch.setattr(cu, "FluiddData", lambda: fluidd)

    # the old get_args(Enum) implementation always returned [], even with a
    # client installed; this pins the corrected behavior
    assert get_existing_clients() == [mainsail]


def test_get_existing_clients_returns_only_fluidd_when_only_fluidd(monkeypatch) -> None:
    mainsail = _client(installed=False)
    fluidd = _client(installed=True)
    monkeypatch.setattr(cu, "MainsailData", lambda: mainsail)
    monkeypatch.setattr(cu, "FluiddData", lambda: fluidd)

    assert get_existing_clients() == [fluidd]


def test_get_existing_clients_returns_both_in_order(monkeypatch) -> None:
    mainsail = _client(installed=True)
    fluidd = _client(installed=True)
    monkeypatch.setattr(cu, "MainsailData", lambda: mainsail)
    monkeypatch.setattr(cu, "FluiddData", lambda: fluidd)

    # both installed -> both returned, Mainsail first
    assert get_existing_clients() == [mainsail, fluidd]


def test_get_existing_clients_empty_when_none_installed(monkeypatch) -> None:
    monkeypatch.setattr(cu, "MainsailData", lambda: _client(installed=False))
    monkeypatch.setattr(cu, "FluiddData", lambda: _client(installed=False))

    assert get_existing_clients() == []
