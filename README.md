# KIAUH - Klipper Installation And Update Helper

### ( This script is always work in progress! )

![main_menu](https://raw.githubusercontent.com/th33xitus/kiauh/dev-2.0/resources/screenshots/main.png)

---

## Disclaimer: Usage of this script happens at your own risk!

This script is "only" a helping hand for you to get set up in a fast and most comfortable way.

**This does not mean, it will relieve you of using brain.exe!**

Feel free to give it a try if you want. If you have suggestions or encounter any problems, please report them.

---

## Instructions:

For downloading this script it is best to have git already installed.
If you haven't, please run `sudo apt-get install git -y` to install git first. You will need it anyways!

After git is installed, use the following commands in the given order to download and execute the script.

```shell
cd ~
git clone https://github.com/th33xitus/kiauh.git
cd kiauh
chmod +x kiauh.sh scripts/*
./kiauh.sh
```

---

## Functions and Features:

### Core Functions:

- **Installing** of the Klipper Firmware to your Raspberry Pi or other Linux Distribution which makes use of init.d.
- **Installing** of several different web interfaces such as Duet Web Control, Mainsail or OctoPrint including their dependencies.
- **Installing** of the Moonraker API 
- **Updating** of all the listed installations above excluding OctoPrint. For updating OctoPrint, please use the OctoPrint interface!
- **Removing** of all the listed installations above.
- **Backup** of all the listed installations above.

What also is possible:
- Build the Klipper Firmware
- Flash the MCU 
- Read ID of the currently connected printer (only one at the time)
- Write necessary entries to your printer.cfg, some of them customizable right in the CLI.

For a list of additional features and their descriptions please see:
[Feature List](https://github.com/th33xitus/kiauh/edit/work-13092020/docs/features.md)

---

## Notes:

- Tested only on Raspbian Buster Lite
- During the use of this script you will be asked for your sudo password. There are several functions involved which need sudo privileges.
- Prevent simultaneous use of DWC2 and OctoPrint if possible. There have been reports that DWC2 does strange things while the OctoPrint service is running while using the DWC2 webinterface. The script disables an existing OctoPrint service when installing DWC2. However, the service can also be reactivated with the script!
- If you used Mainsail v0.0.12 before and you want to upgrade to v0.1.0 or later, you have to reinstall Moonraker as well! Mainsail v0.1.0 will not work with the old Moonraker service. Don't worry, the script can handle the proper removal of the old version.

---

### For more information or instructions, please check out the appropriate repositories listed below:

Klipper by [KevinOConnor](https://github.com/KevinOConnor) :

- https://github.com/KevinOConnor/klipper

Klipper S-Curve fork by [dmbutyugin](https://github.com/dmbutyugin) :

- https://github.com/dmbutyugin/klipper/tree/scurve-smoothing
- https://github.com/dmbutyugin/klipper/tree/scurve-shaping

Moonraker by [Arksine](https://github.com/Arksine) :

- https://github.com/Arksine/moonraker

Mainsail Webinterface by [meteyou](https://github.com/meteyou) :

- https://github.com/meteyou/mainsail

Duet Web Control by [Duet3D](https://github.com/Duet3D) :

- https://github.com/Duet3D/DuetWebControl

DWC2-for-Klipper-Socket by [Stephan3](https://github.com/Stephan3) :

- https://github.com/Stephan3/dwc2-for-klipper-socket

OctoPrint Webinterface by [OctoPrint](https://github.com/OctoPrint) :

- https://octoprint.org
- https://github.com/OctoPrint/OctoPrint

---

## Q&A

**_Q: Can i use this script to install multiple instancec of Klipper on the same Pi? (Multisession?)_**

**A:** No, and at the moment i don't plan to implement this function. For multisession installations take a look at this script manu7irl created: https://github.com/manu7irl/klipper-DWC2-installer . Keep in mind that klipper-DWC2-installer and KIAUH are **NOT** compatible with each other.
