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

#===================================================#
#================ INSTALL MOONRAKER ================#
#===================================================#

function moonraker_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker(-[0-9a-zA-Z]+)?.service" | sort)
  echo "${services}"
}

function moonraker_setup_dialog() {
  status_msg "Initializing Moonraker installation ..."

  ### return early if python version check fails
  if [[ $(python3_check) == "false" ]]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  ### return early if moonraker already exists
  local moonraker_services
  moonraker_services=$(moonraker_systemd)
  if [[ -n ${moonraker_services} ]]; then
    local error="At least one Moonraker service is already installed:"
    for s in ${moonraker_services}; do
      log_info "Found Moonraker service: ${s}"
      error="${error}\n ➔ ${s}"
    done
    print_error "${error}" && return
  fi

  ### return early if klipper is not installed
  local klipper_services
  klipper_services=$(klipper_systemd)
  if [[ -z ${klipper_services} ]]; then
    local error="Klipper not installed! Please install Klipper first!"
    log_error "Moonraker setup started without Klipper being installed. Aborting setup."
    print_error "${error}" && return
  fi

  local klipper_count user_input=() klipper_names=()
  klipper_count=$(echo "${klipper_services}" | wc -w )
  for service in ${klipper_services}; do
    klipper_names+=( "$(get_instance_name "${service}")" )
  done

  local moonraker_count
  if (( klipper_count == 1 )); then
    ok_msg "Klipper installation found!\n"
    moonraker_count=1
  elif (( klipper_count > 1 )); then
    top_border
    printf "|${green}%-55s${white}|\n" " ${klipper_count} Klipper instances found!"
    for name in "${klipper_names[@]}"; do
      printf "|${cyan}%-57s${white}|\n" " ● klipper-${name}"
    done
    blank_line
    echo -e "| The setup will apply the same names to Moonraker!     |"
    blank_line
    echo -e "| Please select the number of Moonraker instances to    |"
    echo -e "| install. Usually one Moonraker instance per Klipper   |"
    echo -e "| instance is required, but you may not install more    |"
    echo -e "| Moonraker instances than available Klipper instances. |"
    bottom_border

    ### ask for amount of instances
    local re="^[1-9][0-9]*$"
    while [[ ! ${moonraker_count} =~ ${re} || ${moonraker_count} -gt ${klipper_count} ]]; do
      read -p "${cyan}###### Number of Moonraker instances to set up:${white} " -i "${klipper_count}" -e moonraker_count
      ### break if input is valid
      [[ ${moonraker_count} =~ ${re} && ${moonraker_count} -le ${klipper_count} ]] && break
      ### conditional error messages
      [[ ! ${moonraker_count} =~ ${re} ]] && error_msg "Input not a number"
      (( moonraker_count > klipper_count )) && error_msg "Number of Moonraker instances larger than installed Klipper instances"
    done && select_msg "${moonraker_count}"
  else
    log_error "Internal error. klipper_count of '${klipper_count}' not equal or grather than one!"
    return 1
  fi

  user_input+=("${moonraker_count}")

  ### confirm instance amount
  local yn
  while true; do
    (( moonraker_count == 1 )) && local question="Install Moonraker?"
    (( moonraker_count > 1 )) && local question="Install ${moonraker_count} Moonraker instances?"
    read -p "${cyan}###### ${question} (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        abort_msg "Exiting Moonraker setup ...\n"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done

  ### write existing klipper names into user_input array to use them as names for moonraker
  if (( klipper_count > 1 )); then
    for name in "${klipper_names[@]}"; do
      user_input+=("${name}")
    done
  fi

  (( moonraker_count > 1 )) && status_msg "Installing ${moonraker_count} Moonraker instances ..."
  (( moonraker_count == 1 )) && status_msg "Installing Moonraker ..."
  moonraker_setup "${user_input[@]}"
}

function install_moonraker_dependencies() {
  local packages
  local install_script="${MOONRAKER_DIR}/scripts/install-moonraker.sh"

  ### read PKGLIST from official install-script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package info
  status_msg "Updating package lists..."
  if ! sudo apt-get update --allow-releaseinfo-change; then
    log_error "failure while updating package lists"
    error_msg "Updating package lists failed!"
    exit 1
  fi

  ### Install required packages
  status_msg "Installing required packages..."
  if ! sudo apt-get install --yes "${packages[@]}"; then
    log_error "failure while installing required moonraker packages"
    error_msg "Installing required packages failed!"
    exit 1
  fi
}

function create_moonraker_virtualenv() {
  status_msg "Installing python virtual environment..."

  ### always create a clean virtualenv
  [[ -d ${MOONRAKER_ENV} ]] && rm -rf "${MOONRAKER_ENV}"

  if virtualenv -p /usr/bin/python3 "${MOONRAKER_ENV}"; then
    "${MOONRAKER_ENV}"/bin/pip install -U pip
    "${MOONRAKER_ENV}"/bin/pip install -r "${MOONRAKER_DIR}/scripts/moonraker-requirements.txt"
  else
    log_error "failure while creating python3 moonraker-env"
    error_msg "Creation of Moonraker virtualenv failed!"
    exit 1
  fi
}

function moonraker_setup() {
  local instance_arr=("${@}")
  ### checking dependencies
  local dep=(git wget curl unzip dfu-util virtualenv)
  ### additional required dependencies on armbian
  dep+=(libjpeg-dev zlib1g-dev)
  dependency_check "${dep[@]}"

  ### step 1: clone moonraker
  clone_moonraker "${MOONRAKER_REPO}"

  ### step 2: install moonraker dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_moonraker_dependencies
  create_moonraker_virtualenv

  ### step 3: create moonraker.conf
  create_moonraker_conf "${instance_arr[@]}"

  ### step 4: create moonraker instances
  create_moonraker_service "${instance_arr[@]}"

  ### step 5: create polkit rules for moonraker
  moonraker_polkit || true

  ### step 6: enable and start all instances
  do_action_service "enable" "moonraker"
  do_action_service "start" "moonraker"

  ### confirm message
  local confirm=""
  (( instance_arr[0] == 1 )) && confirm="Moonraker has been set up!"
  (( instance_arr[0] > 1 )) && confirm="${instance_arr[0]} Moonraker instances have been set up!"
  print_confirm "${confirm}" && print_mr_ip_list "${instance_arr[0]}" && return
}

function clone_moonraker() {
  local repo=${1}

  status_msg "Cloning Moonraker from ${repo} ..."

  ### force remove existing moonraker dir and clone into fresh moonraker dir
  [[ -d ${MOONRAKER_DIR} ]] && rm -rf "${MOONRAKER_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${MOONRAKER_REPO}" "${MOONRAKER_DIR}"; then
    print_error "Cloning Moonraker from\n ${repo}\n failed!"
    exit 1
  fi
}

function create_moonraker_conf() {
  local input=("${@}")
  local moonraker_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local log="${KLIPPER_LOGS}"
  local lan
  lan="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"
  local port=7125 cfg_dir cfg db uds

  if (( moonraker_count == 1 )); then
    cfg_dir="${KLIPPER_CONFIG}"
    cfg="${cfg_dir}/moonraker.conf"
    db="${HOME}/.moonraker_database"
    uds="/tmp/klippy_uds"
    ### write single instance config
    write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${log}" "${db}" "${uds}" "${lan}"

  elif (( moonraker_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= moonraker_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      cfg="${cfg_dir}/moonraker.conf"
      uds="/tmp/klippy_uds-${names[${j}]}"
      db="${HOME}/.moonraker_database_${names[${j}]}"
      ### write multi instance config
      write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${log}" "${db}" "${uds}" "${lan}"
      port=$(( port + 1 ))
      j=$(( j + 1 ))
    done && unset j

  else
    return 1
  fi
}

function write_moonraker_conf() {
  local cfg_dir=${1} cfg=${2} port=${3} log=${4} db=${5} uds=${6} lan=${7}
  local conf_template="${KIAUH_SRCDIR}/resources/moonraker.conf"

  [[ ! -d ${cfg_dir} ]] && mkdir -p "${cfg_dir}"

  if [[ ! -f ${cfg} ]]; then
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

function create_moonraker_service() {
  local input=("${@}")
  local moonraker_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local cfg_dir cfg log service

  if (( moonraker_count == 1 )) && [[ ${#names[@]} -eq 0 ]]; then
    i=""
    cfg_dir="${KLIPPER_CONFIG}"
    cfg="${cfg_dir}/moonraker.conf"
    log="${KLIPPER_LOGS}/moonraker.log"
    service="${SYSTEMD}/moonraker.service"
    ### write single instance service
    write_moonraker_service "" "${cfg}" "${log}" "${service}"
    ok_msg "Moonraker instance created!"

  elif (( moonraker_count > 1 )) && [[ ${#names[@]} -gt 0 ]]; then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= moonraker_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      cfg="${cfg_dir}/moonraker.conf"
      log="${KLIPPER_LOGS}/moonraker-${names[${j}]}.log"
      service="${SYSTEMD}/moonraker-${names[${j}]}.service"
      ### write multi instance service
      write_moonraker_service "${names[${j}]}" "${cfg}" "${log}" "${service}"
      ok_msg "Moonraker instance 'moonraker-${names[${j}]}' created!"
      j=$(( j + 1 ))
    done && unset i

    ### enable mainsails remoteMode if mainsail is found
    if [[ -d ${MAINSAIL_DIR} ]]; then
      status_msg "Mainsail installation found! Enabling Mainsail remote mode ..."
      enable_mainsail_remotemode
      ok_msg "Mainsails remote mode enabled!"
    fi

  else
    return 1
  fi
}

function write_moonraker_service() {
  local i=${1} cfg=${2} log=${3} service=${4}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker.service"

  ### replace all placeholders
  if [[ ! -f ${service} ]]; then
    status_msg "Creating Moonraker Service ${i} ..."
    sudo cp "${service_template}" "${service}"

    [[ -z ${i} ]] && sudo sed -i "s| for instance moonraker-%INST%||" "${service}"
    [[ -n ${i} ]] && sudo sed -i "s|%INST%|${i}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%ENV%|${MOONRAKER_ENV}|; s|%DIR%|${MOONRAKER_DIR}|" "${service}"
    sudo sed -i "s|%CFG%|${cfg}|; s|%LOG%|${log}|" "${service}"
  fi
}

function print_mr_ip_list() {
  local ip count=${1} port=7125
  ip=$(hostname -I | cut -d" " -f1)

  for (( i=1; i <= count; i++ )); do
    echo -e "   ${cyan}● Instance ${i}:${white} ${ip}:${port}"
    port=$(( port + 1 ))
  done && echo
}

### introduced due to
### https://github.com/Arksine/moonraker/issues/349
### https://github.com/Arksine/moonraker/pull/346
function moonraker_polkit() {
  local has_sup

  ### check for required SupplementaryGroups entry in service files
  ### write it to the service if it doesn't exist
  for service in $(moonraker_systemd); do
    has_sup="$(grep "SupplementaryGroups=moonraker-admin" "${service}")"
    if [[ -z ${has_sup} ]]; then
      status_msg "Adding moonraker-admin supplementary group to ${service} ..."
      sudo sed -i "/^Type=simple$/a SupplementaryGroups=moonraker-admin" "${service}"
      ok_msg "Adding moonraker-admin supplementary group successfull!"
    fi
  done

  [[ -z ${has_sup} ]] && echo "reloading services!!!" && sudo systemctl daemon-reload

  ### execute moonrakers policykit-rules script
  "${HOME}"/moonraker/scripts/set-policykit-rules.sh
}

#==================================================#
#================ REMOVE MOONRAKER ================#
#==================================================#

function remove_moonraker_sysvinit() {
  [[ ! -e "${INITD}/moonraker" ]] && return

  status_msg "Removing Moonraker SysVinit service ..."
  sudo systemctl stop moonraker
  sudo update-rc.d -f moonraker remove
  sudo rm -f "${INITD}/moonraker" "${ETCDEF}/moonraker"
  ok_msg "Moonraker SysVinit service removed!"
}

function remove_moonraker_systemd() {
  [[ -z $(moonraker_systemd) ]] && return

  status_msg "Removing Moonraker Systemd Services ..."

  for service in $(moonraker_systemd | cut -d"/" -f5); do
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
  local files regex="moonraker(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${KLIPPER_LOGS}" -maxdepth 1 -regextype posix-extended -regex "${KLIPPER_LOGS}/${regex}" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_moonraker_api_key() {
  ### remove legacy api key
  if [[ -e "${HOME}/.klippy_api_key" ]]; then
    status_msg "Removing legacy API Key ..."
    rm "${HOME}/.klippy_api_key"
    ok_msg "Done!"
  fi

  ### remove api key
  if [[ -e "${HOME}/.moonraker_api_key" ]]; then
    status_msg "Removing API Key ..."
    rm "${HOME}/.moonraker_api_key"
    ok_msg "Done!"
  fi
}

function remove_moonraker_dir() {
  [[ ! -d ${MOONRAKER_DIR} ]] && return

  status_msg "Removing Moonraker directory ..."
  rm -rf "${MOONRAKER_DIR}"
  ok_msg "Directory removed!"
}

function remove_moonraker_env() {
  [[ ! -d ${MOONRAKER_ENV} ]] && return

  status_msg "Removing moonraker-env directory ..."
  rm -rf "${MOONRAKER_ENV}"
  ok_msg "Directory removed!"
}

function remove_moonraker_polkit() {
  [[ ! -d ${MOONRAKER_DIR} ]] && return

  status_msg "Removing all Moonraker PolicyKit rules ..."
  "${MOONRAKER_DIR}"/scripts/set-policykit-rules.sh --clear
  ok_msg "Done!"
}

function remove_moonraker() {
  remove_moonraker_sysvinit
  remove_moonraker_systemd
  remove_moonraker_logs
  remove_moonraker_api_key
  remove_moonraker_polkit
  remove_moonraker_dir
  remove_moonraker_env

  print_confirm "Moonraker was successfully removed!"
  return
}

#==================================================#
#================ UPDATE MOONRAKER ================#
#==================================================#

function update_moonraker() {
  do_action_service "stop" "moonraker"

  if [[ ! -d ${MOONRAKER_DIR} ]]; then
    clone_moonraker "${MOONRAKER_REPO}"
  else
    backup_before_update "moonraker"
    status_msg "Updating Moonraker ..."
    cd "${MOONRAKER_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_moonraker_dependencies
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

function get_moonraker_status() {
  local sf_count status
  sf_count="$(moonraker_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${MOONRAKER_DIR}" "${MOONRAKER_ENV}")
  (( sf_count > 0 )) && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && filecount=$(( filecount + 1 ))
  done

  if (( filecount == ${#data_arr[*]} )); then
    status="Installed: ${sf_count}"
  elif (( filecount == 0 )); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi

  echo "${status}"
}

function get_local_moonraker_commit() {
  [[ ! -d ${MOONRAKER_DIR} || ! -d "${MOONRAKER_DIR}/.git" ]] && return

  local commit
  cd "${MOONRAKER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_moonraker_commit() {
  [[ ! -d ${MOONRAKER_DIR} || ! -d "${MOONRAKER_DIR}/.git" ]] && return

  local commit
  cd "${MOONRAKER_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_moonraker_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_moonraker_commit)"
  remote_ver="$(get_remote_moonraker_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "moonraker"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}