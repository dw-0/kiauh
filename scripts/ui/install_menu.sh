#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>       #
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
  echo -e "|                          |                            |"
  echo -e "| Touchscreen GUI:         | Webcam Streamer:           |"
  echo -e "|  5) [KlipperScreen]      | 10) [MJPG-Streamer]        |"
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
        do_action "select_klipper_python_version" "install_ui";;
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
        do_action "install_mjpg-streamer" "install_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "install_ui";;
    esac
  done
  install_menu
}

function select_klipper_python_version() {
  top_border
  echo -e "| Please select the preferred Python version.           | "
  echo -e "| The recommended version is Python 2.7.                | "
  blank_line
  echo -e "| Installing Klipper with Python 3 is officially not    | "
  echo -e "| recommended and should be considered as experimental. | "
  hr
  echo -e "|  1) [Python 2.7]  (recommended)                       | "
  echo -e "|  2) [Python 3.x]  ${yellow}(experimental)${white}                      | "
  back_footer
  while true; do
    read -p "${cyan}###### Select Python version:${white} " action
    case "${action}" in
      1)
        select_msg "Python 2.7"
        klipper_setup_dialog "python2"
        break;;
      2)
        select_msg "Python 3.x"
        klipper_setup_dialog "python3"
        break;;
      B|b)
        clear; install_menu; break;;
      *)
        error_msg "Invalid Input!\n";;
    esac
  done
}
