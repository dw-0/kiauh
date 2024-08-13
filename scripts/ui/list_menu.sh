#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

function list_ui() {
  top_border
  echo -e "|     ${green}~~~~~~~~~~~~~~~ [ List Menu ] ~~~~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| Firmware & API:          | Other:                     |"
  echo -e "|  1) [Klipper]            |  7) [PrettyGCode]          |"
  echo -e "|  2) [Moonraker]          |  8) [Telegram Bot]         |"
  echo -e "|                          |  9) $(obico_install_title) |"
  echo -e "| Klipper Webinterface:    | 10) [OctoEverywhere]       |"
  echo -e "|  3) [Mainsail]           | 11) [Mobileraker]          |"
  echo -e "|  4) [Fluidd]             | 12) [OctoApp for Klipper]  |"
  echo -e "|                          | 13) [Spoolman]             |"
  echo -e "| Touchscreen GUI:         |                            |"
  echo -e "|  5) [KlipperScreen]      | Webcam Streamer:           |"
  echo -e "|                          | 14) [Crowsnest]            |"
  echo -e "| 3rd Party Webinterface:  |                            |"
  echo -e "|  6) [OctoPrint]          |                            |"
  back_footer
}

function list_menu() {
  print_header
  list_ui

  ### save all installed webinterface ports to the ini file
  fetch_webui_ports

  ### save all klipper multi-instance names to the ini file
  set_multi_instance_names

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      1)
        do_action "list_klipper" "list_ui"
        ;;
        #   2)
        #     do_action "list_moonraker" "list_ui"
        #     ;;
        #   3)
        #     do_action "install_mainsail" "list_ui"
        #     ;;
        #   4)
        #     do_action "install_fluidd" "list_ui"
        #     ;;
        #   5)
        #     do_action "install_klipperscreen" "list_ui"
        #     ;;
        #   6)
        #     do_action "octoprint_setup_dialog" "list_ui"
        #     ;;
        #   7)
        #     do_action "install_pgc_for_klipper" "list_ui"
        #     ;;
        #   8)
        #     do_action "telegram_bot_setup_dialog" "list_ui"
        #     ;;
        #   9)
        #     do_action "moonraker_obico_setup_dialog" "list_ui"
        #     ;;
        #   10)
        #     do_action "octoeverywhere_setup_dialog" "list_ui"
        #     ;;
        #   11)
        #     do_action "install_mobileraker" "list_ui"
        #     ;;
        #   12)
        #     do_action "octoapp_setup_dialog" "list_ui"
        #     ;;
        #   13)
        #     do_action "install_spoolman" "list_ui"
        #     ;;
        #   14)
        #     do_action "install_crowsnest" "list_ui"
        #     ;;
      B | b)
        clear
        main_menu
        break
        ;;
      *)
        deny_action "list_ui"
        ;;
    esac
  done
  install_menu
}
