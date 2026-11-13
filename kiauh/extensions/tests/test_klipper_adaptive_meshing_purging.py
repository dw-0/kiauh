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

from pathlib import Path
from types import SimpleNamespace

import pytest
from core.simple_config_parser.simple_config_parser import SimpleConfigParser
from extensions.klipper_adaptive_meshing_purging.klipper_adaptive_meshing_purging_extension import (
    KlipperAdaptiveMeshingPurgingExtension,
)

MODULE = (
    "extensions.klipper_adaptive_meshing_purging."
    "klipper_adaptive_meshing_purging_extension"
)


@pytest.fixture
def extension() -> KlipperAdaptiveMeshingPurgingExtension:
    return KlipperAdaptiveMeshingPurgingExtension({})


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


def test_object_processing_is_enabled_in_existing_file_manager_section(
    tmp_path: Path, extension
) -> None:
    cfg_file = tmp_path.joinpath("moonraker.conf")
    cfg_file.write_text(
        "[file_manager]\nqueue_gcode_uploads: True\nenable_object_processing: False\n"
    )

    extension._enable_object_processing([SimpleNamespace(cfg_file=cfg_file)])

    scp = SimpleConfigParser()
    scp.read_file(cfg_file)
    assert scp.getval("file_manager", "enable_object_processing") == "True"
    assert scp.getval("file_manager", "queue_gcode_uploads") == "True"
