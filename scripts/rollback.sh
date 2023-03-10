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

function rollback_menu() {
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~ [ Rollback Menu ] ~~~~~~~~~~~~~")     |"
  hr
  echo -e "| If serious errors occured after updating Klipper or   |"
  echo -e "| Moonraker, you can use this menu to try and reset the |"
  echo -e "| repository to an earlier state.                       |"
  hr
  echo -e "| 1) Rollback Klipper                                   |"
  echo -e "| 2) Rollback Moonraker                                 |"
  back_footer

  local action
  while true; do
    read -p "${cyan}###### Perform action:${white} " action
    case "${action}" in
      1)
        select_msg "Klipper"
        rollback_component "klipper"
        break;;
      2)
        select_msg "Moonraker"
        rollback_component "moonraker"
        break;;
      B|b)
        clear; advanced_menu; break;;
      *)
        error_msg "Invalid command!";;
    esac
  done
}

function rollback_component() {
  local component=${1}

  if [[ ! -d "${HOME}/${component}" ]]; then
    print_error "Rollback not possible! Missing installation?"
    return
  fi

  echo
  top_border
  echo -e "| Please select how many commits you want to revert.    |"
  echo -e "| Consider using the information provided by the GitHub |"
  echo -e "| commit history to decide how many commits to revert.  |"
  blank_line
  echo -e "| ${red}Warning:${white}                                              |"
  echo -e "| ${red}Do not proceed if you are currently in the progress${white}   |"
  echo -e "| ${red}of printing! Proceeding WILL terminate that print!${white}    |"
  back_footer

  local count
  while true; do
    read -p "${cyan}###### Revert this amount of commits:${white} " count
    if [[ -n ${count} ]] && (( count > 0 )); then
      status_msg "Revert ${component^} by ${count} commits ..."
      cd "${HOME}/${component}"
      if git reset --hard HEAD~"${count}"; then
        do_action_service "restart" "${component}"
        print_confirm "${component^} was successfully reset!"
      else
        print_error "Reverting ${component^} failed! Please see the console output above."
      fi
      break
    elif [[ ${count} == "B" || ${count} == "b" ]]; then
      clear && print_header && break
    else
      error_msg "Invalid command!"
    fi
  done
  rollback_menu
}
