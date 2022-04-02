#!/bin/bash

#=======================================================================#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

settings_ui(){
  source_kiauh_ini
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~ [ KIAUH Settings ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "| ${red}Caution:${white}                                              | "
  echo -e "| When you change the config folder, be aware that ALL  | "
  echo -e "| Klipper and Moonraker services will be STOPPED,       | "
  echo -e "| reconfigured and then restarted again.                | "
  blank_line
  echo -e "| ${red}DO NOT change the folder during printing!${white}             | "
  hr
  blank_line
  echo -e "|  ${cyan}● Current Klipper config folder:${white}                     | "
  printf "|%-55s|\n" "    $klipper_cfg_loc"
  blank_line
  hr
  if [ -z $klipper_cfg_loc ]; then
  echo -e "|  ${red}N/A) Install Klipper with KIAUH first to unlock!${white}     | "
  else
  echo -e "|  1) Change config folder                              | "
  fi
  back_footer
}

settings_menu(){
  do_action "" "settings_ui"
  while true; do
    read -p "${cyan}Perform action:${white} " action; echo
    case "$action" in
      1)
        if [ ! -z $klipper_cfg_loc ]; then
          do_action "change_klipper_cfg_path" "settings_ui"
        else
          deny_action "settings_ui"
        fi;;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "settings_ui";;
    esac
  done
  settings_ui
}
