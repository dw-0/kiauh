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

function main_ui() {
  echo -e "${yellow}/=======================================================\\"
  echo -e "| Please read the newest changelog carefully:           |"
  echo -e "| https://git.io/JnmlX                                  |"
  echo -e "\=======================================================/${white}"
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|  0) [Log-Upload] |         Klipper: $(print_status "klipper")|"
  echo -e "|                  |            Repo: $(print_klipper_repo)|"
  echo -e "|  1) [Install]    |                                    |"
  echo -e "|  2) [Update]     |       Moonraker: $(print_status "moonraker")|"
  echo -e "|  3) [Remove]     |                                    |"
  echo -e "|  4) [Advanced]   |        Mainsail: $(print_status "mainsail")|"
#  echo -e "|  5) [Backup]     |        Fluidd: $(print_status "fluidd")|"
  echo -e "|                  |          Fluidd: $(print_status "fluidd")|"
  echo -e "|                  |   KlipperScreen: $(print_status "klipperscreen")|"
  echo -e "|  6) [Settings]   |    Telegram Bot: $(print_status "telegram_bot")|"
  echo -e "|                  |       Crowsnest: $(print_status "crowsnest")|"
  echo -e "|                  |           Obico: $(print_status "moonraker_obico")|"
  echo -e "|                  |  OctoEverywhere: $(print_status "octoeverywhere")|"
  echo -e "|                  |                                    |"
  echo -e "|  $(print_kiauh_version)|       Octoprint: $(print_status "octoprint")|"
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
    ### "Not linked!" is only required for Moonraker-obico
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
  elif [[ -n ${repo} && ${repo} != "KLIPPER3D/KLIPPER"  ]]; then
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
      "start klipper") do_action_service "start" "klipper"; main_ui;;
      "stop klipper") do_action_service "stop" "klipper"; main_ui;;
      "restart klipper") do_action_service "restart" "klipper"; main_ui;;
      "start moonraker") do_action_service "start" "moonraker"; main_ui;;
      "stop moonraker") do_action_service "stop" "moonraker"; main_ui;;
      "restart moonraker")do_action_service "restart" "moonraker"; main_ui;;
      "start octoprint") do_action_service "start" "octoprint"; main_ui;;
      "stop octoprint") do_action_service "stop" "octoprint"; main_ui;;
      "restart octoprint") do_action_service "restart" "octoprint"; main_ui;;
      "start crowsnest") do_action_service "start" "crowsnest"; main_ui;;
      "stop crowsnest") do_action_service "stop" "crowsnest"; main_ui;;
      "restart crowsnest") do_action_service "restart" "crowsnest"; main_ui;;
      update) do_action "update_kiauh" "main_ui";;
      0)clear && print_header
        #upload_selection
        print_error "Function currently disabled! Sorry!"
        main_ui;;
      1)clear && print_header
        install_menu
        break;;
      2) clear && print_header
        update_menu
        break;;
      3) clear && print_header
        remove_menu
        break;;
      4)clear && print_header
        advanced_menu
        break;;
      5)clear && print_header
        #backup_menu
        print_error "Function currently disabled! Sorry!"
        main_ui;;
      6)clear && print_header
        settings_menu
        break;;
      Q|q)
        echo -e "${green}###### Happy printing! ######${white}"; echo
        exit 0;;
      *)
        deny_action "main_ui";;
    esac
  done
  main_menu
}
