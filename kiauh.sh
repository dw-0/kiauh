#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e
clear

### set color variables
green=$(echo -en "\e[92m")
yellow=$(echo -en "\e[93m")
red=$(echo -en "\e[91m")
cyan=$(echo -en "\e[96m")
default=$(echo -en "\e[39m")
white=$(echo -en "\e[39m")

### sourcing all additional scripts
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"
for script in "${SRCDIR}/kiauh/scripts/"*.sh; do . "${script}"; done
for script in "${SRCDIR}/kiauh/scripts/ui/"*.sh; do . "${script}"; done

### set important directories
#klipper
KLIPPER_DIR=${HOME}/klipper
KLIPPY_ENV=${HOME}/klippy-env
#nginx
NGINX_SA=/etc/nginx/sites-available
NGINX_SE=/etc/nginx/sites-enabled
NGINX_CONFD=/etc/nginx/conf.d
#moonraker
MOONRAKER_DIR=${HOME}/moonraker
MOONRAKER_ENV=${HOME}/moonraker-env
#mainsail
MAINSAIL_DIR=${HOME}/mainsail
#fluidd
FLUIDD_DIR=${HOME}/fluidd
#dwc2
DWC2FK_DIR=${HOME}/dwc2-for-klipper-socket
DWC_ENV_DIR=${HOME}/dwc-env
DWC2_DIR=${HOME}/duetwebcontrol
#octoprint
OCTOPRINT_DIR=${HOME}/OctoPrint
OCTOPRINT_CFG_DIR=${HOME}/.octoprint
#KlipperScreen
KLIPPERSCREEN_DIR=${HOME}/KlipperScreen
KLIPPERSCREEN_ENV_DIR=${HOME}/.KlipperScreen-env
#MoonrakerTelegramBot
MOONRAKER_TELEGRAM_BOT_DIR=${HOME}/moonraker-telegram-bot
MOONRAKER_TELEGRAM_BOT_ENV_DIR=${HOME}/moonraker-telegram-bot-env
#misc
INI_FILE=${HOME}/.kiauh.ini
BACKUP_DIR=${HOME}/kiauh-backups

### set github repos
ARKSINE_REPO=https://github.com/Arksine/klipper.git
DMBUTYUGIN_REPO=https://github.com/dmbutyugin/klipper.git
DWC2FK_REPO=https://github.com/Stephan3/dwc2-for-klipper-socket.git
KLIPPERSCREEN_REPO=https://github.com/jordanruthe/KlipperScreen.git
NLEF_REPO=https://github.com/nlef/moonraker-telegram-bot.git
#branches
BRANCH_SCURVE_SMOOTHING=dmbutyugin/scurve-smoothing
BRANCH_SCURVE_SHAPING=dmbutyugin/scurve-shaping

### format some default message types
select_msg() {
  echo -e "${white}>>>>>> $1"
}
warn_msg(){
  echo -e "${red}>>>>>> $1${white}"
}
status_msg(){
  echo; echo -e "${yellow}###### $1${white}"
}
ok_msg(){
  echo -e "${green}>>>>>> $1${white}"
}
error_msg(){
  echo -e "${red}>>>>>> $1${white}"
}
abort_msg(){
  echo -e "${red}<<<<<< $1${white}"
}
title_msg(){
  echo -e "${cyan}$1${white}"
}
get_date(){
  current_date=$(date +"%y%m%d-%H%M")
  export current_date
}
print_unkown_cmd(){
  ERROR_MSG="Invalid command!"
}
invalid_option(){
  ERROR_MSG="Invalid command!"
}

print_msg(){
  if [ -n "${ERROR_MSG}" ]; then
    echo -e "${red}"
    echo -e "#########################################################"
    echo -e " ${ERROR_MSG} "
    echo -e "#########################################################"
    echo -e "${white}"
  fi
  if [ -n "${CONFIRM_MSG}" ]; then
    echo -e "${green}"
    echo -e "#########################################################"
    echo -e " ${CONFIRM_MSG} "
    echo -e "#########################################################"
    echo -e "${white}"
  fi
}

print_error(){
  [ -z "${1}" ] && return
  echo -e "${red}"
  echo -e "#########################################################"
  echo -e "  ${1} "
  echo -e "#########################################################"
  echo -e "${white}"
}

print_confirm(){
  [ -z "${1}" ] && return
  echo -e "${green}"
  echo -e "#########################################################"
  echo -e "  ${1} "
  echo -e "#########################################################"
  echo -e "${white}"
}

clear_msg(){
  unset CONFIRM_MSG
  unset ERROR_MSG
}

check_euid
init_ini
kiauh_status
main_menu
