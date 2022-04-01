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
SYSTEMD="/etc/systemd/system"
INITD="/etc/init.d"
ETCDEF="/etc/default"
KLIPPY_ENV="${HOME}/klippy-env"
KLIPPER_DIR="${HOME}/klipper"
KLIPPER_REPO="https://github.com/Klipper3d/klipper.git"
KLIPPER_CONFIG="${HOME}/klipper_config"

#=================================================#
#================ INSTALL KLIPPER ================#
#=================================================#

### check for existing klipper service installations
function klipper_initd() {
  local services
  services=$(find "${INITD}" -maxdepth 1 -regextype posix-extended -regex "${INITD}/klipper(-[^0])?[0-9]*")
  echo "${services}"
}

function klipper_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/klipper(-[^0])?[0-9]*.service")
  echo "${services}"
}

function klipper_exists() {
  local services
  [ -n "$(klipper_initd)" ] && services+="$(klipper_initd) "
  [ -n "$(klipper_systemd)" ] && services+="$(klipper_systemd)"
  echo "${services}"
}

function klipper_setup_dialog(){
  status_msg "Initializing Klipper installation ..."

  ### return early if klipper already exists
  if [ -n "$(klipper_exists)" ]; then
    local error="At least one Klipper service is already installed:"
    for s in $(klipper_exists); do
      error="${error}\n ➔ ${s}"
    done
    print_error "${error}" && return
  fi

  ### ask for amount of instances to create
  top_border
  echo -e "| Please select the number of Klipper instances to set  |"
  echo -e "| up. The number of Klipper instances will determine    |"
  echo -e "| the amount of printers you can run from this machine. |"
  blank_line
  echo -e "| ${yellow}WARNING: There is no limit on the number of instances${white} |"
  echo -e "| ${yellow}you can set up with this script. Setting up too many${white}  |"
  echo -e "| ${yellow}Klipper instances can potentially crash your system.${white}  |"
  bottom_border

  local count
  while [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; do
    read -p "${cyan}###### Number of Klipper instances to set up:${white} " count
    if [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; then
      error_msg "Invalid input!\n"
    else
      echo
      read -p "${cyan}###### Install ${count} instance(s)? (Y/n):${white} " yn
      case "${yn}" in
        Y|y|Yes|yes|"")
          select_msg "Yes"
          status_msg "Installing ${count} Klipper instance(s) ... \n"
          klipper_setup "${count}"
          break;;
        N|n|No|no)
          select_msg "No"
          abort_msg "Exiting Klipper setup ...\n"
          break;;
        *)
          print_error "Invalid command!"
          ;;
      esac
    fi
  done
}

function install_klipper_packages(){
  local packages
  local install_script="${HOME}/klipper/scripts/install-octopi.sh"

  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"
  ### add dbus requirement for DietPi distro
  [ -e "/boot/dietpi/.version" ] && packages+=" dbus"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package info
  status_msg "Updating lists of packages..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install required packages
  status_msg "Installing packages..."
  sudo apt-get install --yes "${packages[@]}"
}

function create_klipper_virtualenv(){
  status_msg "Installing python virtual environment..."
  ### always create a clean virtualenv
  [ -d "${KLIPPY_ENV}" ] && rm -rf "${KLIPPY_ENV}"
  virtualenv -p python2 "${KLIPPY_ENV}"
  "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}"/scripts/klippy-requirements.txt
}

function klipper_setup(){
  local instances=${1}
  ### checking dependencies
  local dep=(git)
  dependency_check "${dep[@]}"

  ### step 1: clone klipper
  status_msg "Downloading Klipper ..."
  ### force remove existing klipper dir and clone into fresh klipper dir
  [ -d "${KLIPPER_DIR}" ] && rm -rf "${KLIPPER_DIR}"
  cd "${HOME}" && git clone "${KLIPPER_REPO}"

  ### step 2: install klipper dependencies and create python virtualenv
  install_klipper_packages
  create_klipper_virtualenv

  ### step 3: create gcode_files and logs folder
  [ ! -d "${HOME}/gcode_files" ] && mkdir -p "${HOME}/gcode_files"
  [ ! -d "${HOME}/klipper_logs" ] && mkdir -p "${HOME}/klipper_logs"

  ### step 4: create klipper instances
  create_klipper_service "${instances}"

  ### step 5: enable and start all instances
  do_action_service "enable" "klipper"
  do_action_service "start" "klipper"

  ### confirm message
  if [[ ${instances} -eq 1 ]]; then
    local confirm="Klipper has been set up!"
  elif [[ ${instances} -gt 1 ]]; then
    local confirm="${instances} Klipper instances have been set up!"
  fi
  print_confirm "${confirm}" && return
}

function write_klipper_service(){
  local i=${1} cfg_dir=${2} cfg=${3} log=${4} printer=${5} uds=${6} service=${7}
  local service_template="${SRCDIR}/kiauh/resources/klipper.service"
  local cfg_template="${SRCDIR}/kiauh/resources/printer.cfg"

  ### create a config directory if it doesn't exist
  [ ! -d "${cfg_dir}" ] && mkdir -p "${cfg_dir}"

  ### create a minimal config if there is no printer.cfg
  [ ! -f "${cfg}" ] && cp "${cfg_template}" "${cfg}"

  ### replace all placeholders
  if [ ! -f "${service}" ]; then
    status_msg "Creating Klipper Service ${i} ..."
    sudo cp "${service_template}" "${service}"

    [ -z "${i}" ] && sudo sed -i "s|instance %INST% ||" "${service}"
    [ -n "${i}" ] && sudo sed -i "s|%INST%|${i}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%ENV%|${KLIPPY_ENV}|; s|%DIR%|${KLIPPER_DIR}|" "${service}"
    sudo sed -i "s|%LOG%|${log}|; s|%CFG%|${cfg}|; s|%PRINTER%|${printer}|; s|%UDS%|${uds}|" "${service}"
  fi
}

function create_klipper_service(){
  local instances=${1}
  if [ "${instances}" -eq 1 ]; then
    local i=""
    local cfg_dir="${KLIPPER_CONFIG}"
    local cfg="${cfg_dir}/printer.cfg"
    local log="${HOME}/klipper_logs/klippy.log"
    local printer="/tmp/printer"
    local uds="/tmp/klippy_uds"
    local service="${SYSTEMD}/klipper.service"
    ### write single instance service
    write_klipper_service "${i}" "${cfg_dir}" "${cfg}" "${log}" "${printer}" "${uds}" "${service}"
    ok_msg "Single Klipper instance created!"
  elif [ "${instances}" -gt 1 ]; then
    local i=1
    while [ "${i}" -le "${instances}" ]; do
      local cfg_dir="${KLIPPER_CONFIG}/printer_${i}"
      local cfg="${cfg_dir}/printer.cfg"
      local log="${HOME}/klipper_logs/klippy-${i}.log"
      local printer="/tmp/printer-${i}"
      local uds="/tmp/klippy_uds-${i}"
      local service="${SYSTEMD}/klipper-${i}.service"
      ### write multi instance service
      write_klipper_service "${i}" "${cfg_dir}" "${cfg}" "${log}" "${printer}" "${uds}" "${service}"
      ok_msg "Klipper instance #${i} created!"
      i=$((i+1))
    done && unset i
  else
    return 1
  fi
}

#================================================#
#================ REMOVE KLIPPER ================#
#================================================#

function remove_klipper_sysvinit() {
  [ ! -e "${INITD}/klipper" ] && return
  status_msg "Removing Klipper SysVinit service ..."
  sudo systemctl stop klipper
  sudo update-rc.d -f klipper remove
  sudo rm -f "${INITD}/klipper" "${ETCDEF}/klipper"
  ok_msg "Klipper SysVinit service removed!"
}

function remove_klipper_systemd() {
  [ -z "$(klipper_systemd)" ] && return
  status_msg "Removing Klipper Systemd Services ..."
  for service in $(klipper_systemd | cut -d"/" -f5)
  do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done
  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
  ok_msg "Klipper Service removed!"
}

function remove_klipper_logs() {
  local files
  files=$(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/klippy(-[^0])?[0-9]*\.log(.*)?")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_klipper_uds() {
  local files
  files=$(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/klippy_uds(-[^0])?[0-9]*")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_klipper_printer() {
  local files
  files=$(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/printer(-[^0])?[0-9]*")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_klipper_dir() {
  [ ! -d "${KLIPPER_DIR}" ] && return
  status_msg "Removing Klipper directory ..."
  rm -rf "${KLIPPER_DIR}"
  ok_msg "Directory removed!"
}

function remove_klipper_env() {
  [ ! -d "${KLIPPY_ENV}" ] && return
  status_msg "Removing klippy-env directory ..."
  rm -rf "${KLIPPY_ENV}"
  ok_msg "Directory removed!"
}

function remove_klipper(){
  remove_klipper_sysvinit
  remove_klipper_systemd
  remove_klipper_logs
  remove_klipper_uds
  remove_klipper_printer
  remove_klipper_dir
  remove_klipper_env

  local confirm="Klipper was successfully removed!"
  print_confirm "${confirm}" && return
}

#================================================#
#================ UPDATE KLIPPER ================#
#================================================#

function update_klipper(){
  do_action_service "stop" "klipper"
  if [ ! -d "${KLIPPER_DIR}" ]; then
    cd "${HOME}" && git clone "${KLIPPER_REPO}"
  else
    bb4u "klipper"
    status_msg "Updating Klipper ..."
    cd "${KLIPPER_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages
    ### install possible new python dependencies
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}/scripts/klippy-requirements.txt"
  fi
  update_log_paths "klipper"
  ok_msg "Update complete!"
  do_action_service "restart" "klipper"
}

#================================================#
#================ KLIPPER STATUS ================#
#================================================#

function get_klipper_status(){
  local sf_count status
  sf_count="$(klipper_systemd | wc -w)"
  ### detect an existing "legacy" klipper init.d installation
  if [ "$(klipper_systemd | wc -w)" -eq 0 ] \
  && [ "$(klipper_initd | wc -w)" -ge 1 ]; then
    sf_count=1
  fi

  ### remove the "SERVICE" entry from the data array if a klipper service is installed
  local data_arr=(SERVICE "${KLIPPER_DIR}" "${KLIPPY_ENV}")
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

function get_local_klipper_commit(){
  [ ! -d "${KLIPPER_DIR}" ] || [ ! -d "${KLIPPER_DIR}"/.git ] && return
  cd "${KLIPPER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_klipper_commit(){
  [ ! -d "${KLIPPER_DIR}" ] || [ ! -d "${KLIPPER_DIR}"/.git ] && return
  cd "${KLIPPER_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_klipper_versions(){
  unset KLIPPER_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_klipper_commit)"
  remote_ver="$(get_remote_klipper_commit)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add klipper to the update all array for the update all function in the updater
    KLIPPER_UPDATE_AVAIL="true" && update_arr+=(update_klipper)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    KLIPPER_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}