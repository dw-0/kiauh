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

from typing import List

import pytest
from components.katapult import katapult
from utils.git_utils import GitException


class TestInstallKatapult:
    @pytest.fixture
    def cloned(self, monkeypatch) -> List[str]:
        cloned: List[str] = []
        monkeypatch.setattr(katapult, "print_katapult_brick_warning", lambda: None)
        monkeypatch.setattr(katapult, "get_confirm", lambda *a, **k: True)
        monkeypatch.setattr(katapult, "get_instances", lambda _: [])
        monkeypatch.setattr(
            katapult, "git_clone_wrapper", lambda repo, *a: cloned.append(repo)
        )
        return cloned

    def test_installs_without_can_interface(self, cloned: List[str]) -> None:
        katapult.install_katapult()
        assert cloned == [katapult.KATAPULT_REPO]

    def test_aborts_without_confirmation(self, cloned: List[str], monkeypatch) -> None:
        monkeypatch.setattr(katapult, "get_confirm", lambda *a, **k: False)
        katapult.install_katapult()
        assert cloned == []

    def test_reports_clone_failure(self, monkeypatch) -> None:
        def fail(*args) -> None:
            raise GitException("clone failed")

        monkeypatch.setattr(katapult, "print_katapult_brick_warning", lambda: None)
        monkeypatch.setattr(katapult, "get_confirm", lambda *a, **k: True)
        monkeypatch.setattr(katapult, "get_instances", lambda _: [])
        monkeypatch.setattr(katapult, "git_clone_wrapper", fail)

        katapult.install_katapult()
