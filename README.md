# THIS VERSION IS WORK IN PROGRESS!!!

# KIAUH

## Klipper Installation And Update Helper

[![kiauh](https://abload.de/img/mobaxterm_personal_207mk20.png)](https://abload.de/image.php?img=mobaxterm_personal_207mk20.png)

This script was actually created for my personal use only but i then decided to make the script accessible for everyone.
~~It is meant to help guiding you through a complete fresh install of Klipper and optionally the DWC2 web UI + DWC2-for-Klipper.
There are also functions for updating your current installations or removing them from your system.~~

## First things first: When you decide to use this script, you use it at your own risk!

Give it a try if you want and if you have suggestions or encounter any problems, please report them. But i can't guarantee that i will fix them immediately (or at all).

## Instructions:

In order to run this script you have to make it executable. Use the following commands in the given order to download and execute the script.
Make sure you don't skip checking out the development branch if you want to use this new version of the script.

```
cd ~
git clone https://github.com/th33xitus/kiauh.git
cd kiauh && git checkout dev-2.0
chmod +x ~/kiauh/kiauh.sh
chmod +x ~/kiauh/scripts/*
./kiauh.sh
```

## Restrictions:

- Tested only on Raspbian Buster Lite
- Prevent simultaneous use of DWC2 and OctoPrint. There have been reports that DWC2 does strange things while the OctoPrint service is running while using the DWC2 web interface. The script disables an existing OctoPrint service when installing DWC2. However, the service can also be reactivated with the script!

## Functions and Features:

- Installing:
  - Klipper
  - dwc2-for-klipper + Duet Web Control
  - Moonraker + Mainsail
  - OctoPrint
- Updating:
  - Klipper
  - dwc2-for-klipper + Duet Web Control
  - Moonraker + Mainsail
- Removing:

  - Klipper
  - dwc2-for-klipper + Duet Web Control
  - Moonraker + Mainsail
  - OctoPrint

- Build Klipper Firmware
- Flash MCU
- Read ID of currently connected printer
- Write several entries to your printer.cfg, some of them customizable right in the console
- Switch between Klipper Forks:
  - scurve-shaping
  - scurve-smoothing
  - moonraker
  - dev-moonraker
- Toggle auto-create backups before updating
- Toggle OctoPrint Service (usefull when using DWC2/Mainsail and Octoprint at the same time)

- Set up reverse proxy for Mainsail/OctoPrint
  
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
