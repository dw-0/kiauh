# PRD #2 - Task 5/5: Backup, restore, and update scenarios

**Tags:** `task`, `prd-2`

## Parent PRD

PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM (`docs/prd/PRD-002-live-vm-test-strategy.md`)

## What to build

Add backup/restore and update scenarios. Document the live test runbook: how to prepare the VM, set inventory, run scenarios, and read results. Ensure the whole live suite can be executed in one command.

## Acceptance criteria

- [ ] Backup scenario creates an archive with expected content.
- [ ] Restore scenario returns config files to expected state.
- [ ] Update scenario changes a component version/config observable on the VM.
- [ ] Runbook `docs/live-testing.md` covers VM setup, inventory, execution, and troubleshooting.
- [ ] Full `pytest -m live` run completes end-to-end.

## Blocked by

- TODO-009 (PRD #2 - Task 4/5: Mainsail and Fluidd install scenarios)

## Next task

None — this is the last task.

## User stories addressed

- User story 4
- User story 7
