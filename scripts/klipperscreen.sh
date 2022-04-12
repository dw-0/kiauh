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

function install_klipperscreen(){
  python3_check
  if [ "${py_chk_ok}" = "true" ]; then
    klipperscreen_setup
    restart_klipperscreen
  else
    ERROR_MSG="Python 3.7 or above required!\n Please upgrade your Python version first."
    print_msg && clear_msg
  fi
}

function python3_check(){
  status_msg "Your Python 3 version is: $(python3 --version)"
  major=$(python3 --version | cut -d" " -f2 | cut -d"." -f1)
  minor=$(python3 --version | cut -d"." -f2)
  if [ "${major}" -ge 3 ] && [ "${minor}" -ge 7 ]; then
    ok_msg "Python version ok!"
    py_chk_ok="true"
  else
    py_chk_ok="false"
  fi
}

function klipperscreen_setup(){
  dep=(wget curl unzip dfu-util)
  dependency_check
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
  source_kiauh_ini

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
    sudo systemctl stop KlipperScreen
    sudo systemctl disable KlipperScreen
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

  CONFIRM_MSG="KlipperScreen successfully removed!"
}

#===================================================#
#=============== UPDATE KLIPPERSCREEN ==============#
#===================================================#

function update_klipperscreen(){
  stop_klipperscreen
  cd "${KLIPPERSCREEN_DIR}"
  KLIPPERSCREEN_OLDREQ_MD5SUM=$(md5sum "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt" | cut -d " " -f1)
  git pull origin master -q && ok_msg "Fetch successfull!"
  git checkout -f master && ok_msg "Checkout successfull"
  #KLIPPERSCREEN_NEWREQ_MD5SUM=$(md5sum $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt)
  if [[ $(md5sum "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt" | cut -d " " -f1) != "${KLIPPERSCREEN_OLDREQ_MD5SUM}" ]]; then
    status_msg "New dependecies detected..."
    PYTHONDIR="${HOME}/.KlipperScreen-env"
    "${PYTHONDIR}"/bin/pip install -r "${KLIPPERSCREEN_DIR}/scripts/KlipperScreen-requirements.txt"
    ok_msg "Dependencies have been installed!"
  fi
  ok_msg "Update complete!"
  start_klipperscreen
}

#===================================================#
#=============== KLIPPERSCREEN STATUS ==============#
#===================================================#

function klipperscreen_status(){
  klsccount=0
  klipperscreen_data=(
    SERVICE
    "${KLIPPERSCREEN_DIR}"
    "${KLIPPERSCREEN_ENV_DIR}"
  )

  ### count amount of klipperscreen_data service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "KlipperScreen" | wc -l)

  ### remove the "SERVICE" entry from the klipperscreen_data array if a KlipperScreen service is installed
  [ "${SERVICE_FILE_COUNT}" -gt 0 ] && unset "klipperscreen_data[0]"

  #count+1 for each found data-item from array
  for klscd in "${klipperscreen_data[@]}"
  do
    if [ -e "${klscd}" ]; then
      klsccount=$((klsccount + 1))
    fi
  done
  if [ "${klsccount}" == "${#klipperscreen_data[*]}" ]; then
    KLIPPERSCREEN_STATUS="${green}Installed!${white}      "
  elif [ "${klsccount}" == 0 ]; then
    KLIPPERSCREEN_STATUS="${red}Not installed!${white}  "
  else
    KLIPPERSCREEN_STATUS="${yellow}Incomplete!${white}     "
  fi
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
