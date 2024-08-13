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

function main_ui() {
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|  0) [Log-Upload] |         Klipper: $(print_status "klipper")|"
  echo -e "|  1) [List]       |            Repo: $(print_klipper_repo)|"
  echo -e "|  2) [Install]    |                                    |"
  echo -e "|  3) [Update]     |                                    |"
  echo -e "|  4) [Remove]     |       Moonraker: $(print_status "moonraker")|"
  echo -e "|  5) [Advanced]   |                                    |"
  echo -e "|  6) [Backup]     |        Mainsail: $(print_status "mainsail")|"
  echo -e "|  7) [Settings]   |          Fluidd: $(print_status "fluidd")|"
  echo -e "|                  |   KlipperScreen: $(print_status "klipperscreen")|"
  echo -e "|                  |    Telegram Bot: $(print_status "telegram_bot")|"
  echo -e "|                  |       Crowsnest: $(print_status "crowsnest")|"
  echo -e "|                  |           Obico: $(print_status "moonraker_obico")|"
  echo -e "|                  |  OctoEverywhere: $(print_status "octoeverywhere")|"
  echo -e "|                  |     Mobileraker: $(print_status "mobileraker")|"
  echo -e "|                  |         OctoApp: $(print_status "octoapp")|"
  echo -e "|                  |        Spoolman: $(print_status "spoolman")|"
  echo -e "|                  |                                    |"
  echo -e "|                  |       Octoprint: $(print_status "octoprint")|"
  hr
  echo -e "|  $(print_kiauh_version)|    Changelog: ${magenta}https://git.io/JnmlX${white} |"
  quit_footer
}

function get_kiauh_version() {
  local version
  cd "${KIAUH_SRCDIR}"
  version="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${version}"
}

function print_kiauh_version() {
  local version
  version="$(printf "%-16s" "$(get_kiauh_version)")"
  echo "${cyan}${version}${white}"
}

function print_status() {
  local status component="${1}"
  status=$(get_"${component}"_status)

  if [[ ${status} == "Not installed!" ]]; then
    status="${red}${status}${white}"
  elif [[ ${status} == "Incomplete!" ]]; then
    status="${yellow}${status}${white}"
  elif [[ ${status} == "Not linked!" ]]; then
    ### "Not linked!" is only required for Obico for Klipper
    status="${yellow}${status}${white}"
  else
    status="${green}${status}${white}"
  fi

  printf "%-28s" "${status}"
}

function print_klipper_repo() {
  read_kiauh_ini

  local repo klipper_status
  klipper_status=$(get_klipper_status)
  repo=$(echo "${custom_klipper_repo}" | sed "s/https:\/\/github\.com\///" | sed "s/\.git$//")
  repo="${repo^^}"

  if [[ ${klipper_status} == "Not installed!" ]]; then
    repo="${red}-${white}"
  elif [[ -n ${repo} && ${repo} != "KLIPPER3D/KLIPPER" ]]; then
    repo="${cyan}custom${white}"
  else
    repo="${cyan}Klipper3d/klipper${white}"
  fi

  printf "%-28s" "${repo}"
}

function main_menu() {
  clear && print_header
  main_ui

  ### initialize kiauh.ini
  init_ini

  local action
  while true; do
    read -p "${cyan}####### Perform action:${white} " action

    case "${action}" in
      "start klipper")
        do_action_service "start" "klipper"
        main_ui
        ;;
      "stop klipper")
        do_action_service "stop" "klipper"
        main_ui
        ;;
      "restart klipper")
        do_action_service "restart" "klipper"
        main_ui
        ;;
      "start moonraker")
        do_action_service "start" "moonraker"
        main_ui
        ;;
      "stop moonraker")
        do_action_service "stop" "moonraker"
        main_ui
        ;;
      "restart moonraker")
        do_action_service "restart" "moonraker"
        main_ui
        ;;
      "start octoprint")
        do_action_service "start" "octoprint"
        main_ui
        ;;
      "stop octoprint")
        do_action_service "stop" "octoprint"
        main_ui
        ;;
      "restart octoprint")
        do_action_service "restart" "octoprint"
        main_ui
        ;;
      "start crowsnest")
        do_action_service "start" "crowsnest"
        main_ui
        ;;
      "stop crowsnest")
        do_action_service "stop" "crowsnest"
        main_ui
        ;;
      "restart crowsnest")
        do_action_service "restart" "crowsnest"
        main_ui
        ;;
      update) do_action "update_kiauh" "main_ui" ;;
      0)
        clear && print_header
        upload_selection
        main_ui
        ;;
      1)
        clear && print_header
        list_menu
        break
        ;;
      2)
        clear && print_header
        install_menu
        break
        ;;
      3)
        clear && print_header
        update_menu
        break
        ;;
      4)
        clear && print_header
        remove_menu
        break
        ;;
      5)
        clear && print_header
        advanced_menu
        break
        ;;
      6)
        clear && print_header
        backup_menu
        main_ui
        ;;
      7)
        clear && print_header
        settings_menu
        break
        ;;
      Q | q)
        echo -e "${green}###### Happy printing! ######${white}"
        echo
        exit 0
        ;;
      *)
        deny_action "main_ui"
        ;;
    esac
  done
  main_menu
}
