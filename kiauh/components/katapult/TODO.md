# Katapult TODO

## Automated MCU updates (#480)

Goal: update the Klipper firmware of every MCU with little to no input, by
remembering which firmware config each MCU uses.

- After a successful flash in `flash_with_flashtool()`, offer to remember the
  MCU (CAN UUID or `/dev/serial/by-id` path) together with the Klipper config
  it was built with (`FlashOptions().selected_kconfig`, saved configs live in
  `KLIPPER_KCONFIGS_DIR`). Store the mapping as a small JSON file next to the
  saved configs, so removing them removes the mapping too.
- Add an "Update all MCUs" entry: group the remembered MCUs by config, build
  each config once (`make clean` + `make KCONFIG_CONFIG=...`), then flash its
  MCUs with `run_flashtool()`, keeping Klipper stopped for the whole run like
  the "flash another MCU" loop does.
- Before flashing, compare the MCU in the build's `klipper.dict`
  (`get_klipper_firmware_info()`) with the remembered one, and skip the MCU on a
  mismatch instead of flashing it.
- Flash USB to CAN bridges last: their CAN interface goes down while flashing,
  which would make the following CAN MCUs fail.
- Shipping preset configs for common boards, as suggested in #480, needs a
  maintainer decision first, as KIAUH would have to keep them up to date.

## Multi-instance support

Installing and flashing already work with several Klipper instances, but
flashing stops all of them. Only the instances using the flashed MCU should be
stopped:

- Make `find_canbus_uuids()` also return the instance each UUID was found for,
  and the `canbus_interface` of its `[mcu]` section (Klipper's default is
  `can0`). Use the interface to filter the UUID list by the selected interface.
- For USB and UART targets, match the selected device against the `serial`
  option of the `[mcu]` sections, after resolving symlinks.
- Add `get_affected_instances(target, instances)`: the instances using the MCU,
  plus all instances on the same CAN interface, as flashing a node (and above
  all a USB to CAN bridge) disrupts the whole bus. Fall back to all instances
  when the MCU isn't found in any config, e.g. for a manually entered UUID.
- Pass the result to `stop_klipper_instances_interactively()` and
  `InstanceManager.start_all()` in `flash_with_flashtool()`, and show the
  instance next to each UUID in the selection list.
- A wrong guess makes a print fail, it doesn't brick the MCU: flashtool refuses
  serial devices used by another process, and a Klipper instance losing its CAN
  MCU shuts down.
