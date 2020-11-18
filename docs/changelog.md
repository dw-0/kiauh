## Changelog

This document covers possible important changes to KIAUH.

### 2020-11-18

* Some changes to Fluidd caused a little rework on how KIAUH will install/update Fluidd from now on. Please see the [fluidd v1.0.0-rc0 release notes](https://github.com/cadriel/fluidd/releases/tag/v1.0.0-rc.0) for further information about what modifications to the moonraker.conf file exactly had to be done. In a nutshell, KIAUH will now always patch the required entries to the moonraker.conf if not already there.

### 2020-10-30:

* The user can now choose to install Klipper as a systemd service.

* The Shell Command extension and `shell_command.py` got renamed to G-Code Shell Command extension and `gcode_shell_command.py`. In case the [pending PR](https://github.com/KevinOConnor/klipper/pull/2173) will be merged in the future, this was an early attempt to dodge possible incompatibilities. The [G-Code Shell Command docs](gcode_shell_command.md) has been updated accordingly.

* The way how KIAUH interacts and writes to the users printer.cfg got changed. Usually KIAUH wrote everything directly into the printer.cfg. The way it will work from now on is, that a new file called `kiauh.cfg` will be created if there is something that needs to be written to the printer.cfg and everything gets written to `kiauh.cfg` instead. The only thing which then gets written to the users printer.cfg is `[include kiauh.cfg]`. This line will be located at the very top of the existing printer.cfg with a little comment as a note. The user can then decide to either keep the `kiauh.cfg` or take its content, places it into the printer.cfg directly and remove the `[include kiauh.cfg]`.

* The `mainsail_macros.cfg` got renamed to `webui_macros.cfg`. Since Mainsail and Fluidd both use the same kind of pause, cancel and resume macros, a more generic name was chosen for the file containing the example macros one can choose to install when installing those webinterfaces.

### 2020-10-10:

* Support for changing the Klipper branch to the moonraker-dev branch from @Arksine has been dropped. Support for Moonraker has been merged into Klipper mainline a long time ago.

* A new function is available from the main menu. You can now upload your log files to http://paste.c-net.org/ to share them for debugging purposes.

### 2020-10-06:

* Fluidd, a new Klipper interface got added to the list of available installers. At the same time some installation routines have changed or have seen some rework. Changes were made to the installation of NGINX configurations. A method was introduced to change the listen port of a webinterface configuration if there is already another webinterface listening on the default port (80).

* At the moment, the Moonraker installer no longer asks you whether you want to install a web interface too. For now you therefore have to install them with their respective installers. Please report any bugs or issues you encounter.

### 2020-09-17:

* The dev-2.0 branch will be abandoned as of today. If you did a checkout to that branch in the past, you have to checkout back to master to receive updates.

### 2020-09-12:

* The old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) won't be supported anymore!\
The is a new, fully rewritten project available: [dwc2-for-klipper-socket](https://github.com/Stephan3/dwc2-for-klipper-socket).\
The installer of this script also got rewritten to make use of that new project. You will not be able to install or remove the old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) with KIAUH anymore if you updated KIAUH to the newest version.
