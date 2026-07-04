# PRD #2 - Task 3/5: Remove Klipper and Moonraker scenarios

**Tags:** `task`, `prd-2`

## Parent PRD

PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM (`docs/prd/PRD-002-live-vm-test-strategy.md`)

## What to build

Add remove-Klipper and install/remove-Moonraker scenarios. Each scenario starts from a clean snapshot. Capture relevant VM logs when a scenario fails to make debugging actionable.

## Acceptance criteria

- [ ] Remove Klipper scenario runs and verifies service/files are gone.
- [ ] Install Moonraker scenario runs and verifies service/config/log files.
- [ ] Remove Moonraker scenario runs and verifies cleanup.
- [ ] Failure output includes tail of installer/service logs.

## Blocked by

- TODO-007 (PRD #2 - Task 2/5: Scenario loader and Klipper install scenario)

## Next task

- TODO-009 (PRD #2 - Task 4/5: Mainsail and Fluidd install scenarios)

## User stories addressed

- User story 2
