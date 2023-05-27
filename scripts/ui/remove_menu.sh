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

function remove_ui() {
  top_border
  echo -e "|     ${red}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| ${yellow}INFO: Configurations and/or any backups will be kept!${white} |"
  hr
  echo -e "| Firmware & API:           | 3rd Party Webinterface:   |"
  echo -e "|  1) [Klipper]             |  8) [OctoPrint]           |"
  echo -e "|  2) [Moonraker]           |                           |"
  echo -e "|                           | Webcam Streamer:          |"
  echo -e "| Klipper Webinterface:     |  9) [Crowsnest]           |"
  echo -e "|  3) [Mainsail]            | 10) [MJPG-Streamer]       |"
  echo -e "|  4) [Mainsail-Config]     |                           |"
  echo -e "|  5) [Fluidd]              | Other:                    |"
  echo -e "|  6) [Fluidd-Config]       | 11) [PrettyGCode]         |"
  echo -e "|                           | 12) [Telegram Bot]        |"
  echo -e "| Touchscreen GUI:          | 13) [Obico for Klipper]   |"
  echo -e "|  7) [KlipperScreen]       | 14) [OctoEverywhere]      |"
  echo -e "|                           | 15) [Mobileraker]         |"
  echo -e "|                           | 16) [NGINX]               |"
  back_footer
}

function remove_menu() {
  do_action "" "remove_ui"

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      1)
        do_action "remove_klipper" "remove_ui";;
      2)
        do_action "remove_moonraker" "remove_ui";;
      3)
        do_action "remove_mainsail" "remove_ui";;
      4)
        do_action "remove_mainsail_config" "remove_ui";;
      5)
        do_action "remove_fluidd" "remove_ui";;
      6)
        do_action "remove_fluidd_config" "remove_ui";;
      7)
        do_action "remove_klipperscreen" "remove_ui";;
      8)
        do_action "remove_octoprint" "remove_ui";;
      9)
        do_action "remove_crowsnest" "remove_ui";;
      10)
        do_action "remove_mjpg-streamer" "remove_ui";;
      11)
        do_action "remove_prettygcode" "remove_ui";;
      12)
        do_action "remove_telegram_bot" "remove_ui";;
      13)
        do_action "remove_moonraker_obico" "remove_ui";;
      14)
        do_action "remove_octoeverywhere" "remove_ui";;
      15)
        do_action "remove_mobileraker" "remove_ui";;
      16)
        do_action "remove_nginx" "remove_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "remove_ui";;
    esac
  done
  remove_menu
}
