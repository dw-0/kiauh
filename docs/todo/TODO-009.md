# PRD #2 - Task 4/5: Mainsail and Fluidd install scenarios

**Tags:** `task`, `prd-2`

## Parent PRD

PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM (`docs/prd/PRD-002-live-vm-test-strategy.md`)

## What to build

Add install scenarios for Mainsail and Fluidd web clients. Assert that the static files are deployed and the reverse-proxy/service config is in place. Harden the snapshot-revert fixture so it runs reliably before every scenario.

## Acceptance criteria

- [ ] Mainsail install scenario passes on the VM.
- [ ] Fluidd install scenario passes on the VM.
- [ ] Expected outcomes check webroot directory and reverse-proxy config.
- [ ] Snapshot revert fixture is robust (wait for SSH, error on revert failure).

## Blocked by

- TODO-008 (PRD #2 - Task 3/5: Remove Klipper and Moonraker scenarios)

## Next task

- TODO-010 (PRD #2 - Task 5/5: Backup, restore, and update scenarios)

## User stories addressed

- User story 3
