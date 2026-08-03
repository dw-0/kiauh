# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from __future__ import annotations

import gettext
import os
from pathlib import Path
from typing import Callable, Dict, List

# NOTE: do NOT `from kiauh import APPLICATION_ROOT` here — that creates a
# circular import because kiauh/__init__.py wants to re-export `_tr` / `_ntr`.
# Resolve APPLICATION_ROOT relative to this file instead (same value).
APPLICATION_ROOT: Path = Path(__file__).resolve().parent.parent
LOCALE_DIR: Path = APPLICATION_ROOT / "locale"
DEFAULT_LANGUAGE: str = "en"
SUPPORTED_LANGUAGES: List[str] = ["en", "zh_CN", "zh_TW"]

LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    # NOTE: these are the native-language display labels shown in the Settings
    # menu footer next to the language toggle. They are intentionally written
    # in the language's own script (like Android's language picker always
    # shows each language in its native script, so e.g. 简体中文 is discoverable
    # even when the active language is English). All OTHER user-visible text
    # comes from the kiauh/locale/*.po transcript files.
    "en": "English",
    "zh_CN": "简体中文",
    "zh_TW": "繁體中文",
}
LANGUAGE_CYCLE: List[str] = ["en", "zh_CN", "zh_TW"]

# Identity function used purely to mark strings for xgettext extraction in
# contexts where the msgid is stored as a plain variable/dict value (rather
# than being passed directly to _tr() / _ntr() at the source line). Using
# `N_("my string")` tells xgettext to include "my string" in the POT catalog,
# but at runtime N_ just returns the string unchanged. Subsequent translation
# then happens via the normal `_tr(N_("my string"))` path at the call site.
N_ = lambda message: message  # noqa: E731

# ---------------------------------------------------------------------------
# Soft-fork i18n contract (Android resource / GNU gettext style):
#
#   1. English msgid = canonical source of truth written directly in .py code
#      (NEVER hardcode any non-English text in a Python file).
#   2. ALL translations live inside kiauh/locale/<lang>/LC_MESSAGES/messages.{po,mo}
#      — the .po file is the "language transcript".
#   3. If a translation is missing (new upstream string, corrupt .mo, bogus
#      language code, catalog absent), the runtime ALWAYS degrades to English
#      msgid. The UI never crashes because of translation problems.
#   4. After merging upstream, re-run:  python3 build_translations.py --rebase
#      which xgettext-extracts a fresh .pot, msgmerge-merges it into the two
#      .po transcript files, and reports newly fuzzy / untranslated entries.
#      Translators then fill in gaps with Poedit / vim msgfmt -c.
# ---------------------------------------------------------------------------

_translation: gettext.GNUTranslations | gettext.NullTranslations | None = None
# Track active language separately from the catalog so that NullTranslations
# (fallback when .mo is missing / corrupted / empty) still reports a correct
# user-visible language code instead of falling back to DEFAULT_LANGUAGE.
_active_language: str = DEFAULT_LANGUAGE


def get_system_language() -> str:
    """
    Detect the system language from locale environment variables.
    Falls back to DEFAULT_LANGUAGE if detection fails or the language
    is not in SUPPORTED_LANGUAGES.
    """
    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        lang = os.environ.get(env_var)
        if not lang:
            continue
        normalized = lang.split(".")[0].replace("-", "_")
        if normalized in SUPPORTED_LANGUAGES:
            return normalized
        # Catch generic zh-TW/zh-HK before falling back to zh_CN
        if normalized in ("zh_TW", "zh_HK", "zh_MO") or normalized.endswith("_TW") or normalized.endswith("_HK"):
            return "zh_TW"
        if normalized.startswith("zh"):
            return "zh_CN"
    return DEFAULT_LANGUAGE


def setup_i18n(language: str | None = None) -> None:
    """
    Initialize the gettext translation catalog for the requested language.

    **Guaranteed never to raise for translation-related reasons** — every
    failure path degrades to a NullTranslations object (returns English msgid,
    same behaviour as Android missing a strings.xml entry).

    Call this once at startup (and whenever language changes at runtime).
    """
    global _translation, _active_language

    if language and language in SUPPORTED_LANGUAGES:
        lang = language
    else:
        lang = get_system_language()
    _active_language = lang

    try:
        # fallback=True is the critical switch:
        #   * If <LOCALE_DIR>/<lang>/LC_MESSAGES/messages.mo is missing -> no raise
        #   * If lang partial-matches (e.g. "zh" vs "zh_CN") -> GNU still tries
        #   * All msgids missing from the catalog -> return msgid (English)
        _translation = gettext.translation(
            "messages",
            localedir=str(LOCALE_DIR),
            languages=[lang, DEFAULT_LANGUAGE],
            fallback=True,
        )
    except Exception:
        # Corrupt .mo, weird platform bug, OSError... any unexpected thing
        # still ends up with English, never a crash.
        _translation = gettext.NullTranslations()

    try:
        _translation.install()
    except Exception:
        pass  # install() only sets builtins._ ; safe to skip


def _tr(message: str) -> str:
    """
    Translate a single message string through the active catalog.
    Safe to call before setup_i18n() — it will lazily initialize.
    """
    global _translation
    if _translation is None:
        setup_i18n()
        assert _translation is not None
    return _translation.gettext(message)


def _ntr(singular: str, plural: str, n: int) -> str:
    """
    Translate a plural-form message. Prefer this for any text containing
    a count that changes grammar in some languages (e.g. Chinese uses
    the same form for singular/plural, but the catalog still needs it).
    """
    global _translation
    if _translation is None:
        setup_i18n()
        assert _translation is not None
    return _translation.ngettext(singular, plural, n)


def get_translation_functions() -> tuple[Callable[[str], str], Callable[[str, str, int], str]]:
    """Return both translation functions as a tuple (gettext, ngettext)."""
    global _translation
    if _translation is None:
        setup_i18n()
        assert _translation is not None
    return (_translation.gettext, _translation.ngettext)


def current_language() -> str:
    """
    Return the currently active language code.

    Uses the separately-tracked ``_active_language`` (not the catalog's info
    dict) so that the English-fallback NullTranslations object still reports
    the user's *requested* language.
    """
    return _active_language


def next_language(current: str) -> str:
    """Cycle through languages in a deterministic, reviewable order."""
    if current not in LANGUAGE_CYCLE:
        return LANGUAGE_CYCLE[0]
    idx = LANGUAGE_CYCLE.index(current)
    return LANGUAGE_CYCLE[(idx + 1) % len(LANGUAGE_CYCLE)]
