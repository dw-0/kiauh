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

### global variables
INI_FILE="${HOME}/.kiauh.ini"
KLIPPER_CONFIG="${HOME}/klipper_config"

function settings_ui() {
  read_kiauh_ini
  local custom_cfg_loc="${custom_klipper_cfg_loc}"
  local ms_pre_rls="${mainsail_always_install_latest}"
  local fl_pre_rls="${fluidd_always_install_latest}"

  if [ -z "${custom_cfg_loc}" ]; then
    custom_cfg_loc="${cyan}${KLIPPER_CONFIG}${white}"
  else
    custom_cfg_loc="${cyan}${custom_cfg_loc}${white}"
  fi
  if [ "${ms_pre_rls}" == "false" ]; then
    ms_pre_rls="${red}● ${ms_pre_rls}${white}"
  else
    ms_pre_rls="${green}● ${ms_pre_rls}${white}"
  fi
  if [ "${fl_pre_rls}" == "false" ]; then
    fl_pre_rls="${red}● ${fl_pre_rls}${white}"
  else
    fl_pre_rls="${green}● ${fl_pre_rls}${white}"
  fi

  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~ [ KIAUH Settings ] ~~~~~~~~~~~~~")     |"
  hr
  echo -e "| Klipper:                                              |"
  printf  "| Config folder: %-49s|\n" "${custom_cfg_loc}"
  blank_line
  echo -e "| Klipper Webinterface:                                 |"
  printf  "| 1) Install Mainsail latest: %-38s|\n" "${ms_pre_rls}"
  printf  "| 2) Install Fluidd latest:   %-38s|\n" "${fl_pre_rls}"
  hr
  blank_line
  back_help_footer
}

function show_settings_help(){
  top_border
  echo -e "|    ~~~~~~ < ? > Help: KIAUH Settings < ? > ~~~~~~     |"
  hr
  echo -e "| ${cyan}Klipper config folder:${white}                                |"
  echo -e "| The location of your printer.cfg and all other config |"
  echo -e "| files that gets used during installation of Klipper   |"
  echo -e "| and all other components which need that location.    |"
  echo -e "| Default: /home/<username>/klipper_config              |"
  blank_line
  echo -e "| ${cyan}Mainsail latest / Fluidd latest:${white}                      |"
  echo -e "| If this setting is set to 'true', KIAUH will always   |"
  echo -e "| install or update Mainsail / Fluidd to the currently  |"
  echo -e "| latest available version. NOTE: This will include     |"
  echo -e "| alpha, beta, and rc (release-candidate) versions!     |"
  echo -e "| If this setting is set to 'false', KIAUH will only    |"
  echo -e "| install the latest STABLE Mainsail version.           |"
  echo -e "| Toggle between 'true' / 'false' by typing '1' / '2'   |"
  echo -e "| and hit enter. Default: 'false'                       |"
  blank_line
  back_footer
  while true; do
    read -p "${cyan}###### Please select:${white} " choice
    case "${choice}" in
      B|b)
        clear && print_header
        settings_menu
        break;;
      *)
        deny_action "show_settings_help";;
    esac
  done
}

settings_menu(){
  do_action "" "settings_ui"
  while true; do
    read -p "${cyan}Perform action:${white} " action; echo
    case "${action}" in
      1)
        switch_mainsail && settings_menu;;
      2)
        switch_fluidd && settings_menu;;
      B|b)
        clear
        main_menu
        break;;
      H|h)
        clear && print_header
        show_settings_help
        break;;
      *)
        deny_action "settings_ui";;
    esac
  done
}

function switch_mainsail() {
  read_kiauh_ini
  local state="${mainsail_always_install_latest}"
  if [ "${state}" == "false" ]; then
    sed -i '/mainsail_always_install_latest=/s/false/true/' "${INI_FILE}"
    log_info "mainsail_always_install_latest changed (false -> true) "
  else
    sed -i '/mainsail_always_install_latest=/s/true/false/' "${INI_FILE}"
    log_info "mainsail_always_install_latest changed (true -> false) "
  fi
}

function switch_fluidd() {
  read_kiauh_ini
  local state="${fluidd_always_install_latest}"
  if [ "${state}" == "false" ]; then
    sed -i '/fluidd_always_install_latest=/s/false/true/' "${INI_FILE}"
    log_info "fluidd_always_install_latest changed (false -> true) "
  else
    sed -i '/fluidd_always_install_latest=/s/true/false/' "${INI_FILE}"
    log_info "fluidd_always_install_latest changed (true -> false) "
  fi
}
