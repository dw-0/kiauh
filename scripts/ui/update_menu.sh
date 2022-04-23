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

function update_ui(){
  top_border
  echo -e "|     ${green}~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~${white}     |"
  hr
  echo -e "| a) [Update all]        |               |              |"
  echo -e "|                        | Installed:    | Latest:      |"
  echo -e "| Klipper & API:         |---------------|--------------|"
  echo -e "|  1) [Klipper]          |$(compare_klipper_versions)|"
  echo -e "|  2) [Moonraker]        |$(compare_moonraker_versions)|"
  echo -e "|                        |               |              |"
  echo -e "| Klipper Webinterface:  |---------------|--------------|"
  echo -e "|  3) [Mainsail]         |$(compare_mainsail_versions)|"
  echo -e "|  4) [Fluidd]           |$(compare_fluidd_versions)|"
  echo -e "|                        |               |              |"
  echo -e "| Touchscreen GUI:       |---------------|--------------|"
  echo -e "|  5) [KlipperScreen]    |$(compare_klipperscreen_versions)|"
  echo -e "|                        |               |              |"
  echo -e "| Other:                 |---------------|--------------|"
  echo -e "|  6) [PrettyGCode]      |$(compare_prettygcode_versions)|"
  echo -e "|  7) [Telegram Bot]     |$(compare_telegram_bot_versions)|"
  echo -e "|                        |------------------------------|"
  echo -e "|  8) [System]           |  $(check_system_updates)   |"
  back_footer
}

function update_menu(){
  unset update_arr
  do_action "" "update_ui"
  while true; do
    read -p "${cyan}####### Perform action:${white} " action
    case "${action}" in
      0)
        do_action "toggle_backups" "update_ui";;
      1)
        do_action "update_klipper" "update_ui";;
      2)
        do_action "update_moonraker" "update_ui";;
      3)
        do_action "update_mainsail" "update_ui";;
      4)
        do_action "update_fluidd" "update_ui";;
      5)
        do_action "update_klipperscreen" "update_ui";;
      6)
        do_action "update_pgc_for_klipper" "update_ui";;
      7)
        do_action "update_telegram_bot" "update_ui";;
      8)
        do_action "update_system" "update_ui";;
      a)
        do_action "update_all" "update_ui";;
      B|b)
        clear; main_menu; break;;
      *)
        deny_action "update_ui";;
    esac
  done
  update_menu
}

function update_all(){
  while true; do
    if [ "${#update_arr[@]}" = "0" ]; then
      CONFIRM_MSG="Everything is already up to date!"
      echo; break
    fi
    echo
    top_border
    echo -e "|  The following installations will be updated:         |"
    if [ "$KLIPPER_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Klipper${white}                                            |"
    fi
    if [ "${MOONRAKER_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● Moonraker${white}                                          |"
    fi
    if [ "${MAINSAIL_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● Mainsail${white}                                           |"
    fi
    if [ "${FLUIDD_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● Fluidd${white}                                             |"
    fi
    if [ "${KLIPPERSCREEN_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● KlipperScreen${white}                                      |"
    fi
    if [ "${PGC_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● PrettyGCode for Klipper${white}                            |"
    fi
    if [ "${MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● MoonrakerTelegramBot${white}                               |"
    fi
    if [ "${SYS_UPDATE_AVAIL}" = "true" ]; then
      echo -e "|  ${cyan}● System${white}                                             |"
    fi
    bottom_border
    if [ "${#update_arr[@]}" != "0" ]; then
      read -p "${cyan}###### Do you want to proceed? (Y/n):${white} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          for update in "${update_arr[@]}"
          do
            $update
          done
          break;;
        N|n|No|no)
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    fi
  done
}
