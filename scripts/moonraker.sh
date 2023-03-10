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

#===================================================#
#================ INSTALL MOONRAKER ================#
#===================================================#

###
# this function detects all installed moonraker
# systemd instances and returns their absolute path
function moonraker_systemd() {
  local services
  local blacklist
  local ignore
  local match

  ###
  # any moonraker client that uses "moonraker" in its own name must be blacklisted using
  # this variable, otherwise they will be falsely recognized as moonraker instances
  blacklist="obico"

  ignore="${SYSTEMD}/moonraker-(${blacklist}).service"
  match="${SYSTEMD}/moonraker(-[0-9a-zA-Z]+)?.service"

  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype awk ! -regex "${ignore}" -regex "${match}" | sort)
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
  configure_moonraker_service "${instance_arr[@]}"

  ### step 5: create polkit rules for moonraker
  install_moonraker_polkit || true

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
  local port lan printer_data cfg_dir cfg uds

  port=7125
  lan="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  if (( moonraker_count == 1 )); then
    printer_data="${HOME}/printer_data"
    cfg_dir="${printer_data}/config"
    cfg="${cfg_dir}/moonraker.conf"
    uds="${printer_data}/comms/klippy.sock"

    ### write single instance config
    write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${uds}" "${lan}"

  elif (( moonraker_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= moonraker_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        printer_data="${HOME}/printer_${names[${j}]}_data"
      else
        printer_data="${HOME}/${names[${j}]}_data"
      fi

      cfg_dir="${printer_data}/config"
      cfg="${cfg_dir}/moonraker.conf"
      uds="${printer_data}/comms/klippy.sock"

      ### write multi instance config
      write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${uds}" "${lan}"
      port=$(( port + 1 ))
      j=$(( j + 1 ))
    done && unset j

  else
    return 1
  fi
}

function write_moonraker_conf() {
  local cfg_dir=${1} cfg=${2} port=${3} uds=${4} lan=${5}
  local conf_template="${KIAUH_SRCDIR}/resources/moonraker.conf"

  [[ ! -d ${cfg_dir} ]] && mkdir -p "${cfg_dir}"

  if [[ ! -f ${cfg} ]]; then
    status_msg "Creating moonraker.conf in ${cfg_dir} ..."
    cp "${conf_template}" "${cfg}"
    sed -i "s|%USER%|${USER}|g; s|%PORT%|${port}|; s|%UDS%|${uds}|" "${cfg}"
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

function configure_moonraker_service() {
  local input=("${@}")
  local moonraker_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local printer_data cfg_dir service env_file

  if (( moonraker_count == 1 )) && [[ ${#names[@]} -eq 0 ]]; then
    i=""
    printer_data="${HOME}/printer_data"
    cfg_dir="${printer_data}/config"
    service="${SYSTEMD}/moonraker.service"
    env_file="${printer_data}/systemd/moonraker.env"

    ### create required folder structure
    create_required_folders "${printer_data}"

    ### write single instance service
    write_moonraker_service "" "${printer_data}" "${service}" "${env_file}"
    ok_msg "Moonraker instance created!"

  elif (( moonraker_count > 1 )) && [[ ${#names[@]} -gt 0 ]]; then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= moonraker_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        printer_data="${HOME}/printer_${names[${j}]}_data"
      else
        printer_data="${HOME}/${names[${j}]}_data"
      fi

      cfg_dir="${printer_data}/config"
      service="${SYSTEMD}/moonraker-${names[${j}]}.service"
      env_file="${printer_data}/systemd/moonraker.env"

      ### create required folder structure
      create_required_folders "${printer_data}"

      ### write multi instance service
      write_moonraker_service "${names[${j}]}" "${printer_data}" "${service}" "${env_file}"
      ok_msg "Moonraker instance 'moonraker-${names[${j}]}' created!"
      j=$(( j + 1 ))
    done && unset i

    ### enable mainsails remoteMode if mainsail is found
    if [[ -d ${MAINSAIL_DIR} ]]; then
      enable_mainsail_remotemode
    fi

  else
    return 1
  fi
}

function write_moonraker_service() {
  local i=${1} printer_data=${2} service=${3} env_file=${4}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker.service"
  local env_template="${KIAUH_SRCDIR}/resources/moonraker.env"

  ### replace all placeholders
  if [[ ! -f ${service} ]]; then
    status_msg "Creating Moonraker Service ${i} ..."
    sudo cp "${service_template}" "${service}"
    sudo cp "${env_template}" "${env_file}"

    [[ -z ${i} ]] && sudo sed -i "s| %INST%||" "${service}"
    [[ -n ${i} ]] && sudo sed -i "s|%INST%|${i}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|g; s|%ENV%|${MOONRAKER_ENV}|; s|%ENV_FILE%|${env_file}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%PRINTER_DATA%|${printer_data}|" "${env_file}"
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
function install_moonraker_polkit() {
  local POLKIT_LEGACY_FILE="/etc/polkit-1/localauthority/50-local.d/10-moonraker.pkla"
  local POLKIT_FILE="/etc/polkit-1/rules.d/moonraker.rules"
  local POLKIT_USR_FILE="/usr/share/polkit-1/rules.d/moonraker.rules"
  local legacy_file_exists
  local file_exists
  local usr_file_exists

  local has_sup
  local require_daemon_reload="false"

  legacy_file_exists=$(sudo find "${POLKIT_LEGACY_FILE}" 2> /dev/null)
  file_exists=$(sudo find "${POLKIT_FILE}" 2> /dev/null)
  usr_file_exists=$(sudo find "${POLKIT_USR_FILE}" 2> /dev/null)

  ### check for required SupplementaryGroups entry in service files
  ### write it to the service if it doesn't exist
  for service in $(moonraker_systemd); do
    has_sup="$(grep "SupplementaryGroups=moonraker-admin" "${service}")"
    if [[ -z ${has_sup} ]]; then
      status_msg "Adding moonraker-admin supplementary group to ${service} ..."
      sudo sed -i "/^Type=simple$/a SupplementaryGroups=moonraker-admin" "${service}"
      require_daemon_reload="true"
      ok_msg "Adding moonraker-admin supplementary group successfull!"
    fi
  done

  if [[ ${require_daemon_reload} == "true" ]]; then
    status_msg "Reloading unit files ..."
    sudo systemctl daemon-reload
    ok_msg "Unit files reloaded!"
  fi

  ### execute moonrakers policykit-rules script only if rule files do not already exist
  if [[ -z ${legacy_file_exists} && ( -z ${file_exists} || -z ${usr_file_exists} ) ]]; then
    status_msg "Installing Moonraker policykit rules ..."
    "${HOME}"/moonraker/scripts/set-policykit-rules.sh
    ok_msg "Moonraker policykit rules installed!"
  fi

  return
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

function remove_moonraker_env_file() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/systemd\/moonraker\.env"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_moonraker_logs() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/moonraker\.log.*"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_legacy_moonraker_logs() {
  local files regex="moonraker(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/${regex}" 2> /dev/null | sort)

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
  remove_moonraker_env_file
  remove_moonraker_logs
  remove_legacy_moonraker_logs
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
  install_moonraker_polkit || true

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
