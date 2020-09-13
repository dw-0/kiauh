# Feature List:

- Automatic dependency check:
  - If packages are missing but needed for the asked task, the script will automatically install them
- Switch between Klipper Forks:
  - [origin/master](https://github.com/KevinOConnor/klipper/tree/master) or [scurve-shaping](https://github.com/dmbutyugin/klipper/tree/scurve-shaping) or [scurve-smoothing](https://github.com/dmbutyugin/klipper/tree/scurve-smoothing) or [moonraker](https://github.com/Arksine/klipper/tree/dev-moonraker-testing)
  - The update function of the script will always update the currently selected/active fork!
- Toggle auto-create backups before updating:
  - When enabled, a backup of the installation you want to update is made prior updating
- Preconfigure OctoPrint:
  - When installing OctoPrint, a config is created which preconfigures your installation to be used with Klipper
    - adding the restart/shutdown commands for OctoPrint
    - adding the serial port `/tmp/printer`
    - set the behavior to "Cancel any ongoing prints but stay connected to the printer"
- Enable/Disable OctoPrint Service:
  - Usefull when using DWC2/Mainsail and OctoPrint at the same time to prevent them interfering with each other
- Set up reverse proxy for DWC2, Mainsail and OctoPrint and changing the hostname:

  - The script can install and configure Nginx for the selected webinterface. This will allow you to make your webinterface reachable over an URL like `<hostname>.local`
  - Example: If you name the host "mainsail" and set up a reverse proxy, type `mainsail.local` in your webbrowser to open the Mainsail webinterface

- Installing the Shell Command extension. Please see: [Shell Command Extension](https://github.com/th33xitus/kiauh/blob/work-13092020/docs/shell_command.md)
  
  
  to be continued...
