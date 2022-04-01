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

install_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~ [ Installation Menu ] ~~~~~~~~~~~${white}     | "
  hr
  echo -e "|  You need this menu usually only for installing       | "
  echo -e "|  all necessary dependencies for the various           | "
  echo -e "|  functions on a completely fresh system.              | "
  hr
  echo -e "|  Firmware & API:          |  Other:                   | "
  echo -e "|  1) [Klipper]             |  6) [OctoPrint]           | "
  echo -e "|  2) [Moonraker]           |  7) [PrettyGCode]         | "
  echo -e "|                           |  8) [Telegram Bot]        | "
  echo -e "|  Klipper Webinterface:    |                           | "
  echo -e "|  3) [Mainsail]            |  Webcam:                  | "
  echo -e "|  4) [Fluidd]              |  9) [MJPG-Streamer]       | "
  echo -e "|                           |                           | "
  echo -e "|  Touchscreen GUI:         |                           | "
  echo -e "|  5) [KlipperScreen]       |                           | "
  back_footer
}

install_menu(){
  do_action "" "install_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        do_action "klipper_setup_dialog" "install_ui";;
      2)
        do_action "moonraker_setup_dialog" "install_ui";;
      3)
        do_action "install_mainsail" "install_ui";;
      4)
        do_action "install_fluidd" "install_ui";;
      5)
        do_action "install_klipperscreen" "install_ui";;
      6)
        do_action "octoprint_setup_dialog" "install_ui";;
      7)
        do_action "install_pgc_for_klipper" "install_ui";;
      8)
        do_action "install_MoonrakerTelegramBot" "install_ui";;
      9)
        do_action "install_mjpg-streamer" "install_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "install_ui";;
    esac
  done
  install_menu
}
