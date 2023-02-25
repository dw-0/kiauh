<p align="center">
  <a>
    <img src="https://raw.githubusercontent.com/th33xitus/kiauh/master/resources/screenshots/kiauh.png" alt="KIAUH logo" height="181">
    <h1 align="center">Klipper Installation And Update Helper</h1>
  </a>
</p>

<p align="center">
  A handy installation script that makes installing Klipper (and more) a breeze!
</p>

<p align="center">
  <a><img src="https://img.shields.io/github/license/th33xitus/kiauh"></a>
  <a><img src="https://img.shields.io/github/stars/th33xitus/kiauh"></a>
  <a><img src="https://img.shields.io/github/forks/th33xitus/kiauh"></a>
  <a><img src="https://img.shields.io/github/languages/top/th33xitus/kiauh?logo=gnubash&logoColor=white"></a>
  <a><img src="https://img.shields.io/github/v/tag/th33xitus/kiauh"></a>
  <br />
  <a><img src="https://img.shields.io/github/last-commit/th33xitus/kiauh"></a>
  <a><img src="https://img.shields.io/github/contributors/th33xitus/kiauh"></a>
</p>

## **🛠️ Instructions:**

### Prerequisites
KIAUH is a script that helps you to install Klipper on a Linux Operating System that has
already been flashed to the SD card of your Raspberry Pi (or other SBC). So you need to make sure to have
a working Linux system available. A recommended Linux image (in case you are using a Raspberry Pi) is
`Raspberry Pi OS Lite (32bit)`. The easiest way to flash an image like this to an SD card is by using the
[official Raspberry Pi Imager](https://www.raspberrypi.com/software/).

* Once you downloaded, installed and launched the Raspberry Pi Imager 
select the `Choose OS` option and then `Raspberry Pi OS (other)`: \
![](resources/screenshots/rpi_imager1.png)

* Then select `Raspberry Pi OS Lite (32bit)`:
![](resources/screenshots/rpi_imager2.png)

* Back in the main menu of the Raspberry Pi Imager select the corresponding SD card you want to
flash the image to.

* Also make sure to go into the Advaced Option (the cog icon in the lower left corner)
and enable SSH and configure Wi-Fi.

* If you need more help for using the Raspberry Pi Imager, consider 
visiting the [official documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html).

These steps only apply if you are actually using a Raspberry Pi. In case you want 
to use a different SBC, please find out how to get an appropriate Linux image flashed 
to the SD card before proceeding further. Also make sure that KIAUH will be able to run 
and operate on the Linux Distribution you are going to flash. Read the Notes 
further down in this document.

### Download and use KIAUH
**📢 Disclaimer: Usage of this script happens at your own risk!**

* **Step 1:** \
To download this script, it is necessary to have git installed. If you don't have git already installed, or if you are unsure, run the following command:
```shell
sudo apt-get install git -y
```

* **Step 2:** \
Once git is installed, use the following commands in the given order to download and execute the script:

```shell
cd ~

git clone https://github.com/th33xitus/kiauh.git

./kiauh/kiauh.sh
```

* **Step 3:** \
You should find yourself in the main menu of KIAUH. You will see several options you can choose 
from depending on what you want to do. For choosing an option, type the corresponding number into the "Perform action" prompt.


## **❗ Notes:**

**📋 Please see the [Changelog](docs/changelog.md) for possible important changes!**

- Mainly tested on Raspberry Pi OS Lite (Debian 10 Buster / Debian 11 Bullseye)
    - Other Debian based distributions (like Ubuntu 20 to 22) likely work too
    - Reported to work on Armbian as well
- During the use of this script you will be asked for your sudo password. There are several functions involved which need sudo privileges.

## **🌐 Sources & Further Information**

<table>
<tr>
<th><h3><a href="https://github.com/Klipper3d/klipper">Klipper</a></h3></th>
<th><h3><a href="https://github.com/Arksine/moonraker">Moonraker</a></h3></th>
<th><h3><a href="https://github.com/mainsail-crew/mainsail">Mainsail</a></h3></th>
</tr>
<tr>
<th><img src="https://raw.githubusercontent.com/Klipper3d/klipper/master/docs/img/klipper-logo.png" alt="Klipper Logo" height="64"></th>
<th><img src="https://avatars.githubusercontent.com/u/9563098?v=4" alt="Arksine avatar" height="64"></th>
<th><img src="https://raw.githubusercontent.com/mainsail-crew/docs/master/assets/img/logo.png" alt="Mainsail Logo" height="64"></th>
</tr>
<tr>
<th>by <a href="https://github.com/KevinOConnor">KevinOConnor</a></th>
<th>by <a href="https://github.com/Arksine">Arksine</a></th>
<th>by <a href="https://github.com/mainsail-crew">mainsail-crew</a></th>
</tr>
<tr>
<th><h3><a href="https://github.com/fluidd-core/fluidd">Fluidd</a></h3></th>
<th><h3><a href="https://github.com/jordanruthe/KlipperScreen">KlipperScreen</a></h3></th>
<th><h3><a href="https://github.com/OctoPrint/OctoPrint">OctoPrint</a></h3></th>
</tr>
<tr>
<th><img src="https://raw.githubusercontent.com/fluidd-core/fluidd/master/docs/assets/images/logo.svg" alt="Fluidd Logo" height="64"></th>
<th><img src="https://avatars.githubusercontent.com/u/31575189?v=4" alt="jordanruthe avatar" height="64"></th>
<th><img src="https://camo.githubusercontent.com/627be7fc67195b626b298af9b9677d7c58e698c67305e54324cffbe06130d4a4/68747470733a2f2f6f63746f7072696e742e6f72672f6173736574732f696d672f6c6f676f2e706e67" alt="OctoPrint Logo" height="64"></th>
</tr>
<tr>
<th>by <a href="https://github.com/fluidd-core">fluidd-core</a></th>
<th>by <a href="https://github.com/jordanruthe">jordanruthe</a></th>
<th>by <a href="https://github.com/OctoPrint">OctoPrint</a></th>
</tr>

<tr>
<th><h3><a href="https://github.com/nlef/moonraker-telegram-bot">Moonraker-Telegram-Bot</a></h3></th>
<th><h3><a href="https://github.com/Kragrathea/pgcode">PrettyGCode for Klipper</a></h3></th>
<th><h3><a href="https://github.com/TheSpaghettiDetective/moonraker-obico">Obico for Klipper</a></h3></th>
</tr>

<tr>
<th><img src="https://avatars.githubusercontent.com/u/52351624?v=4" alt="nlef avatar" height="64"></th>
<th><img src="https://avatars.githubusercontent.com/u/5917231?v=4" alt="Kragrathea avatar" height="64"></th>
<th><img src="https://avatars.githubusercontent.com/u/46323662?s=200&v=4" alt="Obico logo" height="64"></th>
</tr>

<tr>
<th>by <a href="https://github.com/nlef">nlef</a></th>
<th>by <a href="https://github.com/Kragrathea">Kragrathea</a></th>
<th>by <a href="https://github.com/TheSpaghettiDetective">Obico</a></th>
</tr>

<tr>
<th><h3></h3></th>
<th><h3><a href="https://octoeverywhere.com/?source=kiauh_readme">OctoEverywhere For Klipper</a></h3></th>
<th><h3></h3></th>
</tr>

<tr>
<th></th>
<th><a href="https://octoeverywhere.com/?source=kiauh_readme"><img src="https://octoeverywhere.com/img/logo.svg" alt="OctoEverywhere Logo" height="64"></a></th>
<th></th>
</tr>

<tr>
<th></th>
<th>by <a href="https://github.com/QuinnDamerell">Quinn Damerell</a></th>
<th></th>
</tr>

</table>

## **Credits**

* A big thank you to [lixxbox](https://github.com/lixxbox) for that awesome KIAUH-Logo!
* Also a big thank you to everyone who supported my work with a [Ko-fi](https://ko-fi.com/th33xitus) !
* Last but not least: Thank you to all contributors and members of the Klipper Community who like and share this project!
