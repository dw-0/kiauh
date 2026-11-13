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

import pytest
from extensions.tmc_autotune.tmc_autotune_extension import TmcAutotuneExtension

MODULE = "extensions.tmc_autotune.tmc_autotune_extension"


@pytest.fixture
def extension() -> TmcAutotuneExtension:
    return TmcAutotuneExtension({})


def test_failed_update_is_not_reported_as_successful(
    monkeypatch: pytest.MonkeyPatch, extension
) -> None:
    ok_messages: list[str] = []

    def failing_pull(*args) -> None:
        raise RuntimeError("pull failed")

    monkeypatch.setattr(f"{MODULE}.check_file_exist", lambda *args: True)
    monkeypatch.setattr(f"{MODULE}.get_confirm", lambda *args, **kwargs: False)
    monkeypatch.setattr(f"{MODULE}.get_instances", lambda *args: [])
    monkeypatch.setattr(
        f"{MODULE}.stop_klipper_instances_interactively", lambda *args: True
    )
    monkeypatch.setattr(f"{MODULE}.git_pull_wrapper", failing_pull)
    monkeypatch.setattr(
        f"{MODULE}.Logger.print_ok",
        lambda msg, *args, **kwargs: ok_messages.append(msg),
    )

    extension.update_extension()

    assert ok_messages == []
