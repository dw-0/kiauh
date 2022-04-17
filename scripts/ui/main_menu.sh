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

main_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|  0) [Upload Log]     |       Klipper: $(get_klipper_status)|"
  echo -e "|                      |                                |"
  echo -e "|  1) [Install]        |                                |"
  echo -e "|  2) [Update]         |     Moonraker: $(get_moonraker_status)|"
  echo -e "|  3) [Remove]         |                                |"
  echo -e "|  4) [Advanced]       |      Mainsail: $MAINSAIL_STATUS|"
  echo -e "|  5) [Backup]         |        Fluidd: $FLUIDD_STATUS|"
  echo -e "|                      | KlipperScreen: $(klipperscreen_status)|"
  echo -e "|  6) [Settings]       |  Telegram Bot: $(get_telegram_bot_status)|"
  echo -e "|                      |                                |"
  echo -e "|  $(get_kiauh_version)|     Octoprint: $OCTOPRINT_STATUS|"
  quit_footer
}

get_kiauh_version(){
  local version
  cd "${SRCDIR}/kiauh"
  version="$(printf "%-20s" "$(git describe HEAD --always --tags | cut -d "-" -f 1,2)")"
  echo "${cyan}${version}${white}"
}

kiauh_update_dialog(){
  [ ! "$(kiauh_update_avail)" == "true" ] && return
  top_border
  echo -e "|${green}              New KIAUH update available!              ${white}| "
  hr
  echo -e "|${green}  View Changelog: https://git.io/JnmlX                 ${white}| "
  blank_line
  echo -e "|${yellow}  It is recommended to keep KIAUH up to date. Updates  ${white}| "
  echo -e "|${yellow}  usually contain bugfixes, important changes or new   ${white}| "
  echo -e "|${yellow}  features. Please consider updating!                  ${white}| "
  bottom_border
  read -p "${cyan}Do you want to update now? (Y/n):${white} " yn
  while true; do
    case "${yn}" in
    Y|y|Yes|yes|"")
      do_action "update_kiauh"
      break;;
    N|n|No|no) break;;
    *)
      deny_action "kiauh_update_dialog";;
    esac
  done
}

main_menu(){
  print_header
  #prompt for KIAUH update if update available
  kiauh_update_dialog
  #check install status
    fluidd_status
    mainsail_status
    octoprint_status
  main_ui
  while true; do
    read -p "${cyan}Perform action:${white} " action; echo
    case "${action}" in
      "start klipper") do_action_service "start" "klipper"; main_ui;;
      "stop klipper") do_action_service "stop" "klipper"; main_ui;;
      "restart klipper") do_action_service "restart" "klipper"; main_ui;;
      "start moonraker") do_action_service "start" "moonraker"; main_ui;;
      "stop moonraker") do_action_service "stop" "moonraker"; main_ui;;
      "restart moonraker")do_action_service "restart" "moonraker"; main_ui;;
      "start octoprint") do_action_service "start" "octoprint"; main_ui;;
      "stop octoprint") do_action_service "stop" "octoprint"; main_ui;;
      "restart octoprint") do_action_service "restart" "octoprint"; main_ui;;
      update) do_action "update_kiauh" "main_ui";;
      0)clear && print_header
        upload_selection
        break;;
      1)clear && print_header
        install_menu
        break;;
      2) clear && print_header
        update_menu
        break;;
      3) clear && print_header
        remove_menu
        break;;
      4)clear && print_header
        advanced_menu
        break;;
      5)clear && print_header
        backup_menu
        break;;
      6)clear && print_header
        settings_menu
        break;;
      Q|q)
        echo -e "${green}###### Happy printing! ######${white}"; echo
        exit 0;;
      *)
        deny_action "main_ui";;
    esac
  done
  clear; main_menu
}
