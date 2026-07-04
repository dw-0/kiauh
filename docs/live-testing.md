# Live System Testing

Live tests run KIAUH workflows against a real Debian 12 QEMU/KVM VM. They are
isolated from the local developer machine by design.

## Safety Rules

- Live tests NEVER run on the local machine.
- They require `KIAUH_LIVE_ALLOW=1`.
- The target host must be explicitly set via `KIAUH_LIVE_TARGET_HOST` and match
the VM in the inventory.
- Local hostnames, loopback addresses, and the current hostname are blocked.

## Prepare a VM

1. Create a Debian 12 QEMU/KVM VM.
2. Create a user with passwordless sudo.
3. Install an SSH key for that user.
4. Install KIAUH on the VM (e.g. clone this repository).
5. Create a clean snapshot named `clean`:
   ```bash
   virsh snapshot-create-as debian12-kiauh clean
   ```

## Inventory

`kiauh/live/inventory.yaml` defines non-sensitive VM settings. The host and SSH
key path are read from environment variables or a `.env` file so they are not
committed.

Create `.env` in the project root:

```bash
KIAUH_LIVE_DEBIAN12_KIAUH_HOST=192.168.122.10
KIAUH_LIVE_DEBIAN12_KIAUH_KEY_FILE=/home/you/.ssh/kiauh_vm
```

Variable naming: `KIAUH_LIVE_<VM_NAME>_HOST` and `KIAUH_LIVE_<VM_NAME>_KEY_FILE`,
with the VM name uppercased and hyphens replaced by underscores.

You can also point to a custom inventory file:

```bash
export KIAUH_LIVE_INVENTORY=/path/to/inventory.yaml
```

## Run Live Tests

```bash
export KIAUH_LIVE_ALLOW=1
export KIAUH_LIVE_TARGET_HOST=192.168.122.10
pytest -m live
```

Each scenario reverts the VM to the clean snapshot first, so scenarios are
independent.

## Add a Scenario

Create a YAML file in `kiauh/live/scenarios/`:

```yaml
name: Install Klipper on Debian 12
vm: debian12-kiauh
os: debian-12
steps:
  - command: ["kiauh", "install", "klipper", "--count", "1"]
    timeout: 600
expected:
  - type: service
    name: klipper.service
    state: running
```

Supported assertion types: `service`, `file`, `package`, `port`, `command`.

## Troubleshooting

- `UnsafeTargetError`: check `KIAUH_LIVE_ALLOW` and `KIAUH_LIVE_TARGET_HOST`.
- `InventoryError`: check the inventory YAML path and format.
- `LiveRunnerError` during snapshot revert: ensure `virsh` works and the domain
  and snapshot names match the inventory.
