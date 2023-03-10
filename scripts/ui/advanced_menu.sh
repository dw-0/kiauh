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

function advanced_ui() {
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| Klipper & API:          | Mainsail:                   |"
  echo -e "|  1) [Rollback]          |  6) [Theme installer]       |"
  echo -e "|                         |                             |"
  echo -e "| Firmware:               | System:                     |"
  echo -e "|  2) [Build only]        |  7) [Change hostname]       |"
  echo -e "|  3) [Flash only]        |                             |"
  echo -e "|  4) [Build + Flash]     | Extras:                     |"
  echo -e "|  5) [Get MCU ID]        |  8) [G-Code Shell Command]  |"
  back_footer
}

function advanced_menu() {
  do_action "" "advanced_ui"

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      1)
        do_action "rollback_menu" "advanced_menu";;
      2)
        do_action "build_fw" "advanced_ui";;
      3)
        clear && print_header
        do_action "init_flash_process" "advanced_ui";;
      4)
        clear && print_header
        status_msg "Please wait..."
        build_fw && init_flash_process
        advanced_ui;;
      5)
        clear && print_header
        select_mcu_connection
        print_detected_mcu_to_screen
        advanced_ui;;
      6)
        do_action "ms_theme_installer_menu";;
      7)
        clear
        print_header
        set_custom_hostname
        advanced_ui;;
      8)
        do_action "setup_gcode_shell_command" "advanced_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "advanced_ui";;
    esac
  done
  advanced_menu
}