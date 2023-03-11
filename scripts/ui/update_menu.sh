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

function update_ui() {
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
  echo -e "|  8) [Obico for Klipper]|$(compare_moonraker_obico_versions)|"
  echo -e "|  9) [OctoEverywhere]   |$(compare_octoeverywhere_versions)|"
  echo -e "| 10) [Crowsnest]        |$(compare_crowsnest_versions)|"
  echo -e "|                        |------------------------------|"
  echo -e "| 11) [System]           |  $(check_system_updates)   |"
  back_footer
}

function update_menu() {
  do_action "" "update_ui"
  
  local action
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
        do_action "update_moonraker_obico" "update_ui";;
      9)
        do_action "update_octoeverywhere" "update_ui";;
      10)
        do_action "update_crowsnest" "update_ui";;
      11)
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

function update_all() {
  read_kiauh_ini "${FUNCNAME[0]}"

  local update_arr
  local app_update_state="${application_updates_available}"

  IFS=', ' read -r -a update_arr <<< "${app_update_state}"

  while true; do
    if (( ${#update_arr[@]} == 0 )); then
      print_confirm "Everything is already up-to-date!"
      echo; break
    fi
    
    echo
    top_border
    echo -e "|  The following installations will be updated:         |"

    [[ "${update_arr[*]}" =~ "klipper" ]] && \
    echo -e "|  ${cyan}● Klipper${white}                                            |"

    [[ "${update_arr[*]}" =~ "moonraker" ]] && \
    echo -e "|  ${cyan}● Moonraker${white}                                          |"

    [[ "${update_arr[*]}" =~ "mainsail" ]] && \
    echo -e "|  ${cyan}● Mainsail${white}                                           |"

    [[ "${update_arr[*]}" =~ "fluidd" ]] && \
    echo -e "|  ${cyan}● Fluidd${white}                                             |"

    [[ "${update_arr[*]}" =~ "klipperscreen" ]] && \
    echo -e "|  ${cyan}● KlipperScreen${white}                                      |"

    [[ "${update_arr[*]}" =~ "pgc_for_klipper" ]] && \
    echo -e "|  ${cyan}● PrettyGCode for Klipper${white}                            |"

    [[ "${update_arr[*]}" =~ "telegram_bot" ]] && \
    echo -e "|  ${cyan}● MoonrakerTelegramBot${white}                               |"

    [[ "${update_arr[*]}" =~ "octoeverywhere" ]] && \
    echo -e "|  ${cyan}● OctoEverywhere${white}                                     |"

    [[ "${update_arr[*]}" =~ "system" ]] && \
    echo -e "|  ${cyan}● System${white}                                             |"

    bottom_border
    
    local yn
    read -p "${cyan}###### Do you want to proceed? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        for app in "${update_arr[@]}"; do
          local update="update_${app}"
          #shellcheck disable=SC2250
          $update
        done
        break;;
      N|n|No|no)
        break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}
