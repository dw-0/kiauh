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
#================ INSTALL MOONRAKER ================#
#===================================================#

function moonraker_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker(-[^0])?[0-9]*.service")
  echo "${services}"
}

function moonraker_setup_dialog(){
  status_msg "Initializing Moonraker installation ..."

  ### return early if moonraker already exists
  if [ -n "$(moonraker_systemd)" ]; then
    local error="At least one Moonraker service is already installed:"
    for service in $(moonraker_systemd); do
      error="${error}\n ➔ ${service}"
    done
    print_error "${error}" && return
  fi

  ### return early if python version check fails
  if [ "$(python3_check)" == "false" ]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  local klipper_count
  klipper_count=$(klipper_systemd | wc -w)
  top_border
  if [ -f "${INITD}/klipper" ] || [ -f "${SYSTEMD}/klipper.service" ]; then
    printf "|${green}%-55s${white}|\n" " 1 Klipper instance was found!"
  elif [ "${klipper_count}" -gt 1 ]; then
    printf "|${green}%-55s${white}|\n" " ${klipper_count} Klipper instances were found!"
  else
    echo -e "| ${yellow}INFO: No existing Klipper installation found!${white}         |"
  fi
  echo -e "| Usually you need one Moonraker instance per Klipper   |"
  echo -e "| instance. Though you can install as many as you wish. |"
  bottom_border

  local count
  while [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; do
    read -p "${cyan}###### Number of Moonraker instances to set up:${white} " count
    if [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; then
      error_msg "Invalid Input!\n"
    else
      echo
      while true; do
        read -p "${cyan}###### Install ${count} instance(s)? (Y/n):${white} " yn
        case "${yn}" in
          Y|y|Yes|yes|"")
            select_msg "Yes"
            ((count == 1)) && status_msg "Installing single Moonraker instance ..."
            ((count > 1)) && status_msg "Installing ${count} Moonraker instances ..."
            moonraker_setup "${count}"
            break;;
          N|n|No|no)
            select_msg "No"
            error_msg "Exiting Moonraker setup ...\n"
            break;;
          *)
            error_msg "Invalid Input!\n";;
        esac
      done
    fi
  done
}

function install_moonraker_packages(){
  local packages
  local install_script="${HOME}/moonraker/scripts/install-moonraker.sh"

  ### read PKGLIST from official install script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package info
  status_msg "Updating lists of packages..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install required packages
  status_msg "Installing packages..."
  sudo apt-get install --yes "${packages[@]}"
}

function create_moonraker_virtualenv(){
  status_msg "Installing python virtual environment..."
  ### always create a clean virtualenv
  [ -d "${MOONRAKER_ENV}" ] && rm -rf "${MOONRAKER_ENV}"
  virtualenv -p /usr/bin/python3 "${MOONRAKER_ENV}"
  "${MOONRAKER_ENV}"/bin/pip install -r "${MOONRAKER_DIR}/scripts/moonraker-requirements.txt"
}

function moonraker_setup(){
  local confirm_msg instances=${1}
  ### checking dependencies
  local dep=(git wget curl unzip dfu-util virtualenv)
  ### additional required dependencies on armbian
  dep+=(libjpeg-dev zlib1g-dev)
  dependency_check "${dep[@]}"

  ### step 1: clone moonraker
  status_msg "Downloading Moonraker ..."
  ### force remove existing moonraker dir and clone into fresh moonraker dir
  [ -d "${MOONRAKER_DIR}" ] && rm -rf "${MOONRAKER_DIR}"
  cd "${HOME}" && git clone "${MOONRAKER_REPO}"

  ### step 2: install moonraker dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_moonraker_packages
  create_moonraker_virtualenv

  ### step 3: create moonraker.conf
  create_moonraker_conf "${instances}"

  ### step 4: create moonraker instances
  create_moonraker_service "${instances}"

  ### step 5: create polkit rules for moonraker
  moonraker_polkit || true

  ### step 6: enable and start all instances
  do_action_service "enable" "moonraker"
  do_action_service "start" "moonraker"

  ### confirm message
  [ "${instances}" -eq 1 ] && confirm_msg="Moonraker has been set up!"
  [ "${instances}" -gt 1 ] && confirm_msg="${instances} Moonraker instances have been set up!"
  print_confirm "${confirm_msg}"
  print_mr_ip_list "${instances}"
}

function create_moonraker_conf(){
  local lan instances=${1} log="${HOME}/klipper_logs"
  lan="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  if [ "${instances}" -eq 1 ]; then
    local cfg_dir="${KLIPPER_CONFIG}"
    local cfg="${cfg_dir}/moonraker.conf"
    local port=7125
    local db="${HOME}/.moonraker_database"
    local uds="/tmp/klippy_uds"
    ### write single instance config
    write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${log}" "${db}" "${uds}" "${lan}"
  elif [ "${instances}" -gt 1 ]; then
    local i=1 port=7125
    while [ "${i}" -le "${instances}" ]; do
      local cfg_dir="${KLIPPER_CONFIG}/printer_${i}"
      local cfg="${cfg_dir}/moonraker.conf"
      local db="${HOME}/.moonraker_database_${i}"
      local uds="/tmp/klippy_uds-${i}"
      ### write multi instance config
      write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${log}" "${db}" "${uds}" "${lan}"
      port=$((port+1))
      i=$((i+1))
    done
  else
    return 1
  fi
}

function write_moonraker_conf(){
  local cfg_dir=${1} cfg=${2} port=${3} log=${4} db=${5} uds=${6} lan=${7}
  local conf_template="${SRCDIR}/kiauh/resources/moonraker.conf"
  [ ! -d "${cfg_dir}" ] && mkdir -p "${cfg_dir}"

  if [ ! -f "${cfg}" ]; then
    status_msg "Creating moonraker.conf in ${cfg_dir} ..."
    cp "${conf_template}" "${cfg}"
    sed -i "s|%USER%|${USER}|g" "${cfg}"
    sed -i "s|%CFG%|${cfg_dir}|; s|%PORT%|${port}|; s|%LOG%|${log}|; s|%DB%|${db}|; s|%UDS%|${uds}|" "${cfg}"
    # if host ip is not in the default ip ranges replace placeholder,
    # otherwise remove placeholder from config
    if ! grep -q "${lan}" "${cfg}"; then
      sed -i "s|%LAN%|${lan}|" "${cfg}"
    else
      sed -i "/%LAN%/d" "${cfg}"
    fi
    ok_msg "moonraker.conf created!"
  else
    status_msg "File '${cfg_dir}/moonraker.conf' already exists!\nSkipping..."
  fi
}

function create_moonraker_service(){
  local instances=${1}
  if [ "${instances}" -eq 1 ]; then
    local i=""
    local cfg_dir="${KLIPPER_CONFIG}"
    local cfg="${cfg_dir}/moonraker.conf"
    local log="${HOME}/klipper_logs/moonraker.log"
    local service="${SYSTEMD}/moonraker.service"
    ### write single instance service
    write_moonraker_service "${i}" "${cfg_dir}" "${cfg}" "${log}" "${service}"
    ok_msg "Single Moonraker instance created!"
  elif [ "${instances}" -gt 1 ]; then
    local i=1
    while [ "${i}" -le "${instances}" ]; do
      local cfg_dir="${KLIPPER_CONFIG}/printer_${i}"
      local cfg="${cfg_dir}/moonraker.conf"
      local log="${HOME}/klipper_logs/moonraker-${i}.log"
      local service="${SYSTEMD}/moonraker-${i}.service"
      ### write multi instance service
      write_moonraker_service "${i}" "${cfg_dir}" "${cfg}" "${log}" "${service}"
      ok_msg "Moonraker instance #${i} created!"
      i=$((i+1))
    done && unset i
    ### enable mainsails remoteMode if mainsail is found
    if [ -d "${MAINSAIL_DIR}" ]; then
      status_msg "Mainsail installation found!"
      status_msg "Enabling Mainsail remoteMode ..."
      enable_mainsail_remotemode
      ok_msg "Mainsails remoteMode enabled!"
    fi
  else
    return 1
  fi
}

function write_moonraker_service(){
  local i=${1} cfg_dir=${2} cfg=${3} log=${4} service=${5}
  local service_template="${SRCDIR}/kiauh/resources/moonraker.service"

  ### replace all placeholders
  if [ ! -f "${service}" ]; then
    status_msg "Creating Moonraker Service ${i} ..."
      sudo cp "${service_template}" "${service}"

      [ -z "${i}" ] && sudo sed -i "s|instance %INST% ||" "${service}"
      [ -n "${i}" ] && sudo sed -i "s|%INST%|${i}|" "${service}"
      sudo sed -i "s|%USER%|${USER}|; s|%ENV%|${MOONRAKER_ENV}|; s|%DIR%|${MOONRAKER_DIR}|" "${service}"
      sudo sed -i "s|%CFG%|${cfg}|; s|%LOG%|${log}|" "${service}"
  fi
}

function print_mr_ip_list(){
  local ip instances="${1}" i=1 port=7125
  ip=$(hostname -I | cut -d" " -f1)
  while [ "${i}" -le "${instances}" ] ; do
    echo -e "   ${cyan}● Instance ${i}:${white} ${ip}:${port}"
    port=$((port+1))
    i=$((i+1))
  done && echo
}

### introduced due to
### https://github.com/Arksine/moonraker/issues/349
### https://github.com/Arksine/moonraker/pull/346
function moonraker_polkit(){
  local has_sup
  ### check for required SupplementaryGroups entry in service files
  ### write it to the service if it doesn't exist
  for service in $(moonraker_systemd); do
    has_sup="$(grep "SupplementaryGroups=moonraker-admin" "${service}")"
    if [ -z "${has_sup}" ]; then
      status_msg "Adding moonraker-admin supplementary group to ${service} ..."
      sudo sed -i "/^Type=simple$/a SupplementaryGroups=moonraker-admin" "${service}"
      ok_msg "Adding moonraker-admin supplementary group successfull!"
    fi
  done
  [ -z "${has_sup}" ] && echo "reloading services!!!" && sudo systemctl daemon-reload
  ### execute moonrakers policykit-rules script
  /bin/bash "${HOME}/moonraker/scripts/set-policykit-rules.sh"
}

#==================================================#
#================ REMOVE MOONRAKER ================#
#==================================================#

function remove_moonraker_sysvinit() {
  [ ! -e "${INITD}/moonraker" ] && return
  status_msg "Removing Moonraker SysVinit service ..."
  sudo systemctl stop moonraker
  sudo update-rc.d -f moonraker remove
  sudo rm -f "${INITD}/moonraker" "${ETCDEF}/moonraker"
  ok_msg "Moonraker SysVinit service removed!"
}

function remove_moonraker_systemd() {
  [ -z "$(moonraker_systemd)" ] && return
  status_msg "Removing Moonraker Systemd Services ..."
  local files
  for service in $(moonraker_systemd | cut -d"/" -f5)
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
  ok_msg "Moonraker Services removed!"
}

function remove_moonraker_logs() {
  local files
  files=$(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/moonraker(-[^0])?[0-9]*\.log(.*)?")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_moonraker_api_key() {
  ### remove legacy api key
  if [ -e "${HOME}/.klippy_api_key" ]; then
    status_msg "Removing legacy API Key ..."
    rm "${HOME}/.klippy_api_key"
    ok_msg "Done!"
  fi
  ### remove api key
  if [ -e "${HOME}/.moonraker_api_key" ]; then
    status_msg "Removing API Key ..."
    rm "${HOME}/.moonraker_api_key"
    ok_msg "Done!"
  fi
}

function remove_moonraker_dir() {
  [ ! -d "${MOONRAKER_DIR}" ] && return
  status_msg "Removing Moonraker directory ..."
  rm -rf "${MOONRAKER_DIR}"
  ok_msg "Directory removed!"
}

function remove_moonraker_env() {
  [ ! -d "${MOONRAKER_ENV}" ] && return
  status_msg "Removing moonraker-env directory ..."
  rm -rf "${MOONRAKER_ENV}"
  ok_msg "Directory removed!"
}

function remove_moonraker_polkit() {
  [ ! -d "${MOONRAKER_DIR}" ] && return
  status_msg "Removing all Moonraker PolicyKit rules ..."
  /bin/bash "${MOONRAKER_DIR}/scripts/set-policykit-rules.sh" --clear
  ok_msg "Done!"
}

#TODO this is technically not moonraker but rather webinterface related configs, so this should be refactored.
function remove_moonraker_nginx() {
  if [[ -e "${NGINX_CONFD}/upstreams.conf" || -e "${NGINX_CONFD}/common_vars.conf" ]]; then
    status_msg "Removing Moonraker NGINX configuration ..."
    sudo rm -f "${NGINX_CONFD}/upstreams.conf" "${NGINX_CONFD}/common_vars.conf"
    ok_msg "Moonraker NGINX configuration removed!"
  fi
}


function remove_moonraker(){
  remove_moonraker_sysvinit
  remove_moonraker_systemd
  remove_moonraker_logs
  remove_moonraker_api_key
  remove_moonraker_polkit
  remove_moonraker_dir
  remove_moonraker_env
  remove_moonraker_nginx

  local confirm="Moonraker was successfully removed!"
  print_confirm "${confirm}" && return
}

#==================================================#
#================ UPDATE MOONRAKER ================#
#==================================================#

function update_moonraker(){
  do_action_service "stop" "moonraker"
  if [ ! -d "${MOONRAKER_DIR}" ]; then
    cd "${HOME}" && git clone "${MOONRAKER_REPO}"
  else
    backup_before_update "moonraker"
    status_msg "Updating Moonraker ..."
    cd "${MOONRAKER_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_moonraker_packages
    ### install possible new python dependencies
    "${MOONRAKER_ENV}"/bin/pip install -r "${MOONRAKER_DIR}/scripts/moonraker-requirements.txt"
  fi
  ### required due to https://github.com/Arksine/moonraker/issues/349
  moonraker_polkit

  ok_msg "Update complete!"
  do_action_service "restart" "moonraker"
}

#==================================================#
#================ MOONRAKER STATUS ================#
#==================================================#

function get_moonraker_status(){
  local sf_count status
  sf_count="$(moonraker_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${MOONRAKER_DIR}" "${MOONRAKER_ENV}")
  [ "${sf_count}" -gt 0 ] && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [ -e "${data}" ] && filecount=$(("${filecount}" + 1))
  done

  if (( filecount == ${#data_arr[*]})); then
    status="Installed: ${sf_count}"
  elif ((filecount == 0)); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi
  echo "${status}"
}

function get_local_moonraker_commit(){
  local commit
  [ ! -d "${MOONRAKER_DIR}" ] || [ ! -d "${MOONRAKER_DIR}"/.git ] && return
  cd "${MOONRAKER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_moonraker_commit(){
  local commit
  [ ! -d "${MOONRAKER_DIR}" ] || [ ! -d "${MOONRAKER_DIR}"/.git ] && return
  cd "${MOONRAKER_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_moonraker_versions(){
  unset MOONRAKER_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_moonraker_commit)"
  remote_ver="$(get_remote_moonraker_commit)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to the update all array for the update all function in the updater
    MOONRAKER_UPDATE_AVAIL="true" && update_arr+=(update_moonraker)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    MOONRAKER_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}