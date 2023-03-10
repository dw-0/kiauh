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

#=================================================#
#================== INSTALL PGC ==================#
#=================================================#

function install_pgc_for_klipper() {
  local pgconfsrc="${PGC_DIR}/pgcode.local.conf"
  local pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  local pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"
  local pgc_uri pgc_custom_port pgc_default_port="7136"

  status_msg "Installing PrettyGCode for Klipper ..."
  echo -e "${cyan}\n###### On which port should PrettyGCode run? (Default: ${pgc_default_port})${white} "
  read -e -p "${cyan}###### Port:${white} " -i "${pgc_default_port}" pgc_custom_port

  ### check nginx dependency
  local dep=(nginx)
  dependency_check "${dep[@]}"

  [[ -d ${PGC_DIR} ]] && rm -rf "${PGC_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${PGC_REPO}" "${PGC_DIR}"; then
    print_error "Cloning PrettyGCode for Klipper from\n ${PGC_REPO}\n failed!"
    exit 1
  fi

  sudo cp "${pgconfsrc}" "${pgconf}"
  sudo sed -i "s|/home/pi/pgcode;|${HOME}/pgcode;|" "${pgconf}"

  ### replace default port
  if (( pgc_custom_port != pgc_default_port )); then
    sudo sed -i "s|listen ${pgc_default_port};|listen ${pgc_custom_port};|" "${pgconf}"
    sudo sed -i "s|listen \[::\]:${pgc_default_port};|listen \[::\]:${pgc_custom_port};|" "${pgconf}"
  fi

  [[ ! -L ${pgconfsl} ]] && sudo ln -s "${pgconf}" "${pgconfsl}"
  sudo systemctl restart nginx

  pgc_uri="http://$(hostname -I | cut -d" " -f1):${pgc_custom_port}"
  echo -e "${cyan}\n● Accessible via:${white} ${pgc_uri}"
  ok_msg "PrettyGCode for Klipper installed!\n"
}

#=================================================#
#=================== REMOVE PGC ==================#
#=================================================#

function remove_prettygcode() {
  local pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  local pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"

  if [[ -d ${PGC_DIR} || -f ${pgconf} || -L ${pgconfsl} ]]; then
    status_msg "Removing PrettyGCode for Klipper ..."
    rm -rf "${PGC_DIR}"
    sudo rm -f "${pgconf}"
    sudo rm -f "${pgconfsl}"
    sudo systemctl restart nginx
    print_confirm "PrettyGCode for Klipper successfully removed!"
  else
    print_error "PrettyGCode for Klipper not found!\n Skipping..."
  fi
}

#=================================================#
#=================== UPDATE PGC ==================#
#=================================================#

function update_pgc_for_klipper() {
  [[ ! -d ${PGC_DIR} ]] && return

  status_msg "Updating PrettyGCode for Klipper ..."
  cd "${PGC_DIR}" && git pull
  ok_msg "Update complete!"
}

#=================================================#
#=================== PGC STATUS ==================#
#=================================================#

function get_local_prettygcode_commit() {
  local commit

  [[ ! -d ${PGC_DIR} || ! -d "${PGC_DIR}/.git" ]] && return
  cd "${PGC_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_prettygcode_commit() {
  local commit

  [[ ! -d ${PGC_DIR} || ! -d "${PGC_DIR}/.git" ]] && return
  cd "${PGC_DIR}" && git fetch origin -q
  commit=$(git describe origin/main --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_prettygcode_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_prettygcode_commit)"
  remote_ver="$(get_remote_prettygcode_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "pgc_for_klipper"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}