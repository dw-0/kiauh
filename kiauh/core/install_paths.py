from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Union

INSTALL_ROOT_ENV_VAR = "KIAUH_INSTALL_ROOT"
DEFAULT_INSTALL_ROOT = Path("/var/lib/kiauh")
LEGACY_INSTALL_ROOT = Path.home()


def _normalize_path(path_value: Union[str, Path]) -> Path:
    path = Path(path_value).expanduser()
    try:
        # resolve to an absolute form without requiring the path to exist
        return path.resolve()
    except FileNotFoundError:
        # fall back to absolute path construction if resolution fails
        return path.absolute()


def _legacy_installation_present() -> bool:
    markers = [
        LEGACY_INSTALL_ROOT.joinpath("klipper"),
        LEGACY_INSTALL_ROOT.joinpath("klippy-env"),
        LEGACY_INSTALL_ROOT.joinpath("printer_data"),
    ]

    return any(marker.exists() for marker in markers)


def _legacy_install_root() -> Path:
    return LEGACY_INSTALL_ROOT


def install_root_join(*segments: Union[str, os.PathLike]) -> Path:
    return get_install_root().joinpath(*segments)


@lru_cache(maxsize=1)
def get_install_root() -> Path:
    """
    Determine the base installation directory following the 12-factor principle.
    Priority order:
      1) Environment variable `KIAUH_INSTALL_ROOT`
      2) `install_root` value set in kiauh.cfg
      3) Detected legacy installations within $HOME
      4) Default of `/var/lib/kiauh`
    """
    env_value = os.environ.get(INSTALL_ROOT_ENV_VAR)
    if env_value:
        return _normalize_path(env_value)

    try:
        from core.settings.kiauh_settings import KiauhSettings

        settings = KiauhSettings()
        config_value = getattr(settings.kiauh, "install_root", None)
        if config_value:
            normalized = _normalize_path(config_value)
            if normalized == DEFAULT_INSTALL_ROOT and _legacy_installation_present():
                return _legacy_install_root()
            return normalized
    except Exception:
        # configuration may not yet be available or initialised
        pass

    if _legacy_installation_present():
        return _legacy_install_root()

    return DEFAULT_INSTALL_ROOT
