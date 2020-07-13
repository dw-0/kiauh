# THIS VERSION IS WORK IN PROGRESS!!! 

# KIAUH

## Klipper Installation And Update Helper

[![kiauh](https://abload.de/img/mobaxterm_personal_207mk20.png)](https://abload.de/image.php?img=mobaxterm_personal_207mk20.png)

This script was actually created for my personal use only but i then decided to make the script accessible for everyone.
It is meant to help guiding you through a complete fresh install of Klipper and optionally the DWC2 web UI + DWC2-for-Klipper.
There are also functions for updating your current installations or removing them from your system.

## First things first: When you decide to use this script, you use it at your own risk!

Give it a try if you want and if you have suggestions or encounter any problems, please report them. But i can't guarantee that i will fix them immediately (or at all).

## Instructions:

In order to run this script you have to make it executable. Use the following commands in the given order to download and execute the script.

```
cd ~
git clone https://github.com/th33xitus/kiauh.git
cd kiauh && git checkout dev-2.0
chmod +x ~/kiauh/kiauh.sh
chmod +x ~/kiauh/scripts/*
./kiauh.sh
```

## Restrictions:
* Tested only on Raspbian Buster Lite

## Functions and Features:
Soon™


## Q&A

__*Q: Can i install octoprint with this script?*__

**A:** Soon™


__*Q: Can i use this script to install multiple instancec of Klipper on the same Pi? (Multisession?)*__

 **A:** No, and at the moment i don't plan to implement this function. For multisession installations take a look at this script manu7irl created: https://github.com/manu7irl/klipper-DWC2-installer
