#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e
clear -x

# make sure we have the correct permissions while running the script
umask 022

#===================================================#
#=================== UPDATE KIAUH ==================#
#===================================================#

function update_kiauh() {
  status_msg "Updating KIAUH ..."

  cd "${KIAUH_SRCDIR}"
  git reset --hard && git pull

  ok_msg "Update complete! Please restart KIAUH."
  exit 0
}

#===================================================#
#=================== KIAUH STATUS ==================#
#===================================================#

function kiauh_update_avail() {
  [[ ! -d "${KIAUH_SRCDIR}/.git" ]] && return
  local origin head

  cd "${KIAUH_SRCDIR}"

  ### abort if not on master branch
  ! git branch -a | grep -q "\* master" && return

  ### compare commit hash
  git fetch -q
  origin=$(git rev-parse --short=8 origin/master)
  head=$(git rev-parse --short=8 HEAD)

  if [[ ${origin} != "${head}" ]]; then
    echo "true"
  fi
}

function kiauh_update_dialog() {
  [[ ! $(kiauh_update_avail) == "true" ]] && return
  echo -e "/-------------------------------------------------------\\"
  echo -e "|${green}              New KIAUH update available!              ${white}|"
  echo -e "|-------------------------------------------------------|"
  echo -e "|${green}  View Changelog: https://git.io/JnmlX                 ${white}|"
  echo -e "|                                                       |"
  echo -e "|${yellow}  It is recommended to keep KIAUH up to date. Updates  ${white}|"
  echo -e "|${yellow}  usually contain bugfixes, important changes or new   ${white}|"
  echo -e "|${yellow}  features. Please consider updating!                  ${white}|"
  echo -e "\-------------------------------------------------------/"

  local yn
  read -p "${cyan}###### Do you want to update now? (Y/n):${white} " yn
  while true; do
    case "${yn}" in
     Y|y|Yes|yes|"")
       do_action "update_kiauh"
       break;;
     N|n|No|no)
       break;;
     *)
       deny_action "kiauh_update_dialog";;
    esac
  done
}

function check_euid() {
  if [[ ${EUID} -eq 0 ]]; then
    echo -e "${red}"
    echo -e "/-------------------------------------------------------\\"
    echo -e "|       !!! THIS SCRIPT MUST NOT RUN AS ROOT !!!        |"
    echo -e "|                                                       |"
    echo -e "|        It will ask for credentials as needed.         |"
    echo -e "\-------------------------------------------------------/"
    echo -e "${white}"
    exit 1
  fi
}

function check_if_ratos() {
  if [[ -n $(which ratos) ]]; then
    echo -e "${red}"
    echo -e "/-------------------------------------------------------\\"
    echo -e "|        !!! RatOS 2.1 or greater detected !!!          |"
    echo -e "|                                                       |"
    echo -e "|        KIAUH does currently not support RatOS.        |"
    echo -e "| If you have any questions, please ask for help on the |"
    echo -e "| RatRig Community Discord: https://discord.gg/ratrig   |"
    echo -e "\-------------------------------------------------------/"
    echo -e "${white}"
    exit 1
  fi
}

function main() {
   local entrypoint

   if ! command -v python3 &>/dev/null || [[ $(python3 -V | cut -d " " -f2 | cut -d "." -f2) -lt 8 ]]; then
     echo "Python 3.8 or higher is not installed!"
     echo "Please install Python 3.8 or higher and try again."
     exit 1
   fi

   entrypoint=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

   export PYTHONPATH="${entrypoint}"

   clear -x
   python3 "${entrypoint}/kiauh/main.py"
}

check_if_ratos
check_euid
kiauh_update_dialog
main
