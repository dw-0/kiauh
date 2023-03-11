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

function backup_ui() {
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     |"
  hr
  echo -e "| ${yellow}INFO: Backups are located in '~/kiauh-backups'${white}        |"
  hr
  echo -e "| Klipper & API:             | Touchscreen GUI:         |"
  echo -e "|  1) [Klipper]              |  7) [KlipperScreen]      |"
  echo -e "|  2) [Moonraker]            |                          |"
  echo -e "|  3) [Configuration Folder] | 3rd Party Webinterface:  |"
  echo -e "|  4) [Moonraker Database]   |  8) [OctoPrint]          |"
  echo -e "|                            |                          |"
  echo -e "| Klipper Webinterface:      | Other:                   |"
  echo -e "|  5) [Mainsail]             |  9) [Telegram Bot]       |"
  echo -e "|  6) [Fluidd]               |                          |"
  back_footer
}

function backup_menu() {
  do_action "" "backup_ui"

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      1)
        do_action "backup_klipper" "backup_ui";;
      2)
        do_action "backup_moonraker" "backup_ui";;
      3)
        do_action "backup_klipper_config_dir" "backup_ui";;
      4)
        do_action "backup_moonraker_database" "backup_ui";;
      5)
        do_action "backup_mainsail" "backup_ui";;
      6)
        do_action "backup_fluidd" "backup_ui";;
      7)
        do_action "backup_klipperscreen" "backup_ui";;
      8)
        do_action "backup_octoprint" "backup_ui";;
      9)
        do_action "backup_telegram_bot" "backup_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "backup_ui";;
    esac
  done
  backup_menu
}
