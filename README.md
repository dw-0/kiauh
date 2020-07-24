# THIS VERSION IS WORK IN PROGRESS!!!

# KIAUH

## Klipper Installation And Update Helper

![main_menu](https://raw.githubusercontent.com/th33xitus/kiauh/dev-2.0/resources/screenshots/main.png)
![remove_menu](https://raw.githubusercontent.com/th33xitus/kiauh/dev-2.0/resources/screenshots/remove.png)
![update_menu](https://raw.githubusercontent.com/th33xitus/kiauh/dev-2.0/resources/screenshots/update.png)
![advanced_menu](https://raw.githubusercontent.com/th33xitus/kiauh/dev-2.0/resources/screenshots/advanced.png)

## First things first: When you decide to use this script, you use it at your own risk!

Give it a try if you want and if you have suggestions or encounter any problems, please report them to me. 

## Instructions:

If you don't have git already installed on your machine run `sudo apt-get install git -y` to install git first. You will need it anyways!

After you have successfully installed git, use the following commands in the given order to download and execute the script.
Make sure you **don't skip checking out the development branch** if you want to use this new version of the script.

```shell
cd ~
git clone https://github.com/th33xitus/kiauh.git
cd kiauh && git checkout dev-2.0
chmod +x ~/kiauh/kiauh.sh
chmod +x ~/kiauh/scripts/*
./kiauh.sh
```

## Restrictions:

- Tested only on Raspbian Buster Lite
- Prevent simultaneous use of DWC2 and OctoPrint if possible. There have been reports that DWC2 does strange things while the OctoPrint service is running while using    the DWC2 webinterface. The script disables an existing OctoPrint service when installing DWC2. However, the service can also be reactivated with the script!

## Notes:

During the use of this script you will be asked for your sudo password. There are several functions involved which need sudo privileges.

## Functions and Features:

### Core Functions:
- **Install:** Klipper Firmware, dwc2-for-klipper + Duet Web Control, Moonraker + Mainsail, OctoPrint
- **Update:** Klipper Firmware, dwc2-for-klipper + Duet Web Control, Moonraker + Mainsail
- **Backup:** Klipper Firmware, dwc2-for-klipper + Duet Web Control, Moonraker + Mainsail, OctoPrint
- **Remove:** Klipper Firmware, dwc2-for-klipper + Duet Web Control, Moonraker + Mainsail, OctoPrint
- Build Klipper Firmware
- Flash MCU
- Read ID of the currently connected printer (only one at the time)
- Write several entries to your printer.cfg, some of them customizable right in the console
  - Before writing to an existing printer.cfg the script will create a backup! (better safe than sorry!)

### Features:
- Automatic dependency check:
  - If packages are missing on your machine but needed for the asked task, the script will automatically install them
- Switch between Klipper Forks:
  - origin/master, scurve-shaping, scurve-smoothing, moonraker, dev-moonraker
  - The update function of the script will always update the currently selected/active fork!
- Toggle auto-create backups before updating:
  - When enabled, a backup of the installation you want to update is made prior updating
- Preconfigure OctoPrint:
  - When installing OctoPrint, a config is created which preconfigures your installation to be used with Klipper
    - adding the restart/shutdown commands for OctoPrint
    - adding the serial port `/tmp/printer`
    - set the behavior to "Cancel any ongoing prints but stay connected to the printer"
- Enable/Disable OctoPrint Service:
  - Usefull when using DWC2/Mainsail and Octoprint at the same time to prevent them interfering with each other
- Set up reverse proxy for DWC2, Mainsail and OctoPrint and changing the hostname:
  - The script can install and configure Nginx for the selected webinterface. This will allow you to make your webinterface reachable over an URL like `<hostname>.local`
   - Example: If you name the host "mainsail" and set up a reverse proxy, type `mainsail.local` in your webbrowser to open the Mainsail webinterface
  
  tbc ...

## What this script can't do:

- Updating OctoPrint -> Use OctoPrint for updating!
- Setting up webcam related stuff:

  - If you want to use a webcam you have to install the dependencies and configurations yourself. I can't test this stuff sufficient enough due to me not having/using a webcam and therefore it's just too much work for me to set up an installation script which works, at best, with the first try.

    There are install instructions (at least in case of OctoPrint) available:
    [Setting up OctoPrint on a Raspberry Pi running Raspbian](https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspbian/2337)
    (look for "Optional: Webcam")

## Q&A

**_Q: Can i install octoprint with this script?_**

**A:** ~~Soon™~~ Yes :)

**_Q: Can i use this script to install multiple instancec of Klipper on the same Pi? (Multisession?)_**

**A:** No, and at the moment i don't plan to implement this function. For multisession installations take a look at this script manu7irl created: https://github.com/manu7irl/klipper-DWC2-installer . Keep in mind that klipper-DWC2-installer and KIAUH are **NOT** compatible with each other.
