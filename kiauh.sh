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

### sourcing all additional scripts
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. && pwd )"
for script in "${SRCDIR}/kiauh/scripts/"*.sh; do . "${script}"; done
for script in "${SRCDIR}/kiauh/scripts/ui/"*.sh; do . "${script}"; done

#===================================================#
#=================== UPDATE KIAUH ==================#
#===================================================#

function update_kiauh(){
  status_msg "Updating KIAUH ..."
  cd "${SRCDIR}/kiauh"
  git reset --hard && git pull
  ok_msg "Update complete! Please restart KIAUH."
  exit 0
}

#===================================================#
#=================== KIAUH STATUS ==================#
#===================================================#

function kiauh_update_avail(){
  [ ! -d "${SRCDIR}/kiauh/.git" ] && return
  local origin head
  cd "${SRCDIR}/kiauh"
  ### abort if not on master branch
  ! git branch -a | grep -q "\* master" && return
  ### compare commit hash
  git fetch -q
  origin=$(git rev-parse --short=8 origin/master)
  head=$(git rev-parse --short=8 HEAD)
  if [ "${origin}" != "${head}" ]; then
    echo "true"
  fi
}

#print_unkown_cmd(){
#  ERROR_MSG="Invalid command!"
#}
#invalid_option(){
#  ERROR_MSG="Invalid command!"
#}

#print_msg(){
#  if [ -n "${ERROR_MSG}" ]; then
#    echo -e "${red}"
#    echo -e "#########################################################"
#    echo -e " ${ERROR_MSG} "
#    echo -e "#########################################################"
#    echo -e "${white}"
#  fi
#  if [ -n "${CONFIRM_MSG}" ]; then
#    echo -e "${green}"
#    echo -e "#########################################################"
#    echo -e " ${CONFIRM_MSG} "
#    echo -e "#########################################################"
#    echo -e "${white}"
#  fi
#}
#
#clear_msg(){
#  unset CONFIRM_MSG
#  unset ERROR_MSG
#}

check_euid
set_globals
init_ini
kiauh_update_avail
main_menu
