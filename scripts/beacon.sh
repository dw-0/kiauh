#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

#=======================================================================#
# Script to run Beacon Installer by lraithel15133                       #
# https://github.com/beacon3d/beacon_klipper                            #
#=======================================================================#

set -e

#=================================================#
#================ INSTALL BEACON =================#
#=================================================#

function install_beacon() {
  local repo="https://github.com/beacon3d/beacon_klipper.git"
  local install_script="./beacon_klipper/install.sh"

  ### return early if beacon_klipper directory already exists
  if [[ -d "${HOME}/beacon_klipper" ]]; then
    echo "Looks like Beacon is already installed! Please remove it first before you try to re-install it!"
    return
  fi

  echo "Initializing Beacon installation ..."

  ### step 1: clone beacon_klipper
  echo "Cloning Beacon from ${repo} ..."
  cd "${HOME}" || exit 1
  if ! git clone "${repo}"; then
    echo "Cloning Beacon from ${repo} failed!"
    exit 1
  fi
  echo "Cloning complete!"

  ### step 2: run install script
  echo "Running Beacon install script ..."
  cd beacon_klipper || exit 1
  if ! bash install.sh; then
    echo "Beacon installation failed!"
    exit 1
  fi
  echo "Beacon installation complete!"
}

#=================================================#
#================ REMOVE BEACON ==================#
#=================================================#

function remove_beacon() {
  ### remove beacon_klipper directory
  if [[ -d "${HOME}/beacon_klipper" ]]; then
    echo "Removing Beacon directory ..."
    rm -rf "${HOME}/beacon_klipper"
    echo "Beacon directory removed!"
  else
    echo "Beacon is not installed."
  fi

  ### remove beacon.py from extras folder
  if [[ -f "${HOME}/klipper/klippy/extras/beacon.py" ]]; then
    echo "Removing beacon.py from extras folder ..."
    rm -f "${HOME}/klipper/klippy/extras/beacon.py"
    echo "beacon.py removed!"
  fi
}

#=================================================#
#=============== COMPARE VERSIONS ================#
#=================================================#

function compare_beacon_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_beacon_commit)"
  remote_ver="$(get_remote_beacon_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add beacon to application_updates_available
    add_to_application_updates "beacon"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}

function get_local_beacon_commit() {
  [[ ! -d ${HOME}/beacon_klipper || ! -d "${HOME}/beacon_klipper/.git" ]] && return

  local commit
  cd "${HOME}/beacon_klipper"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_beacon_commit() {
  [[ ! -d ${HOME}/beacon_klipper || ! -d "${HOME}/beacon_klipper/.git" ]] && return

  local commit
  cd "${HOME}/beacon_klipper" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function update_beacon() {
  local beacon_dir="${HOME}/beacon_klipper"

  if [[ ! -d ${beacon_dir} ]]; then
    clone_crowsnest
  else
    status_msg "Updating Beacon ..."
    cd "${beacon_dir}" && git pull
  fi
  ok_msg "Update complete!"
}

#=================================================#
#=============== GET BEACON STATUS ===============#
#=================================================#

function get_beacon_status() {
  local -a files
  files=(
      "${HOME}/beacon_klipper"
      "${HOME}/klipper/klippy/extras/beacon.py"
    )

  local count
  count=0

  for file in "${files[@]}"; do
    [[ -e "${file}" ]] && count=$(( count + 1 ))
  done

  if [[ "${count}" -eq "${#files[*]}" ]]; then
    echo "Installed"
  elif [[ "${count}" -gt 0 ]]; then
    echo "Incomplete!"
  else
    echo "Not installed!"
  fi
}
