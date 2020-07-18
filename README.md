# KIAUH

## Klipper Installation And Update Helper

This script was actually created for my personal use only but i then decided to make the script accessible for everyone.
It is meant to help guiding you through a complete fresh install of Klipper and optionally the DWC2 web UI + DWC2-for-Klipper.
There are also functions for updating your current installations or removing them from your system.

## First things first: When you decide to use this script, you use it at your own risk!

Although i implemented backup-functions for pretty much everything and tested this script extensively with my available (yet limited) hardware before releasing it, it doesn't mean that it will work 100% perfect for everyone out there. Please keep that in mind!

Give it a try if you want and if you have suggestions or encounter any problems, please report them. But i can't guarantee that i will fix them immediately (or at all).

[![kiauh](https://abload.de/img/putty_20-05-22_18-49-1nkaa.png)](https://abload.de/image.php?img=putty_20-05-22_18-49-1nkaa.png)

## Instructions:
If you don't have git already installed, please install it first:
`sudo apt-get install git -y`

After you made sure to have git installed, use the following commands in the given order to download and execute the script.
```
cd ~
git clone https://github.com/th33xitus/kiauh.git
cd ~/kiauh
chmod +x kiauh.sh
./kiauh.sh
```

## Restrictions:
* Tested only on Raspbian Buster Lite

## Functions and features:
* Install Klipper + DWC2-for-klipper + DWC2 from scratch
* Check the status of your installations
* Update, backup and remove existing installations
* Building firmware
* Flashing firmware to your MCU
* Grabbing the printer-ID of your connected printer
* Writing the printer-ID to your printer.cfg
* Writing the DWC2-for-Klipper example config to your printer.cfg



## Q&A

__*Q: Can i install octoprint with this script?*__

**A:** No, and i don't plan to implement this function


__*Q: Can i use this script to install multiple instancec of Klipper on the same Pi? (Multisession?)*__

 **A:** No, and at the moment i don't plan to implement this function. For multisession installations take a look at this script manu7irl created: https://github.com/manu7irl/klipper-DWC2-installer
 
