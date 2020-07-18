### set up some UI stuff

#ui total width = 57 chars
top_border(){
  echo -e "/=======================================================\ "
}

bottom_border(){
  echo -e "\=======================================================/"
}

hr(){
  echo -e "|-------------------------------------------------------|"
}

quit_footer(){
  hr
  echo -e "|                        ${red}Q) Quit${default}                        | "
  bottom_border
}

print_header(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~ [ KIAUH ] ~~~~~~~~~~~~~~~~~")     |"
  echo -e "|     $(title_msg "   Klipper Installation And Update Helper    ")     |"
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")     |"
  bottom_border
}

main_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|  0) [System status]  |                                |"
  echo -e "|                      |    Klipper: $KLIPPER_STATUS|"
  echo -e "|  1) [Install]        |     Branch: $PRINT_BRANCH|"
  echo -e "|  2) [Update]         |                                |"
  echo -e "|  3) [Remove]         |       DWC2: $DWC2_STATUS|"
  echo -e "|                      |   Mainsail: $MAINSAIL_STATUS|"
  echo -e "|  4) [Advanced]       |  Octoprint: $OCTOPRINT_STATUS|"
  echo -e "|  5) [Backup]         |                                |"
  quit_footer
}

install_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~ [ Installation Menu ] ~~~~~~~~~~~")     | "
  hr
  echo -e "|  You need this menu usually only for installing       | "
  echo -e "|  all necessary dependencies for the various           | "
  echo -e "|  functions on a completely fresh system.              | "
  hr
  echo -e "|  Firmware:             |                              | "
  echo -e "|  1) [Klipper]          |                              | "
  echo -e "|                        |                              | "
  echo -e "|  Webinterface:         |                              | "
  echo -e "|  2) [DWC2]             |                              | "
  echo -e "|  3) [Mainsail]         |                              | "
  echo -e "|  4) [Octoprint]        |                              | "
  quit_footer
}

update_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|  It is a good idea to check the following website     | "
  echo -e "|  for important software changes to the config file    | "
  echo -e "|  >> BEFORE << updating your klipper installation:     | "
  echo -e "|                                                       | "
  echo -e "|  ${yellow}https://www.klipper3d.org/Config_Changes.html${default}        | "
  bottom_border
  top_border
  echo -e "|  0) $BB4U_STATUS| "
  hr
  echo -e "|                        |  Local Vers:  | Remote Vers: | "
  echo -e "|  Firmware:             |               |              | "
  echo -e "|  1) [Klipper]          |  $(echo "$LOCAL_COMMIT")     | $(echo "$REMOTE_COMMIT")     | "
  echo -e "|                        |               |              | "
  echo -e "|  Webinterface:         |               |              | "
  echo -e "|  2) [DWC2-for-Klipper] |  $(echo "$LOCAL_DWC2FK_COMMIT")     | $(echo "$REMOTE_DWC2FK_COMMIT")     | "
  echo -e "|  3) [DWC2 Web UI]      |  $(echo "$DWC2_LOCAL_VER")        | $(echo "$DWC2_REMOTE_VER")        | "
  echo -e "|  4) [Mainsail]         |  $(echo "$MAINSAIL_LOCAL_VER")       | $(echo "$MAINSAIL_REMOTE_VER")       | "
  echo -e "|                        |               |              | "
  quit_footer
}

remove_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|  Files and directories which remain untouched:        | "
  echo -e "|  --> ~/printer.cfg                                    | "
  echo -e "|  --> ~/kiauh-backups                                  | "
  echo -e "|  You need remove them manually if you wish so.        | "
  hr
  echo -e "|  1) [Klipper]          |  5) [Tornado]                | "
  echo -e "|  2) [DWC2-for-Klipper] |  6) [Nginx]                  | "
  echo -e "|  3) [Mainsail]         |                              | "
  echo -e "|  4) [Octoprint]        |                              | "
  quit_footer
}

advanced_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "|  0) $OPRINT_SERVICE_STATUS| "
  hr
  echo -e "|                                                       | "
  echo -e "|  1) [Switch Klipper version]                          | "
  echo -e "|                                                       | "
  echo -e "|  2) [Build Firmware]                                  | "
  echo -e "|  3) [Flash MCU]                                       | "
  echo -e "|  4) [Get Printer-ID]                                  | "
  echo -e "|  5) [Write Printer-ID to printer.cfg]                 | "
  echo -e "|  6) [Write DWC2-for-Klipper config]                   | "
  echo -e "|                                                       | "
quit_footer
}

backup_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|                                                       | "
  hr
  echo -e "|  1) [        ]                                        | "
  echo -e "|  2) [        ]                                        | "
  echo -e "|  3) [        ]                                        | "
  echo -e "|  4) [        ]                                        | "
  echo -e "|  5) [        ]                                        | "
  echo -e "|  6) [        ]                                        | "
  echo -e "|  7) [        ]                                        | "
  echo -e "|                                                       | "
  quit_footer
}

switch_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~ [ Switch Klipper Branch ] ~~~~~~~~~")     |"
  bottom_border
  echo
  echo -e " $(title_msg "Active Branch: ")${green}$GET_BRANCH${default}"
  echo
  top_border
  echo -e "|  1) [--> origin/master]                               | "
  echo -e "|                                                       | "
  echo -e "|  2) [--> scurve-shaping]                              | "
  echo -e "|  3) [--> scurve-smoothing]                            | "
  echo -e "|                                                       | "
  echo -e "|  4) [--> moonraker]                                   | "
  echo -e "|  5) [--> dev-moonraker]                               | "
  quit_footer
}