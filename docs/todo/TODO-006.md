# PRD #2 - Task 1/5: VM inventory, SSH fixture, and safety guards

**Tags:** `task`, `prd-2`

## Parent PRD

PRD #2: Isolated live-system acceptance test strategy on Debian 12 VM (`docs/prd/PRD-002-live-vm-test-strategy.md`)

## What to build

Create the VM inventory config schema (host/IP, SSH user/key, OS family). Implement the SSH connection fixture and the multi-layer safety guards that abort if the target could be the local machine. Write tests for the guards without executing any workflow.

## Acceptance criteria

- [ ] Inventory config schema documented and validated.
- [ ] SSH fixture connects only when target is explicitly allowed.
- [ ] Guards block `localhost`, `127.*`, current hostname, local interfaces, and unknown SSH host keys.
- [ ] Guard tests run on the local machine and prove the blocks work.

## Blocked by

None — can start immediately.

## Next task

- TODO-007 (PRD #2 - Task 2/5: Scenario loader and Klipper install scenario)

## User stories addressed

- User story 5
- User story 6
