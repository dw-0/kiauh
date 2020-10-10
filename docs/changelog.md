## Changelog

This document covers possible important changes to KIAUH.

### 2020-10-10:

Support for changing the Klipper branch to the moonraker-dev branch from @Arksine has been dropped. Support for Moonraker has been merged into Klipper mainline a long time ago.

A new function is available from the main menu. You can now upload your log files to http://paste.c-net.org/ to share them for debugging purposes.

### 2020-10-06:

Fluidd, a new Klipper interface got added to the list of available installers. At the same time some installation routines have changed or have seen some rework. Changes were made to the installation of NGINX configurations. A method was introduced to change the listen port of a webinterface configuration if there is already another webinterface listening on the default port (80).\
At the moment, the Moonraker installer no longer asks you whether you want to install a web interface too. For now you therefore have to install them with their respective installers. Please report any bugs or issues you encounter.

### 2020-09-17:

The dev-2.0 branch will be abandoned as of today. If you did a checkout to that branch in the past, you have to checkout back to master to receive updates.

### 2020-09-12:

The old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) won't be supported anymore!

The is a new, fully rewritten project available: [dwc2-for-klipper-socket](https://github.com/Stephan3/dwc2-for-klipper-socket).

The installer of this script also got rewritten to make use of that new project. You will not be able to install or remove the old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) with KIAUH anymore if you updated KIAUH to the newest version.
