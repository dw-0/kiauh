## ⚠️ Working on this PRD

Do NOT implement this PRD directly. It has been broken into sequential tasks.
Work through the tasks below in order.

## Task Index

| # | Task | Todo | Blocked by | Status |
|---|------|------|------------|--------|
| 1/5 | VM inventory, SSH fixture, and safety guards | TODO-006 | — | 🔄 open |
| 2/5 | Scenario loader and Klipper install scenario | TODO-007 | TODO-006 | ⏳ blocked |
| 3/5 | Remove Klipper and Moonraker scenarios | TODO-008 | TODO-007 | ⏳ blocked |
| 4/5 | Mainsail and Fluidd install scenarios | TODO-009 | TODO-008 | ⏳ blocked |
| 5/5 | Backup, restore, and update scenarios | TODO-010 | TODO-009 | ⏳ blocked |

Start with: **TODO-006** (PRD #2 - Task 1/5: VM inventory, SSH fixture, and safety guards)

---

# PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM

**Tags:** `prd`, `prd-2`

## Problem Statement

- Pytest unit tests cannot validate real package installs, systemd services, git clones, and OS-specific behavior.
- Running workflow tests on a local developer machine risks destroying the environment.
- Need reproducible, isolated acceptance tests with explicit expected outcomes.

## Solution

- Acceptance tests run only on a pre-built Debian 12 QEMU/KVM VM.
- Test harness connects via SSH; never executes on the local host.
- YAML scenarios define workflows and expected outcomes.
- VM snapshot reverted before every scenario.
- Multi-layer safety prevents local execution.

## User Stories

1. As a maintainer, I want install/remove Klipper workflow tested on a real VM, so I know the installer still works.
2. As a maintainer, I want install/remove Moonraker workflow tested, so API stack compatibility is verified.
3. As a maintainer, I want Mainsail/Fluidd install workflow tested, so web client setup works end-to-end.
4. As a maintainer, I want backup/restore workflow tested, so user data survives the cycle.
5. As a maintainer, I want tests parameterized by VM inventory, so future Ubuntu/Debian versions can be added without code changes.
6. As a maintainer, I want local execution blocked by multiple guards, so the developer machine is never modified.
7. As a CI operator, I want scenario results to show expected vs actual outcome, so failures are actionable.

## Implementation Decisions

- VM inventory config supplies host/IP, SSH user/key, OS family. No auto-provisioning; base images are prepared in advance.
- Test harness: pytest + SSH fixture + Testinfra assertions. Commands are routed through SSH; assertions use Testinfra modules for service/file/package/port state.
- Scenario schema YAML: `name`, `os`, `steps` (commands/options), `expected` (assertions for service running, file exists, package installed, port reachable, process present).
- Snapshot reset: revert VM overlay before every scenario. Scenarios must be independent.
- Safety guards: require `KIAUH_LIVE_TARGET_HOST`; abort if value is `localhost`, `127.*`, or matches current hostname; abort if target resolves to a local interface; verify SSH host key differs from local; optional explicit confirmation prompt.
- Workflow priority: (1) install/remove Klipper; (2) install/remove Moonraker; (3) install Mainsail/Fluidd; (4) backup/restore; (5) update flows.
- Test user on VM has passwordless sudo; VM has internet access; long installs use timeouts.
- Scenario runner exposes expected outcome per step; failure shows command, expected assertion, and actual result.

## Testing Decisions

- Acceptance tests verify observable system state, not internal functions.
- Each scenario defines exact pre-state (clean snapshot) and post-state assertions.
- Flaky network commands are retried with timeout; failures attach relevant VM logs.
- Live suite is marked with a `live` pytest marker and excluded from the default `pytest` run.

## Out of Scope

- Running live tests on the local machine or bare metal.
- Auto-provisioning or building VM images.
- Testing every extension in the first iteration; only core workflows.

## Further Notes

- Future OS matrix (Ubuntu 22.04/24.04) is enabled by adding inventory entries and matching base images; no harness changes needed.
