#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

#
# This file is written and maintained by Patrick Schmidt author of Mobileraker
# It is based of the kliperscreen.sh install script!


set -e

#===================================================#
#========== INSTALL MOBILERAKER COMPANION ==========#
#===================================================#

function mobileraker_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/mobileraker.service")
  echo "${services}"
}

function install_mobileraker() {
  ### return early if python version check fails
  if [[ $(python3_check) == "false" ]]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  ### first, we create a backup of the full klipper_config dir - safety first!
  backup_klipper_config_dir

  ### install Mobileraker's Companion
  mobileraker_setup

  ### add Mobileraker's Companion to the update manager in moonraker.conf
  patch_mobileraker_update_manager

  do_action_service "restart" "mobileraker"
}

function mobileraker_setup() {
  local dep=(wget curl unzip dfu-util)
  dependency_check "${dep[@]}"
  status_msg "Cloning Mobileraker's companion from ${MOBILERAKER_REPO} ..."

  # force remove existing Mobileraker's companion dir
  [[ -d ${MOBILERAKER_DIR} ]] && rm -rf "${MOBILERAKER_DIR}"

  # clone into fresh Mobileraker's companion dir
  cd "${HOME}" || exit 1
  if ! git clone "${MOBILERAKER_REPO}" "${MOBILERAKER_DIR}"; then
    print_error "Cloning mobileraker's companion from\n ${MOBILERAKER_REPO}\n failed!"
    exit 1
  fi

  status_msg "Installing Mobileraker's companion ..."
  if "${MOBILERAKER_DIR}"/scripts/install-mobileraker-companion.sh; then
    ok_msg "Mobileraker's companion successfully installed!"
  else
    print_error "Mobileraker's companion installation failed!"
    exit 1
  fi
}

#===================================================#
#=========== REMOVE MOBILERAKER COMPANION ==========#
#===================================================#

function remove_mobileraker() {
  ### remove Mobileraker's companion dir
  if [[ -d ${MOBILERAKER_DIR} ]]; then
    status_msg "Removing Mobileraker's companion directory ..."
    rm -rf "${MOBILERAKER_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove Mobileraker's companion VENV dir
  if [[ -d ${MOBILERAKER_ENV} ]]; then
    status_msg "Removing Mobileraker's companion VENV directory ..."
    rm -rf "${MOBILERAKER_ENV}" && ok_msg "Directory removed!"
  fi

  ### remove Mobileraker's companion service
  if [[ -e "${SYSTEMD}/mobileraker.service" ]]; then
    status_msg "Removing mobileraker service ..."
    do_action_service "stop" "mobileraker"
    do_action_service "disable" "mobileraker"
    sudo rm -f "${SYSTEMD}/mobileraker.service"

    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "Mobileraker's companion Service removed!"
  fi


  remove_mobileraker_logs

  print_confirm "Mobileraker's companion successfully removed!"
}

function remove_mobileraker_logs() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/mobileraker\.log.*"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

#===================================================#
#=========== UPDATE MOBILERAKER COMPANION ==========#
#===================================================#

function update_mobileraker() {
  local old_md5
  old_md5=$(md5sum "${MOBILERAKER_DIR}/scripts/mobileraker-requirements.txt" | cut -d " " -f1)

  do_action_service "stop" "mobileraker"
  cd "${MOBILERAKER_DIR}"
  git pull origin main -q && ok_msg "Fetch successfull!"
  git checkout -f main && ok_msg "Checkout successfull"

  if [[ $(md5sum "${MOBILERAKER_DIR}/scripts/mobileraker-requirements.txt" | cut -d " " -f1) != "${old_md5}" ]]; then
    status_msg "New dependecies detected..."
    "${MOBILERAKER_ENV}"/bin/pip install -r "${MOBILERAKER_DIR}/scripts/mobileraker-requirements.txt"
    ok_msg "Dependencies have been installed!"
  fi

  ok_msg "Update complete!"
  do_action_service "start" "mobileraker"
}

#===================================================#
#=========== MOBILERAKER COMPANION STATUS ==========#
#===================================================#

function get_mobileraker_status() {
  local sf_count status
  sf_count="$(mobileraker_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${MOBILERAKER_DIR}" "${MOBILERAKER_ENV}")
  (( sf_count > 0 )) && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && filecount=$(( filecount + 1 ))
  done

  if (( filecount == ${#data_arr[*]} )); then
    status="Installed!"
  elif (( filecount == 0 )); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi
  echo "${status}"
}

function get_local_mobileraker_commit() {
  [[ ! -d ${MOBILERAKER_DIR} || ! -d "${MOBILERAKER_DIR}/.git" ]] && return

  local commit
  cd "${MOBILERAKER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_mobileraker_commit() {
  [[ ! -d ${MOBILERAKER_DIR} || ! -d "${MOBILERAKER_DIR}/.git" ]] && return

  local commit
  cd "${MOBILERAKER_DIR}" && git fetch origin -q
  commit=$(git describe origin/main --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_mobileraker_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_mobileraker_commit)"
  remote_ver="$(get_remote_mobileraker_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "mobileraker"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function patch_mobileraker_update_manager() {
  local patched moonraker_configs regex
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  patched="false"
  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager mobileraker\]\s*$" "${conf}"; then
      ### add new line to conf if it doesn't end with one
      [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"

      ### add Mobileraker's Companion update manager section to moonraker.conf
      status_msg "Adding Mobileraker's Companion to update manager in file:\n       ${conf}"
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF

[update_manager mobileraker]
type: git_repo
path: ${HOME}/mobileraker_companion
origin: https://github.com/Clon1998/mobileraker_companion.git
primary_branch:main
managed_services: mobileraker
env: ${HOME}/mobileraker-env/bin/python
requirements: scripts/mobileraker-requirements.txt
install_script: scripts/install-mobileraker-companion.sh
MOONRAKER_CONF

    fi

    patched="true"
  done

  if [[ ${patched} == "true" ]]; then
    do_action_service "restart" "moonraker"
  fi
}
