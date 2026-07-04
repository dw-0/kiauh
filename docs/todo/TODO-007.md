# PRD #2 - Task 2/5: Scenario loader and Klipper install scenario

**Tags:** `task`, `prd-2`

## Parent PRD

PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM (`docs/prd/PRD-002-live-vm-test-strategy.md`)

## What to build

Implement the YAML scenario loader and the `live` pytest marker. Write the first end-to-end scenario: install Klipper on the Debian 12 VM, define expected outcomes (service file, env file, folders), and run it with snapshot revert before the scenario.

## Acceptance criteria

- [ ] YAML scenario loader parses `name`, `os`, `steps`, and `expected` assertions.
- [ ] `pytest -m live` runs only live scenarios; default run skips them.
- [ ] Klipper install scenario runs on the VM and passes.
- [ ] Snapshot revert happens before the scenario.
- [ ] Expected outcomes include file, service, and folder assertions.

## Blocked by

- TODO-006 (PRD #2 - Task 1/5: VM inventory, SSH fixture, and safety guards)

## Next task

- TODO-008 (PRD #2 - Task 3/5: Remove Klipper and Moonraker scenarios)

## User stories addressed

- User story 1
- User story 7
