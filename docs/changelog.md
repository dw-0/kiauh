## Changelog

This document covers possible important changes to KIAUH.

### 2023-02-03
The installer for MJPG-Streamer got replaced by crowsnest. It is an improved webcam service, utilizing ustreamer. 
Please have a look here for additional info about crowsnest and how to configure it: https://github.com/mainsail-crew/crowsnest \
It's unsure if the previous MJPG-Streamer installer will be updated and make its way back into KIAUH.
A big thanks to [KwadFan](https://github.com/KwadFan) for writing the crowsnest implementation.

### 2022-10-31
Some functions got updated, though not all of them.

The following functions are still currently unavailable:
- Installation of: MJPG-Streamer
- All backup functions and the Log-Upload

### 2022-10-20
KIAUH has now reached major version 5 !

Recently Moonraker introduced some changes which makes it necessary to change the folder structure of printer setups.
If you are interested in the details, check out this PR: https://github.com/Arksine/moonraker/pull/491 \
Although Moonraker has some mechanics available to migrate existing setups to the new file structure with the use of symlinks, fresh and clean installs
should be considered.

The version jump of KIAUH to v5 is a breaking change due to those major changes! That means v4 and v5 are not compatible with each other!
This is also the reason why you will currently be greeted by a yellow notification in the main menu of KIAUH leading to this changelog.
I decided to disable a few functions of the script and focus on releasing the required changes to the core components of this script.
I will work on updating the other parts of the script piece by piece during the next days/weeks.
So I am already sorry in advance if one of your desired components you wanted to install or use temporarily cannot be installed or used right now.

The following functions are currently unavailable:
- Installation of: KlipperScreen, Obico, Octoprint, MJPG-Streamer, Telegram Bot and PrettyGCode
- All backup functions and the Log-Upload

**So what is working?**\
Installation of Klipper, Moonraker, Mainsail and Fluidd. Both, single and multi-instance setups work!\
As already said, the rest will follow in the near future. Updating and removal of already installed components should continue to work.

**What was removed?**\
The option to change Klippers configuration directory got removed. From now on it will not be possible anymore to change
the configuration directory from within KIAUH and the new filestructure is enforced.

**What if I don't have an existing Klipper/Moonraker install right now?**\
Nothing important to think about, install Klipper and Moonraker. KIAUH will install both of them with the new filestructure.

**What if I have an existing Klipper/Moonraker install?**\
First of all: Backups! Please copy all of your config files and the Moonraker database (it is a hidden folder, usually `~/.moonraker_database`) to a safe location.
After that, uninstall Klipper and Moonraker with KIAUH. You can then proceed and re-install both of them with KIAUH again. It is important that you are on KIAUH v5 for that!
Once everything is installed again, you need to manually copy your configuration files from the old `~/klipper_config` folder to the new `~/printer_data/config` folder.
Previous, by Moonraker created symlinks to folder of the old filestructure will not work anymore, you need to move the files to their new location now!
Do the same with the two files inside of `~/.moonraker_database`. Move/copy them into `~/printer_data/database`. If `~/printer_data/database` is already populated with a `data.mdb` and `lock.mdb`
delete them or simply overwrite them. Nothing should be lost as those should be empty database files. Anyway, you made backups, right?
You can now proceed and restart Moonraker. Either from within Mainsail or Fluidd, or use SSH and execute `sudo systemctl restart moonraker`.
If everything went smooth, you should be good to go again. If you see some Moonraker warnings about deprecated options in the `moonraker.conf`, go ahead and resolve them.
I will not cover them in detail here. A good source is the Moonraker documentation: https://moonraker.readthedocs.io/en/latest/configuration/

**What if I have an existing Klipper/Moonraker multi-instance install?**\
Pretty much the same steps that are required for single instance installs apply to multi-instance setups. So please go ahead and read the previous paragraph if you didn't already.
Make backups of everything first. Then remove and install the desired amount of Klipper and Moonraker instances again.
Now you need to move all config and database files to their new locations.\
Example with an instance called `printer_1`:\
The config files go from `~/klipper_config/printer_1` to `~/printer_1_data/config`.
The database files go from `~/.moonraker_database_1` to `~/printer_1_data/database`.
Now restart all Moonraker services. You can restart all of them at once if you launch KIAUH, and in the main menu type `restart moonraker` and hit Enter.

I hope I have covered the most important things. In case you need further support, the official Klipper Discord is a good place to ask for help.

### 2022-08-15
Support for "Obico for Klipper" was added! Huge thanks to [kennethjiang](https://github.com/kennethjiang) for helping me with the implementation!

### 2022-05-29
KIAUH has now reached major version 4 !
* feat: Klipper can be installed under Python3 (still considered as experimental)
* feat: Klipper can be installed from custom repositories / inofficial forks
* feat: Custom instance name for multi instance installations of Klipper
  * Any other multi instance will share the same name given to the corresponding Klipper instance
  * E.g. klipper-voron2 -> moonraker-voron2 -> moonraker-telegram-bot-voron2
* feat: Option to allow installation of / updating to unstable Mainsail and Fluidd versions
  * by default only stable versions get installed/updated
* feat: Multi-Instance OctoPrint installations now each have their own virtual python environment
  * allows independent installation of plugins for each instance
* feat: Implementing the use of shellcheck during development
* feat: Implementing a simple logging mechanic
* feat: Log-upload function now also allows uploading other logfiles (kiauh.log, webcamd.log etc.)
* feat: added several new help dialogs which try to explain various functions
* fix: During Klipper installation, checks for group membership of `tty` and `dialout` are made
* refactor: rework of the settings menu for better control the new KIAUH features
* refactor: Support for DWC and DWC-for-Klipper has been removed
* refactor: The backup before update settings were moved to the KIAUH settings menu
* refactor: Switch branch function has been removed (was replaced by the custom Klipper repo feature)
* refactor: The update manager sections for Mainsail, Fluidd and KlipperScreen were removed from the moonraker.conf template
  * They will now be individually added during installation of the corresponding interface
* refactor: The rollback function was reworked and now also allows rollbacks of Moonraker
  * It now takes numerical inputs and reverts the corresponding repository by the given amount instead
  * KIAUH does not save previous states to its config anymore like it did with the previous approach


### 2022-01-29
* Starting from the 28th of January, Moonraker can make use of PackageKit and PolicyKit.\
More details on that can be found [here](
https://github.com/Arksine/moonraker/issues/349) and [here](https://github.com/Arksine/moonraker/pull/346)
* KIAUH will install Moonrakers PolicyKit rules by default when __installing__ Moonraker
* KIAUH will also install Moonrakers PolicyKit rules when __updating__ Moonraker __via KIAUH__ as of now

### 2021-12-30
* Updated the doc for the usage of the [G-Code Shell Command Extension](docs/gcode_shell_command.md)
* It became apparent, that some user groups are missing on some systems. A missing video group \
membership for example caused issues when installing mjpg-streamer while not using the default pi user. \
Other issues could occur when trying to flash an MCU on Debian or Ubuntu distributions where a user might not be part
of the dialout group by default. A check for the tty group is also done. The tty group is needed for setting
up a linux MCU (currently not yet supported by KIAUH).
* There is an issue when trying to install Mainsail or Fluidd on Ubuntu 21.10. Permissions on that distro seem to have seen a rework 
 in comparison to 20.04 and users will be greeted with an "Error 403 - Permission denied" message after installing one of Klippers webinterfaces.
I still have to figure out a viable solution for that.

### 2021-09-28
* New Feature! Added an installer for the Telegram Bot for Moonraker by [nlef](https://github.com/nlef).
Checkout his project! Remember to report all issues and/or bugs regarding that project in its corresponding repo and not here 😛.\
You can find it here: https://github.com/nlef/moonraker-telegram-bot

### 2021-09-24
* The flashing function got adjusted a bit. It is now possible to also flash controllers which are connected over UART and thus accessible via `/dev/ttyAMA0`. You now have to select a connection methop prior flashing which is either USB or UART.
* Due to several requests over time I have now created a Ko-fi account for those who want to support this project and my work with a small donation. Many thanks in advance to all future donors. You can support me on Ko-fi with this link: https://ko-fi.com/th33xitus
* As usual, if you find any bugs or issues please report them. I tested the little rework i did with the hardware i have available and haven't encountered any malfunctions of flashing them yet.

### 2021-08-10
* KIAUH now supports the installation of the "PrettyGCode for Klipper" GCode-Viewer created by [Kragrathea](https://github.com/Kragrathea)! Installation, updating and removal are possible with KIAUH. For more details to this cool piece of software, please have a look here: https://github.com/Kragrathea/pgcode

### 2021-07-10
* The NGINX configuration files got updated to be in sync with MainsailOS and FluiddPi. Issues with the NGINX service not starting up due to wrong configuration should be resolved now. To get the updated configuration files, please remove Moonraker and Mainsail / Fluidd with KIAUH first and then re-install it. An automated file check for those configuration files might follow in the future which then automates updating those files if there were important changes.

* The default `moonraker.conf` was updated to reflect the recent changes to the update manager section. The update channel is set to `dev`.

### 2021-06-29
* KIAUH will now patch the new `log_path` to existing moonraker.conf files when updating Moonraker and the entry is missing. Before that, it was necessary that the user provided that path manually to make Fluidd display the logfiles in its interface. This issue should be resolved now.

### 2021-06-15

* Moonraker introduced an optional `log_path` which clients can make use of to show log files located in that folder to their users. More info here: https://github.com/Arksine/moonraker/commit/829b3a4ee80579af35dd64a37ccc092a1f67682a \
Client developers agreed upon using `~/klipper_logs` as the new default log path.\
That means, from now on, Klipper and Moonraker services installed with KIAUH will place their logfiles in that mentioned folder.
* Additionally, KIAUH will now detect Klipper and Moonraker systemd services that still use the old default location of `/tmp/<service>.log` and will update them next time the user updates Klipper and/or Moonraker with the KIAUH update function.
* Additional symlinks for the following logfiles will get created along those update procedures to make them accessible through the webinterface once its supported:
    - webcamd.log
    - mainsail-access.log
    - mainsail-error.log
    - fluidd-access.log
    - fluidd-error.log
* For MainsailOS and FluiddPi users:\
MainsailOS and FluiddPi will switch the shipped Klipper service from SysVinit to systemd probably with their next release. KIAUH can already help migrate older MainsailOS (0.4.0 and below) and FluiddPi (v1.13.0) releases to match their new service-, file- and folder-structure so you don't have to re-flash the SD-Card of your Raspberry Pi.\
In detail here is what is going to happen when you use the new "CustomPiOS Migration Helper" from the Advanced Menu\
`(Main Menu -> 4 -> Enter -> 10 -> Enter)` in a short summary:
    * The Klipper SysVinit service will get replaced by a Klipper systemd service
    * Klipper and Moonraker will use the new log-directory `~/klipper_logs`
    * The webcamd service gets updated
    * The webcamd script gets updated and moved from `/root/bin/webcamd` to `/usr/local/bin/webcamd`
    * The NGINX `upstreams.conf` gets updated to be able to configure up to 4 webcams
    * The `mainsail.txt` / `fluiddpi.txt` gets moved from `/boot` to `~/klipper_config` and renamed to `webcam.txt`
    * Symlinks for the webcamd.log and various NGINX logs get created in `~/klipper_config`
    * Configuration files for Klipper, Moonraker and webcamd get added to `/etc/logrotate.d`
    * If they still exist, two lines will be removed from the mainsail.cfg or client_macros.cfg macro configurations:\
    `SAVE_GCODE_STATE NAME=PAUSE_state` and `RESTORE_GCODE_STATE NAME=PAUSE_state`
* **Please note:**\
The "CustomPiOS Migration Helper" is intended to only work on "vanilla" MainsailOS and FluiddPi systems. Do not try to migrate a modified MainsailOS or FluiddPi system (for example if you already used KIAUH to re-install services or to set up a multi-instance installation for Klipper / Moonraker). This won't work.

### 2021-01-31

* **This is a big one... KIAUH v3.0 is out.**\
With this update you can now install multiple instances of Klipper, Moonraker, Duet Web Control or Octoprint on the same Pi. This was quite a big rework of the whole script. So bugs can appear but with the help of some testers, i think there shouldn't be any critical ones anymore. In this regards thanks to @lixxbox and @zellneralex for testing.

* Important changes to how installations are set up now: All components get installed as systemd services. Installation via init.d was dropped completely! This shouldn't affect you at all, since the common linux distributions like RaspberryPi OS or custom distributions like MainsailOS, FluiddPi or OctoPi support both ways of installing services. I just wanted to mention it here.

* Now with KIAUH v3.0 and multi-instance installation capabilities, there are some things to point out. You will now need to tell KIAUH where your printers configurations are located when installing Klipper for the first time. Even though it is not recommended, you can change this location with the help of KIAUH and rewrite Klipper and Moonraker to use the new location.

* When setting up a multi-instance system, the folder structure will only change slightly. The goal was to keep it as compatible as possible with the custom distributions like mainsailOS and FluiddPi. This should help converting a single-instance setup of mainsailOS/FluiddPi to a multi-instance setup in no time, but keeping single-instance backwards compatibility if needed at a later point in time.

* The folder structure is as follows when setting up multi-instances:\
Each printer instance will get its own folder within your configuration location. The decision to this specific structure was made to make it as painless and easy as possible to convert to a multi-instance setup.
Here is an example:
    ```shell
    /home/<username>
              └── klipper_config
                  ├── printer_1
                  │   ├── printer.cfg
                  │   └── moonraker.conf
                  ├── printer_2
                  │   ├── printer.cfg
                  │   └── moonraker.conf
                  └── printer_n
                      ├── printer.cfg
                      └── moonraker.conf
    ```
* Also when setting up multi-instances of each service, the name of each service slightly changes.
Each service gets its corresponding instance added to the service filename.

    **This only applies to multi-instances! Single instance installations with KIAUH will keep their original names!**

    Corresponding to the filetree example from above that would mean:
    ```
    Klipper services:
            --> klipper-1.service
            --> klipper-2.service
            --> klipper-n.service

    Moonraker services:
            --> moonraker-1.service
            --> moonraker-2.service
            --> moonraker-n.service
    ```
* The same service file rules from above apply to OctoPrint even though only Klipper and Moonraker are shown in this example.

* You can start, stop and restart all Klipper, Moonraker and OctoPrint instances from the KIAUH main menu. For doing this, just type "stop klipper", "start moonraker", "restart octoprint" and so on.

* KIAUH v3.0 relocated its ini-file. It is now a hidden file in the users home-directory calles `.kiauh.ini`. This has the benefit of keeping all values in that file between possible re-installations of KIAUH. Otherwise that file would be lost.

* The option of adding more trusted clients to the moonraker.conf file was dropped. Since you can edit this file right inside of Mainsail or Fluidd, only some basic entries are made which get you running.

* I bet i have missed mentioning other stuff as well because it took me quite some time to re-write many functions. So i just hope you like the new version 😄

### 2020-11-28

* KIAUH now supports the installation, update and removal of [KlipperScreen](https://github.com/jordanruthe/KlipperScreen). This feature was was provided by [jordanruthe](https://github.com/jordanruthe)! Thank you!

### 2020-11-18

* Some changes to Fluidd caused a little rework on how KIAUH will install/update Fluidd from now on. Please see the [fluidd v1.0.0-rc0 release notes](https://github.com/cadriel/fluidd/releases/tag/v1.0.0-rc.0) for further information about what modifications to the moonraker.conf file exactly had to be done. In a nutshell, KIAUH will now always patch the required entries to the moonraker.conf if not already there.

### 2020-10-30:

* The user can now choose to install Klipper as a systemd service.

* The Shell Command extension and `shell_command.py` got renamed to G-Code Shell Command extension and `gcode_shell_command.py`. In case the [pending PR](https://github.com/KevinOConnor/klipper/pull/2173) will be merged in the future, this was an early attempt to dodge possible incompatibilities. The [G-Code Shell Command docs](gcode_shell_command.md) has been updated accordingly.

* The way how KIAUH interacts and writes to the users printer.cfg got changed. Usually KIAUH wrote everything directly into the printer.cfg. The way it will work from now on is, that a new file called `kiauh.cfg` will be created if there is something that needs to be written to the printer.cfg and everything gets written to `kiauh.cfg` instead. The only thing which then gets written to the users printer.cfg is `[include kiauh.cfg]`. This line will be located at the very top of the existing printer.cfg with a little comment as a note. The user can then decide to either keep the `kiauh.cfg` or take its content, places it into the printer.cfg directly and remove the `[include kiauh.cfg]`.

* The `mainsail_macros.cfg` got renamed to `webui_macros.cfg`. Since Mainsail and Fluidd both use the same kind of pause, cancel and resume macros, a more generic name was chosen for the file containing the example macros one can choose to install when installing those webinterfaces.

### 2020-10-10:

* Support for changing the Klipper branch to the moonraker-dev branch from @Arksine has been dropped. Support for Moonraker has been merged into Klipper mainline a long time ago.

* A new function is available from the main menu. You can now upload your log files to http://paste.c-net.org/ to share them for debugging purposes.

### 2020-10-06:

* Fluidd, a new Klipper interface got added to the list of available installers. At the same time some installation routines have changed or have seen some rework. Changes were made to the installation of NGINX configurations. A method was introduced to change the listen port of a webinterface configuration if there is already another webinterface listening on the default port (80).

* At the moment, the Moonraker installer no longer asks you whether you want to install a web interface too. For now you therefore have to install them with their respective installers. Please report any bugs or issues you encounter.

### 2020-09-17:

* The dev-2.0 branch will be abandoned as of today. If you did a checkout to that branch in the past, you have to checkout back to master to receive updates.

### 2020-09-12:

* The old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) won't be supported anymore!\
The is a new, fully rewritten project available: [dwc2-for-klipper-socket](https://github.com/Stephan3/dwc2-for-klipper-socket).\
The installer of this script also got rewritten to make use of that new project. You will not be able to install or remove the old [dwc2-for-klipper](https://github.com/Stephan3/dwc2-for-klipper) with KIAUH anymore if you updated KIAUH to the newest version.
