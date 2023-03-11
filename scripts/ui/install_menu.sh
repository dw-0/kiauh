#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

function install_ui() {
  top_border
  echo -e "|     ${green}~~~~~~~~~~~ [ Installation Menu ] ~~~~~~~~~~~${white}     |"
  hr
  echo -e "|  You need this menu usually only for installing       |"
  echo -e "|  all necessary dependencies for the various           |"
  echo -e "|  functions on a completely fresh system.              |"
  hr
  echo -e "| Firmware & API:          | 3rd Party Webinterface:    |"
  echo -e "|  1) [Klipper]            |  6) [OctoPrint]            |"
  echo -e "|  2) [Moonraker]          |                            |"
  echo -e "|                          | Other:                     |"
  echo -e "| Klipper Webinterface:    |  7) [PrettyGCode]          |"
  echo -e "|  3) [Mainsail]           |  8) [Telegram Bot]         |"
  echo -e "|  4) [Fluidd]             |  9) $(obico_install_title) |"
  echo -e "|                          | 10) [OctoEverywhere]       |"
  echo -e "| Touchscreen GUI:         |                            |"
  echo -e "|  5) [KlipperScreen]      | Webcam Streamer:           |"
  echo -e "|                          | 11) [Crowsnest]            |"
  back_footer
}

function install_menu() {
  clear && print_header
  install_ui

  ### save all installed webinterface ports to the ini file
  fetch_webui_ports

  ### save all klipper multi-instance names to the ini file
  set_multi_instance_names

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      1)
        do_action "start_klipper_setup" "install_ui";;
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
        do_action "telegram_bot_setup_dialog" "install_ui";;
      9)
        do_action "moonraker_obico_setup_dialog" "install_ui";;
      10)
        do_action "octoeverywhere_setup_dialog" "install_ui";;
      11)
        do_action "install_crowsnest" "install_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "install_ui";;
    esac
  done
  install_menu
}
