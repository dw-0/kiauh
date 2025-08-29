# Raspberry Pi Setup

This guide will help you set up a Raspberry Pi for running Klipper and other,
Klipper related 3D printing software. In case you are using a different single-board
computer (SBC), please refer to the manufacturer's instructions for installing
a compatible version of Linux on your device.

It is assumed that you have at least a Raspberry Pi 3 or newer, along with a
microSD card (at least 8GB, preferably 16GB or more) and a power supply.
Additionally, you will need a computer with an SD card reader to prepare
the microSD card.

KIAUH requires a Linux operating system that has already been flashed to your
Raspberry Pi's (or other SBC's) microSD card. As a result, you must ensure that you
already have a functional Linux system on hand before you can proceed with
installing KIAUH. `Raspberry Pi OS Lite` (either 32bit or 64bit) is a recommended Linux image
if you are using a Raspberry Pi.

---

To flash `Raspberry Pi OS Lite` to your microSD card using the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/),
follow the steps below. If you encounter any issues or need further assistance, please refer to the [official Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html).

1. Open the Raspberry Pi Imager application on your computer.
2. Click on `Choose OS` and select `Raspberry Pi OS (other)`.
   ![OS selection](https://raw.githubusercontent.com/dw-0/kiauh/master/resources/screenshots/rpi_imager1.png)
3. Choose `Raspberry Pi OS Lite (32bit)` (or 64bit if desired).
   ![Lite selection](https://raw.githubusercontent.com/dw-0/kiauh/master/resources/screenshots/rpi_imager2.png)
4. Insert the microSD card into your computer's SD card reader.
5. In the main menu of the Imager, select the correct microSD card.
6. Click the gear icon at the bottom left of the main menu to open advanced options.
7. Enable SSH and enter your Wi-Fi credentials.

    !!! info
        Wi-Fi is only necessary if you want to connect to your Raspberry Pi over a wireless network. If you plan to use a wired Ethernet connection, you can skip this step. SSH is required for remote access to your Raspberry Pi, so make sure to enable it.

8. Click `Save` to close the advanced options menu.
9. Click `Write` to start flashing the image to the microSD card.

    !!! warning
        All data on the microSD card will be overwritten!

10. Once the flashing process is complete, safely eject the microSD card from your computer.
11. Insert the microSD card into your Raspberry Pi.
12. Connect your Raspberry Pi to a power source to boot it up.
13. Wait for a few minutes to allow the Raspberry Pi to complete its initial setup.
14. You can now connect to your Raspberry Pi via SSH using the IP address assigned by your router. The default username is `pi` and the default password is `raspberry`.

If you successfully connected to your Raspberry Pi via SSH, you can proceed to install KIAUH by following the instructions in the [Installation Guide](installation.md).
