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
  echo -e "                                          KIAUH: $CURR_KIAUH_BRANCH"
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
  echo -e "|  1) [Install]        |     Branch: ${cyan}$PRINT_BRANCH${default}|"
  echo -e "|  2) [Update]         |                                |"
  echo -e "|  3) [Remove]         |       DWC2: $DWC2_STATUS|"
  echo -e "|                      |   Mainsail: $MAINSAIL_STATUS|"
  echo -e "|  4) [Advanced]       |  Octoprint: $OCTOPRINT_STATUS|"
  echo -e "|  5) [Backup]         |                                |"
  quit_footer
}

install_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~ [ Installation Menu ] ~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  You need this menu usually only for installing       | "
  echo -e "|  all necessary dependencies for the various           | "
  echo -e "|  functions on a completely fresh system.              | "
  hr
  echo -e "|  Firmware:             |  Webinterface:               | "
  echo -e "|  1) [Klipper]          |  3) [DWC2]                   | "
  echo -e "|                        |  4) [Mainsail]               | "
  echo -e "|  Klipper API:          |  5) [Octoprint]              | "
  echo -e "|  2) [Moonraker]        |                              | "
  quit_footer
}

update_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~${default}     | "
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
  echo -e "|  Webinterface:         |---------------|--------------| "
  echo -e "|  2) [DWC2-for-Klipper] |  $(echo "$LOCAL_DWC2FK_COMMIT")     | $(echo "$REMOTE_DWC2FK_COMMIT")     | "
  echo -e "|  3) [DWC2 Web UI]      |  $(echo "$DWC2_LOCAL_VER")        | $(echo "$DWC2_REMOTE_VER")        | "
  echo -e "|                        |---------------|--------------| "
  echo -e "|  4) [Moonraker]        |  $(echo "$LOCAL_MOONRAKER_COMMIT")     | $(echo "$REMOTE_MOONRAKER_COMMIT")     | "
  echo -e "|  5) [Mainsail]         |  $(echo "$MAINSAIL_LOCAL_VER")        | $(echo "$MAINSAIL_REMOTE_VER")        | "
  quit_footer
}

remove_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  Files and directories which remain untouched:        | "
  echo -e "|  --> ~/printer.cfg                                    | "
  echo -e "|  --> ~/kiauh-backups                                  | "
  echo -e "|  You need remove them manually if you wish so.        | "
  hr
  echo -e "|  Firmware:             |  Webinterface:               | "
  echo -e "|  1) [Klipper]          |  3) [DWC2]                   | "
  echo -e "|                        |  4) [Mainsail]               | "
  echo -e "|  Klipper API:          |  5) [Octoprint]              | "
  echo -e "|  2) [Moonraker]        |                              | "
  echo -e "|                        |  Webserver:                  | "
  echo -e "|                        |  6) [Nginx]                  | "
  quit_footer
}

advanced_ui(){
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  0) $OPRINT_SERVICE_STATUS| "
  hr
  echo -e "|                           |                           | "
  echo -e "|  Klipper:                 |  System:                  | "
  echo -e "|  1) [Switch Version]      |  8) [Change hostname]     | "
  echo -e "|  2) [Rollback]            |                           | "
  echo -e "|                           |  Mainsail:                | "
  echo -e "|  Firmware:                |  9) [Remove branding]     | "
  echo -e "|  3) [Build Firmware]      |                           | "
  echo -e "|  4) [Flash MCU]           |                           | "
  echo -e "|  5) [Get Printer-USB]     |                           | "
  echo -e "|  6) [Write Printer-USB]   |                           | "
  echo -e "|  7) [Write DWC2 config]   |                           | "
  echo -e "|                           |                           | "
quit_footer
}

backup_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|           ${yellow}Backup location: ~/kiauh-backups${default}            | "
  hr
  echo -e "|  Firmware:                                            | "
  echo -e "|  1) [Klipper]                                         | "
  echo -e "|                                                       | "
  echo -e "|  Webinterface:                                        | "
  echo -e "|  2) [DWC2 Web UI]                                     | "
  echo -e "|                                                       | "
  echo -e "|  3) [Mainsail]                                        | "
  echo -e "|  4) [Moonraker]                                       | "
  echo -e "|                                                       | "
  echo -e "|  5) [OctoPrint]                                       | "
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
  quit_footer
}

kiauh_update_msg(){
  top_border
  echo -e "|  ${yellow}There is a newer version of this script available!${default}   | "
  echo -e "|  ${yellow}Type 'update' if you want to update KIAUH now.${default}       | "
  bottom_border
}

rollback_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~ [ Rollback Menu ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "|  If serious errors occured after updating Klipper,    | "
  echo -e "|  you can use this menu to return to the previously    | "
  echo -e "|  used commit from which you have updated.             | "
  bottom_border
  top_border
  echo -e "|  Active branch: ${green}$PRINT_BRANCH${default}                   | "
  hr
  echo -e "|  Currently on commit:                                 | "
  echo -e "|  $CURR_UI                             | "
  hr
  echo -e "|  Commit last updated from:                            | "
  echo -e "|  $PREV_UI                             | "
  quit_footer
}