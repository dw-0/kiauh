# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

from typing import List

import main as main_module
import pytest


class _FakeKiauhAppSettings:
    def __init__(self, language: str | None = None) -> None:
        self.language = language


class _FakeKiauhSettings:
    def __init__(self, language: str | None = None) -> None:
        self.kiauh = _FakeKiauhAppSettings(language=language)


class _FakeMainMenu:
    """Minimal stand-in for ``core.menus.main_menu.MainMenu``."""

    instances: List["_FakeMainMenu"] = []

    def __init__(self) -> None:
        self._run = False
        type(self).instances.append(self)

    def run(self) -> None:
        self._run = True

    @classmethod
    def reset(cls) -> None:
        cls.instances = []


@pytest.fixture(autouse=True)
def _reset_fake_menu() -> None:
    _FakeMainMenu.reset()
    yield
    _FakeMainMenu.reset()


def _patch_tui_seeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise the heavyweight side-effects triggered when launching the TUI."""
    monkeypatch.setattr(main_module, "KiauhSettings", _FakeKiauhSettings)
    monkeypatch.setattr(main_module, "setup_i18n", lambda language=None: None)
    monkeypatch.setattr(main_module, "ensure_encoding", lambda: None)
    monkeypatch.setattr(main_module, "MainMenu", _FakeMainMenu)


class TestMainDispatch:
    def test_no_command_launches_tui(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # rc == -1 means "fall back to the TUI": ``MainMenu().run()`` is called.
        monkeypatch.setattr(main_module, "run_cli", lambda: -1)
        _patch_tui_seeds(monkeypatch)

        main_module.main()

        assert _FakeMainMenu.instances
        assert all(m._run for m in _FakeMainMenu.instances)

    def test_cli_success_returns_cleanly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # rc == 0 means the CLI succeeded; the TUI must NOT start and main must
        # NOT call sys.exit.
        monkeypatch.setattr(main_module, "run_cli", lambda: 0)
        _patch_tui_seeds(monkeypatch)

        main_module.main()  # must not raise SystemExit

        assert _FakeMainMenu.instances == []

    def test_cli_failure_exits_nonzero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # rc > 0 means the CLI reported a failure; main must propagate via sys.exit.
        monkeypatch.setattr(main_module, "run_cli", lambda: 2)
        _patch_tui_seeds(monkeypatch)

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 2
        assert _FakeMainMenu.instances == []

    def test_tui_keyboard_interrupt_is_absorbed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A Ctrl-C while the TUI runs must be caught and printed friendly
        # instead of crashing with a traceback.
        class _InterruptingMenu(_FakeMainMenu):
            def run(self) -> None:
                raise KeyboardInterrupt()

        monkeypatch.setattr(main_module, "run_cli", lambda: -1)
        monkeypatch.setattr(main_module, "KiauhSettings", _FakeKiauhSettings)
        monkeypatch.setattr(main_module, "setup_i18n", lambda language=None: None)
        monkeypatch.setattr(main_module, "ensure_encoding", lambda: None)
        monkeypatch.setattr(main_module, "MainMenu", _InterruptingMenu)

        main_module.main()  # must not raise; KeyboardInterrupt is absorbed

    def test_tui_keyboard_interrupt_stops_spinners(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Any loading spinner still running when the user hits Ctrl-C must be
        # stopped before the interpreter starts shutting down.
        stopped: list[bool] = []

        class _InterruptingMenu(_FakeMainMenu):
            def run(self) -> None:
                raise KeyboardInterrupt()

        monkeypatch.setattr(main_module, "run_cli", lambda: -1)
        monkeypatch.setattr(main_module, "KiauhSettings", _FakeKiauhSettings)
        monkeypatch.setattr(main_module, "setup_i18n", lambda language=None: None)
        monkeypatch.setattr(main_module, "ensure_encoding", lambda: None)
        monkeypatch.setattr(main_module, "MainMenu", _InterruptingMenu)
        monkeypatch.setattr(
            main_module.Spinner, "stop_all", lambda: stopped.append(True)
        )

        main_module.main()

        assert stopped == [True]
