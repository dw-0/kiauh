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

#===================================================#
#============== INSTALL KLIPPERSCREEN ==============#
#===================================================#

function klipperscreen_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/KlipperScreen.service")
  echo "${services}"
}

function install_klipperscreen(){
  ### return early if python version check fails
  if [ "$(python3_check)" == "false" ]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  ### install KlipperScreen
  klipperscreen_setup

  ### add klipperscreen to the update manager in moonraker.conf
  patch_klipperscreen_update_manager

  do_action_service "restart" "KlipperScreen"
}

function klipperscreen_setup(){
  local dep=(wget curl unzip dfu-util)
  dependency_check "${dep[@]}"
  status_msg "Downloading KlipperScreen ..."
  # force remove existing KlipperScreen dir
  [ -d "${KLIPPERSCREEN_DIR}" ] && rm -rf "${KLIPPERSCREEN_DIR}"
  # clone into fresh KlipperScreen dir
  cd "${HOME}" && git clone "${KLIPPERSCREEN_REPO}"
  ok_msg "Download complete!"
  status_msg "Installing KlipperScreen ..."
  /bin/bash "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-install.sh"
  ok_msg "KlipperScreen successfully installed!"
}

#===================================================#
#=============== REMOVE KLIPPERSCREEN ==============#
#===================================================#

function remove_klipperscreen(){
  ### remove KlipperScreen dir
  if [ -d "${KLIPPERSCREEN_DIR}" ]; then
    status_msg "Removing KlipperScreen directory ..."
    rm -rf "${KLIPPERSCREEN_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove KlipperScreen VENV dir
  if [ -d "${KLIPPERSCREEN_ENV_DIR}" ]; then
    status_msg "Removing KlipperScreen VENV directory ..."
    rm -rf "${KLIPPERSCREEN_ENV_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove KlipperScreen service
  if [ -e "${SYSTEMD}/KlipperScreen.service" ]; then
    status_msg "Removing KlipperScreen service ..."
    do_action_service "stop" "KlipperScreen"
    do_action_service "disable" "KlipperScreen"
    sudo rm -f "${SYSTEMD}/KlipperScreen.service"
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "KlipperScreen Service removed!"
  fi

  ### remove KlipperScreen log
  if [ -e "/tmp/KlipperScreen.log" ]; then
    status_msg "Removing KlipperScreen log file ..."
    rm -f "/tmp/KlipperScreen.log" && ok_msg "File removed!"
  fi

  ### remove KlipperScreen log symlink in config dir

  if [ -e "${KLIPPER_CONFIG}/KlipperScreen.log" ]; then
    status_msg "Removing KlipperScreen log symlink ..."
    rm -f "${KLIPPER_CONFIG}/KlipperScreen.log" && ok_msg "File removed!"
  fi

  print_confirm "KlipperScreen successfully removed!"
}

#===================================================#
#=============== UPDATE KLIPPERSCREEN ==============#
#===================================================#

function update_klipperscreen(){
  local old_md5
  old_md5=$(md5sum "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt" | cut -d " " -f1)

  do_action_service "stop" "KlipperScreen"
  cd "${KLIPPERSCREEN_DIR}"
  git pull origin master -q && ok_msg "Fetch successfull!"
  git checkout -f master && ok_msg "Checkout successfull"
  if [[ $(md5sum "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt" | cut -d " " -f1) != "${old_md5}" ]]; then
    status_msg "New dependecies detected..."
    PYTHONDIR="${HOME}/.KlipperScreen-env"
    "${PYTHONDIR}"/bin/pip install -r "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt"
    ok_msg "Dependencies have been installed!"
  fi
  ok_msg "Update complete!"
  do_action_service "start" "KlipperScreen"
}

#===================================================#
#=============== KLIPPERSCREEN STATUS ==============#
#===================================================#

function klipperscreen_status(){
  local sf_count status
  sf_count="$(klipperscreen_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${KLIPPERSCREEN_DIR}" "${KLIPPERSCREEN_ENV_DIR}")
  [ "${sf_count}" -gt 0 ] && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [ -e "${data}" ] && filecount=$(("${filecount}" + 1))
  done

  if [ "${filecount}" == "${#data_arr[*]}" ]; then
    status="$(printf "${green}Installed: %-5s${white}" "${sf_count}")"
  elif [ "${filecount}" == 0 ]; then
    status="${red}Not installed!${white}  "
  else
    status="${yellow}Incomplete!${white}     "
  fi
  echo "${status}"
}

function get_local_klipperscreen_commit(){
  local commit
  [ ! -d "${KLIPPERSCREEN_DIR}" ] || [ ! -d "${KLIPPERSCREEN_DIR}"/.git ] && return
  cd "${KLIPPERSCREEN_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_klipperscreen_commit(){
  local commit
  [ ! -d "${KLIPPERSCREEN_DIR}" ] || [ ! -d "${KLIPPERSCREEN_DIR}"/.git ] && return
  cd "${KLIPPERSCREEN_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_klipperscreen_versions(){
  unset KLIPPERSCREEN_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_klipperscreen_commit)"
  remote_ver="$(get_remote_klipperscreen_commit)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add klipperscreen to the update all array for the update all function in the updater
    KLIPPERSCREEN_UPDATE_AVAIL="true" && update_arr+=(update_klipperscreen)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    KLIPPERSCREEN_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function patch_klipperscreen_update_manager(){
  local moonraker_configs
  moonraker_configs=$(find "$(get_klipper_cfg_dir)" -type f -name "moonraker.conf")
  for conf in ${moonraker_configs}; do
    status_msg "Adding KlipperScreen to update manager in file:\n       ${conf}"
    ### add new line to conf if it doesn't end with one
    [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"
    ### add KlipperScreens update manager section to moonraker.conf
    if grep -Eq "[update_manager KlipperScreen]" "${conf}"; then
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF

[update_manager KlipperScreen]
type: git_repo
path: ${HOME}/KlipperScreen
origin: https://github.com/jordanruthe/KlipperScreen.git
env: ${HOME}/.KlipperScreen-env/bin/python
requirements: scripts/KlipperScreen-requirements.txt
install_script: scripts/KlipperScreen-install.sh
MOONRAKER_CONF
    fi
  done
}
