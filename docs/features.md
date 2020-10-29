# Feature List:

- **Automatic dependency check:**\
If packages are missing but needed for the asked task, the script will automatically install them
- **Switch between different Klipper Forks:**\
[origin/master](https://github.com/KevinOConnor/klipper/tree/master) or [scurve-shaping](https://github.com/dmbutyugin/klipper/tree/scurve-shaping) or [scurve-smoothing](https://github.com/dmbutyugin/klipper/tree/scurve-smoothing)\
The update function of the script will always update the currently selected/active fork!
- **Toggle auto-create backups before updating:**\
When enabled, a backup of the installation you want to update is made prior updating
- **Rollback:**\
When updating Klipper, KIAUH saves the current commit hash to a local ini-file. In case of an unsuccesfull update you can use this function to quickly revert back to the commit with the hash you updated from.
- **Preconfigure OctoPrint:**\
When installing OctoPrint, a config is created which preconfigures your installation to be used with Klipper.\
That means:
  - adding the restart/shutdown commands for OctoPrint
  - adding the serial port `/tmp/printer`
  - set the behavior to "Cancel any ongoing prints but stay connected to the printer"
- **Enable/Disable OctoPrint Service:**\
Usefull when using DWC2/Mainsail/Fluidd and OctoPrint at the same time to prevent them interfering with each other
- **Set up reverse proxy for DWC2, Mainsail, Fluidd and OctoPrint and changing the hostname:**
  - The script can install and configure Nginx for the selected webinterface
  - It also allows you to make your webinterface reachable over an URL like `<hostname>.local` via avahi
    - Example: If you name the host "my-printer", type `my-printer.local` in your webbrowser to open the installed webinterface
    - If there is more than one webinterface installed, you have to append the port to that adress

- **Installing a G-Code Shell Command extension:**\
For further information about that extension please see the  [G-Code Shell Command Extension Doc](gcode_shell_command.md)

- **Uploading logfiles:**\
You can directly upload logfiles like klippy.log, moonraker.log and dwc2.log from the KIAUH main menu for providing them for troubleshooting purposes.


to be continued...
