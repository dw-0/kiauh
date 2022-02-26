![main_menu](resources/screenshots/kiauh.png)
# Klipper Installation And Update Helper
![GitHub](https://img.shields.io/github/license/th33xitus/kiauh) ![GitHub Repo stars](https://img.shields.io/github/stars/th33xitus/kiauh) ![GitHub forks](https://img.shields.io/github/forks/th33xitus/kiauh) ![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/th33xitus/kiauh) ![GitHub last commit](https://img.shields.io/github/last-commit/th33xitus/kiauh) ![GitHub contributors](https://img.shields.io/github/contributors/th33xitus/kiauh)

### **📋 Please see the [Changelog](docs/changelog.md) for possible important information !**

**📢 Disclaimer: Usage of this script happens at your own risk!**


## **🛠️ Instructions:**

For downloading this script it is necessary to have git installed.\
If you haven't, please run `sudo apt-get install git -y` to install git first.\
After git is installed, use the following commands in the given order to download and execute the script:

```shell
cd ~

git clone https://github.com/th33xitus/kiauh.git

./kiauh/kiauh.sh
```


## **🧰 Functions and Features:**

### **Core Functions:**

- **Installing** Klipper to your Raspberry Pi or other Debian based Linux Distribution.
- **Installing** of the Moonraker API (needed for Mainsail, Fluidd and KlipperScreen)
- **Installing** several web interfaces such as Mainsail, Fluidd, Duet Web Control or OctoPrint including their dependencies.
- **Installing** of KlipperScreen (OctoScreen but for Klipper!)
- **Updating** of all the listed installations above excluding OctoPrint. For updating OctoPrint, please use the OctoPrint interface!
- **Removing** of all the listed installations above.
- **Backup** of all the listed installations above.

### **Also possible:**

- Build the Klipper Firmware
- Flash the MCU
- Read ID of the currently connected MCU
- and more ...

### **For a list of additional features please see: [Feature List](docs/features.md)**

## **❗ Notes:**

- Tested **only** on Raspberry Pi OS Lite (Debian 10 Buster)
    - Other Debian based distributions can work
    - Reported to work on Armbian too
- During the use of this script you might be asked for your sudo password. There are several functions involved which need sudo privileges.

## **🌐 Sources & Further Information**

For more information or instructions to the various components KIAUH can install, please check out the corresponding repositories listed below:

* ⛵[Klipper](https://github.com/Klipper3d/klipper) by [KevinOConnor](https://github.com/KevinOConnor)
* 🌙[Moonraker](https://github.com/Arksine/moonraker) by [Arksine](https://github.com/Arksine)
* 💨[Mainsail](https://github.com/mainsail-crew/mainsail) by [mainsail-crew](https://github.com/mainsail-crew)
* 🌊[Fluidd](https://github.com/fluidd-core/fluidd) by [fluidd-core](https://github.com/fluidd-core)
* 🕸️[Duet Web Control](https://github.com/Duet3D/DuetWebControl) by [Duet3D](https://github.com/Duet3D)
* 🕸️[DWC2-for-Klipper-Socket](https://github.com/Stephan3/dwc2-for-klipper-socket) by [Stephan3](https://github.com/Stephan3)
* 🖥️[KlipperScreen](https://github.com/jordanruthe/KlipperScreen) by [jordanruthe](https://github.com/jordanruthe)
* 🐙[OctoPrint](https://github.com/OctoPrint/OctoPrint) by [OctoPrint](https://github.com/OctoPrint)
* 🔬[PrettyGCode](https://github.com/Kragrathea/pgcode) by [Kragrathea](https://github.com/Kragrathea)
* 🤖[Moonraker-Telegram-Bot](https://github.com/nlef/moonraker-telegram-bot) by [nlef](https://github.com/nlef)

## **Credits**

* A big thank you to [lixxbox](https://github.com/lixxbox) for that awesome KIAUH-Logo!
* Also a big thank you to everyone who supported my work with a [Ko-fi](https://ko-fi.com/th33xitus) !
* Last but not least: Thank you to all contributors and members of the Klipper Community who like and share this project!
