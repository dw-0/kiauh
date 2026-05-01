# Proposal: Configurable Base Directory for KIAUH

> **Status:** Proposed  
> **Author:** itdir  
> **Target:** dw-0/kiauh upstream  
> **Backward Compatible:** Yes — zero behaviour change when no override is set

---

## Executive Summary

This proposal introduces a configurable base directory (`BASE_DIR`) for all
component and extension installations in KIAUH. Today, every install path is
hard-wired to `Path.home()` (the running user's home directory). This change
replaces those references with a single, centrally-defined `BASE_DIR` that
**defaults to `Path.home()`** and can optionally be overridden via:

1. The `KIAUH_BASE_DIR` environment variable (highest priority), or
2. The `base_dir` option in `kiauh.cfg` (persisted configuration)

When neither is set, KIAUH behaves **identically to upstream** — every path
resolves to `~/component_name` exactly as before.

---

## Problem Statement

### Current State (Upstream)

KIAUH hard-codes `Path.home()` in **~25 module-level constants** across
components and extensions:

```python
# kiauh/components/klipper/__init__.py  (upstream)
KLIPPER_DIR = Path.home().joinpath("klipper")
KLIPPER_ENV_DIR = Path.home().joinpath("klippy-env")

# kiauh/components/moonraker/__init__.py  (upstream)
MOONRAKER_DIR = Path.home().joinpath("moonraker")

# kiauh/extensions/octoeverywhere/__init__.py  (upstream)
OE_DIR = Path.home().joinpath("octoeverywhere")
```

This design assumes a single user running a single Klipper stack in their
home directory. It prevents several legitimate deployment scenarios.

### Use Cases Blocked by Hard-Coded Paths

| Scenario | Description |
|----------|-------------|
| **Multi-printer farms** | A print farm operator wants separate Klipper stacks under `/srv/printer1/`, `/srv/printer2/` |
| **System-wide installs** | A shared workstation where Klipper is installed under `/opt/klipper-stack/` |
| **Container/chroot deployments** | Docker or systemd-nspawn environments where `$HOME` doesn't exist or is ephemeral |
| **CI/CD testing** | Automated test pipelines that need deterministic, non-home install paths |
| **Backup portability** | Backups that reference a configurable root instead of a user-specific home directory |

---

## Proposed Solution

### Architecture

```
Resolution Order (first non-empty absolute path wins):

  ┌─────────────────────────────────┐
  │ 1. KIAUH_BASE_DIR env variable  │  ← Highest priority (ops/CI)
  ├─────────────────────────────────┤
  │ 2. base_dir in kiauh.cfg       │  ← Persisted user preference
  ├─────────────────────────────────┤
  │ 3. Path.home()                  │  ← Default (upstream behaviour)
  └─────────────────────────────────┘
```

### Code Changes Summary

| File | Change | Impact |
|------|--------|--------|
| `core/constants.py` | Add `_resolve_base_dir()` → `BASE_DIR` | Single source of truth |
| `default.kiauh.cfg` | Add commented `#base_dir:` option | Self-documenting |
| `core/settings/kiauh_settings.py` | Add `base_dir` to `AppSettings` | Persistence support |
| `main.py` | Log non-default `BASE_DIR` at startup | User feedback |
| 15× `__init__.py` (components) | `Path.home()` → `BASE_DIR` | Path consistency |
| 10× `__init__.py` (extensions) | `Path.home()` → `BASE_DIR` | Path consistency |
| `utils/fs_utils.py` | `Path.home()` → `BASE_DIR` in `get_data_dir()` | Data dir resolution |
| `utils/sys_utils.py` | Check both home + `BASE_DIR` for NGINX perms | Backward compat |
| `core/services/backup_service.py` | Search both home + `BASE_DIR` for fallback | Backward compat |
| `components/moonraker/utils/utils.py` | Search both home + `BASE_DIR` for fallback | Backward compat |
| `components/webui_client/client_utils.py` | Use `tempfile.mkstemp()` for nginx cfg tmp | Safety fix |

### Key Design Decisions

1. **Module-level constant, not a function call.** `BASE_DIR` is evaluated once
   at import time. This matches the existing pattern used by `SYSTEMD`,
   `NGINX_SITES_AVAILABLE`, etc. in `core/constants.py`.

2. **Config file is read with a minimal parser** (not `KiauhSettings`) to avoid
   circular imports. Component `__init__` modules import `BASE_DIR` before
   `KiauhSettings` is constructed.

3. **Env var takes priority over config file.** This follows the standard
   twelve-factor app convention and allows ops teams to override the setting
   without modifying files.

4. **Only absolute paths are accepted.** Empty strings, whitespace, and relative
   paths silently fall back to `Path.home()`, preventing misconfiguration.

5. **Backward-compatible fallback search.** Backup and NGINX permission checks
   search *both* `Path.home()` and `BASE_DIR` when they differ, so existing
   installations in `~` are always found.

---

## Analysis

### What Changes for Existing Users?

**Nothing.** When `KIAUH_BASE_DIR` is unset and `base_dir` is absent from
`kiauh.cfg`, `BASE_DIR` resolves to `Path.home()` — the exact same value
upstream uses today. Every path remains `~/klipper`, `~/moonraker`,
`~/printer_data`, etc.

### What Changes for the Codebase?

The diff touches ~25 files, but the pattern in each is identical:

```diff
- from pathlib import Path
+ from core.constants import BASE_DIR

- COMPONENT_DIR = Path.home().joinpath("component")
+ COMPONENT_DIR = BASE_DIR.joinpath("component")
```

No logic changes. No new dependencies. No new classes. The only *behavioural*
additions are in backup fallback search (search both directories) and NGINX
permission checks (ensure both directories have execute rights).

---

## SWOT Analysis

### Strengths
- **Zero-impact default.** No behaviour change for the >99% of users who run
  KIAUH from their home directory.
- **Single constant.** One `BASE_DIR` in one file, imported everywhere. Easy to
  audit, easy to grep.
- **Settings integration.** `kiauh.cfg` already governs ports, repos, and
  update preferences — `base_dir` fits naturally.
- **Env var support.** Standard mechanism for container/CI overrides without
  file changes.
- **Backward-compatible fallbacks.** Backup search and NGINX permissions handle
  the case where `BASE_DIR ≠ Path.home()` gracefully.

### Weaknesses
- **Module-level constant.** `BASE_DIR` is evaluated at import time, so
  changing it requires restarting KIAUH. (This is the same constraint as all
  other constants in `core/constants.py`.)
- **Config file parsed twice.** `_resolve_base_dir()` does a lightweight read
  of `kiauh.cfg` before `KiauhSettings` parses it fully. This is intentional
  (to avoid circular imports) but adds a small amount of duplication.
- **Touches many files.** The diff spans ~25 files, which can be intimidating
  to review. However, each change is mechanical and identical.

### Opportunities
- **Multi-printer-per-host support.** With a configurable base dir, KIAUH can
  be invoked multiple times with different `KIAUH_BASE_DIR` values to manage
  separate printer stacks on one machine.
- **Container-native deployments.** Makes KIAUH usable in Docker, Podman, and
  systemd-nspawn without special `HOME` manipulation.
- **Easier automated testing.** CI pipelines can set `KIAUH_BASE_DIR` to a
  temporary directory, avoiding pollution of the test user's home.
- **Foundation for future features.** A configurable root paves the way for
  profile management, per-printer settings, and fleet administration.

### Threats
- **Upstream merge conflicts.** If upstream adds new `Path.home()` references
  in new components or extensions, they would need to use `BASE_DIR` instead.
  This is mitigable with a lint rule or CI check.
- **User misconfiguration.** An incorrect `base_dir` path could cause KIAUH to
  install into an unexpected location. Mitigated by: (a) only accepting
  absolute paths, (b) logging the active `BASE_DIR` at startup, and (c)
  leaving the option commented out by default.

---

## Pros & Cons

### Pros

1. ✅ **100% backward compatible** — default behaviour is unchanged
2. ✅ **Minimal API surface** — one constant (`BASE_DIR`), one env var, one config option
3. ✅ **Follows existing patterns** — uses the same module-level constant style as `SYSTEMD`, `NGINX_SITES_AVAILABLE`
4. ✅ **Self-documenting** — `default.kiauh.cfg` includes commented documentation
5. ✅ **Startup feedback** — non-default base dir is logged at launch
6. ✅ **Security improvement** — nginx config temp files use `tempfile.mkstemp()` instead of predictable `~/name.tmp`
7. ✅ **Dual-search fallback** — backups find data in both `~` and `BASE_DIR`

### Cons

1. ⚠️ **Large diff** — touches ~25 files (all mechanical, same pattern)
2. ⚠️ **Ongoing maintenance** — new components must use `BASE_DIR` instead of `Path.home()`
3. ⚠️ **Not runtime-changeable** — requires restart to take effect (same as all other constants)
4. ⚠️ **Dual config parse** — `kiauh.cfg` read once by `_resolve_base_dir()` and once by `KiauhSettings`

---

## Migration Guide

### For Users

No migration needed. KIAUH works exactly as before.

To use a custom base directory:

```bash
# Option A: environment variable (temporary / per-session)
export KIAUH_BASE_DIR=/opt/klipper-farm
./kiauh.sh

# Option B: persistent configuration
# Edit kiauh.cfg and add under [kiauh]:
#   base_dir: /opt/klipper-farm
```

### For Developers / Downstream Forks

When adding a new component or extension, use `BASE_DIR` instead of
`Path.home()`:

```python
from core.constants import BASE_DIR

MY_COMPONENT_DIR = BASE_DIR.joinpath("my-component")
```

---

## Comparison with Alternative Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **This proposal (BASE_DIR constant)** | Simple, one constant, follows existing patterns | Touches many files |
| **Monkey-patch `Path.home()`** | Zero file changes needed | Fragile, affects all Python code, terrible practice |
| **Runtime path resolver function** | Lazy evaluation possible | Every path access becomes a function call; breaks existing APIs |
| **Centralized path registry** | All paths in one file | Massive refactor; breaks all existing imports |
| **Symlink-based approach** | No code changes | Fragile, OS-dependent, hard to debug |

The proposed approach (module-level `BASE_DIR` constant) offers the best
trade-off between simplicity, compatibility, and maintainability.

---

## Testing

### Automated

```bash
# Default behaviour (no override)
PYTHONPATH=kiauh python3 -c "
from core.constants import BASE_DIR
from pathlib import Path
assert BASE_DIR == Path.home()
print('PASS: default')
"

# Environment variable override
KIAUH_BASE_DIR=/opt/test PYTHONPATH=kiauh python3 -c "
from core.constants import BASE_DIR
assert str(BASE_DIR) == '/opt/test'
print('PASS: env var')
"

# Invalid values fall back to home
KIAUH_BASE_DIR='' PYTHONPATH=kiauh python3 -c "
from core.constants import BASE_DIR
from pathlib import Path
assert BASE_DIR == Path.home()
print('PASS: empty env')
"

KIAUH_BASE_DIR='relative' PYTHONPATH=kiauh python3 -c "
from core.constants import BASE_DIR
from pathlib import Path
assert BASE_DIR == Path.home()
print('PASS: relative env')
"
```

### Manual

1. Run KIAUH without any override → verify all paths use `~`
2. Set `KIAUH_BASE_DIR=/tmp/kiauh-test` → verify startup log message
3. Add `base_dir: /tmp/kiauh-test` to `kiauh.cfg` → verify paths update
4. Set both env var and config → verify env var wins

---

## Conclusion

This proposal provides a clean, backward-compatible mechanism for configuring
KIAUH's installation base directory. It follows existing codebase conventions,
integrates with the settings system, and opens the door for multi-printer and
container deployments — all without changing the experience for existing users.

We respectfully request the upstream maintainers consider this change for
inclusion in a future KIAUH release.
