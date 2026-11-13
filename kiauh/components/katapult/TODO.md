# Katapult TODO

## Automated MCU updates (#480)

Done: MCUs flashed with a firmware built from a saved config can be
remembered (`klipper_flashing.py`), and "Update all remembered MCUs" rebuilds
each config once, flashes every MCU with Klipper stopped once, USB to CAN
bridges last, then checks the version each MCU reports to Klipper. Left to do:

- Shipping preset configs for common boards, as suggested in #480, needs a
  maintainer decision first, as KIAUH would have to keep them up to date.
  Esoterical's CANBus guide documents the settings of many boards and could be
  the source.

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
