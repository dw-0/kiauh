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

### base variables
PGC_FOR_KLIPPER_REPO="https://github.com/Kragrathea/pgcode"
PGC_DIR="${HOME}/pgcode"

#=================================================#
#================== INSTALL PGC ==================#
#=================================================#

function install_pgc_for_klipper(){
  pgconfsrc="${PGC_DIR}/pgcode.local.conf"
  pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"
  pgc_default_port="7136"

  status_msg "Installing PrettyGCode for Klipper ..."
  ### let the user decide which port is used
  echo -e "${cyan}\n###### On which port should PrettyGCode run? (Default: ${pgc_default_port})${white} "
  read -e -p "${cyan}###### Port:${white} " -i "${pgc_default_port}" pgc_custom_port
  ### check nginx dependency
  dep=(nginx)
  dependency_check
  ### clone repo
  [ -d "${PGC_DIR}" ] && rm -rf "${PGC_DIR}"
  cd "${HOME}" && git clone "${PGC_FOR_KLIPPER_REPO}"
  ### copy nginx config into destination directory
  sudo cp "${pgconfsrc}" "${pgconf}"
  ### replace default pi user in case the user is called different
  sudo sed -i "s|/home/pi/pgcode;|/home/${USER}/pgcode;|" "${pgconf}"
  ### replace default port
  if [ "${pgc_custom_port}" != "${pgc_default_port}" ]; then
    sudo sed -i "s|listen ${pgc_default_port};|listen ${pgc_custom_port};|" "${pgconf}"
    sudo sed -i "s|listen \[::\]:${pgc_default_port};|listen \[::\]:${pgc_custom_port};|" "${pgconf}"
  fi
  ### create symlink
  [ ! -L "${pgconfsl}" ] && sudo ln -s "${pgconf}" "${pgconfsl}"
  sudo systemctl restart nginx
  ### show URI
  pgc_uri="http://$(hostname -I | cut -d" " -f1):${pgc_custom_port}"
  echo -e "${cyan}\n● Accessible via:${white} ${pgc_uri}"
  ok_msg "PrettyGCode for Klipper installed!\n"
}

#=================================================#
#=================== REMOVE PGC ==================#
#=================================================#

function remove_prettygcode(){
  pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"
  if [ -d "${HOME}/pgcode" ] || [ -f "${pgconf}" ] || [ -L "${pgconfsl}" ]; then
    status_msg "Removing PrettyGCode for Klipper ..."
    rm -rf "${HOME}/pgcode"
    sudo rm -f "${pgconf}"
    sudo rm -f "${pgconfsl}"
    sudo systemctl restart nginx
    CONFIRM_MSG="PrettyGCode for Klipper successfully removed!"
  else
    ERROR_MSG="PrettyGCode for Klipper not found!\n Skipping..."
  fi
}

#=================================================#
#=================== UPDATE PGC ==================#
#=================================================#

function update_pgc_for_klipper(){
  PGC_DIR="${HOME}/pgcode"
  status_msg "Updating PrettyGCode for Klipper ..."
  cd "${PGC_DIR}" && git pull
  ok_msg "Update complete!"
}

#=================================================#
#=================== PGC STATUS ==================#
#=================================================#

function read_pgc_versions(){
  PGC_DIR="${HOME}/pgcode"
  if [ -d "${PGC_DIR}" ] && [ -d "${PGC_DIR}/.git" ]; then
    cd "${PGC_DIR}"
    git fetch origin main -q
    LOCAL_PGC_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_PGC_COMMIT=$(git describe origin/main --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_PGC_COMMIT=${NONE}
    REMOTE_PGC_COMMIT=${NONE}
  fi
}

function compare_pgc_versions(){
  unset PGC_UPDATE_AVAIL
  read_pgc_versions
  if [ "${LOCAL_PGC_COMMIT}" != "${REMOTE_PGC_COMMIT}" ]; then
    LOCAL_PGC_COMMIT="${yellow}$(printf "%-12s" "${LOCAL_PGC_COMMIT}")${white}"
    REMOTE_PGC_COMMIT="${green}$(printf "%-12s" "${REMOTE_PGC_COMMIT}")${white}"
    # add PGC to the update all array for the update all function in the updater
    PGC_UPDATE_AVAIL="true" && update_arr+=(update_pgc_for_klipper)
  else
    LOCAL_PGC_COMMIT="${green}$(printf "%-12s" "${LOCAL_PGC_COMMIT}")${white}"
    REMOTE_PGC_COMMIT="${green}$(printf "%-12s" "${REMOTE_PGC_COMMIT}")${white}"
    PGC_UPDATE_AVAIL="false"
  fi
}