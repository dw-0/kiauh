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
  ### return early if python version check fails
  if [[ $(python3_check) == "false" ]]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  local klipper_services=$(find_klipper_systemd)
  local klipper_count=$(echo "${klipper_services}" | wc -w )
  for service in ${klipper_services}; do
    klipper_names+=( "$(get_instance_name "${service}")" )
  done

  local moonraker_services=$(moonraker_systemd)
  local moonraker_count=$(echo "${moonraker_services}" | wc -w )
  for service in ${moonraker_services}; do
    moonraker_names+=( "$(get_instance_name "${service}")" )
  done

  ### return early if klipper is not installed
  if [[ -z ${klipper_services} ]]; then
    local error="Klipper not installed! Please install Klipper first!"
    log_error "Moonraker setup started without Klipper being installed. Aborting setup."
    print_error "${error}" && return
  fi

  top_border
  echo -e "|     ${red}~~~~~~~~~ [ Moonraker installation ] ~~~~~~~~${white}     |"
  hr

  printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker services found!"
  local moonraker_folders=()
  for name in ${moonraker_services}; do
    local moonraker_folder=$(get_data_folder $(basename ${name}) moonraker)
    printf "|${cyan}%-57s${white}|\n" " ● $(basename ${name}) - $(get_moonraker_address $(basename ${name}))"
    moonraker_folders+=( "${moonraker_folder}" )
  done
  blank_line
  printf "|${green}%-55s${white}|\n" " ${klipper_count} Klipper services found!"
  local klipper_available=()
  for name in ${klipper_services}; do
    local klipper_folder=$(get_data_folder $(basename ${name}) klipper)
    printf "|${cyan}%-57s${white}|\n" " ● $(basename ${name}) - ${klipper_folder}"
    if [[ ! " ${moonraker_folders[*]} " =~ " ${klipper_folder} " ]]; then
      klipper_available+=( "$(basename ${name})" )
    fi
  done
  local klipper_available_count=${#klipper_available[@]}
  hr

  printf "|${green}%-55s${white}|\n" " ${klipper_available_count} Moonraker services can be installed:"
  local service_name
  if (( klipper_available_count == 1 )); then
    service_name=$(basename "${klipper_available[@]}")
    printf "| 0) %-51s|\n" "${service_name}"
  else
    printf "| 0) %-51s|\n" "Install all"
    local i=1
    for name in "${klipper_available[@]}"; do
      printf "| ${i}) %-51s|\n" "${name}"
      (( i=i+1 ))
    done
  fi
  back_footer

  local option
  while true; do
    read -p "${cyan}Install moonraker for:${white} " option
    if [[ ${option} == "B" || ${option} == "b" ]]; then
      return
    elif [[ $((option)) != $option ]]; then
      error_msg "Invalid command!"
    elif (( option >= 0 && option < ${#klipper_available[@]} )); then
      break
    else
      error_msg "Invalid command!"
    fi
  done

  if (( option == 0 )); then
    user_input=( ${klipper_available[@]} )
  else
    user_input=( "${klipper_available[(( option-1 ))]}" )
  fi

  status_msg "Installing Moonraker ..."
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
  if [[ "${moonraker_clone_result}" == "0" ]]; then
    create_moonraker_virtualenv
  fi
  unset moonraker_clone_result

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
  (( ${#instance_arr[@]} == 1 )) && confirm="Moonraker has been set up!"
  (( ${#instance_arr[@]} > 1 )) && confirm="${#instance_arr[@]} Moonraker instances have been set up!"
  print_confirm "${confirm}"
  print_moonraker_addresses
}

function clone_moonraker() {
  local repo=${1}

  status_msg "Cloning Moonraker from ${repo} ..."

  if [[ -d ${MOONRAKER_DIR} ]]
  then
    status_msg "Moonraker already cloned, pulling recent changes ..."
    git -C ${MOONRAKER_DIR} stash
    git -C ${MOONRAKER_DIR} pull --ff-only
    moonraker_clone_result="1"
    return
  fi

  ### force remove existing moonraker dir and clone into fresh moonraker dir
  [[ -d ${MOONRAKER_DIR} ]] && rm -rf "${MOONRAKER_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${MOONRAKER_REPO}" "${MOONRAKER_DIR}"; then
    print_error "Cloning Moonraker from\n ${repo}\n failed!"
    exit 1
  fi
  moonraker_clone_result="0"
}

function create_moonraker_conf() {
  local names=("${@}")
  local moonraker_count=${#names[@]}
  local lan printer_data cfg_dir cfg uds
  local port=$(get_moonraker_next_port)

  lan="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  for service in "${names[@]}"; do
    ### overwrite config folder if name is only a number
    printer_data=$(get_data_folder "${service}" "klipper")

    cfg_dir="${printer_data}/config"
    cfg="${cfg_dir}/moonraker.conf"
    uds="${printer_data}/comms/klippy.sock"

    ### write multi instance config
    write_moonraker_conf "${cfg_dir}" "${cfg}" "${port}" "${uds}" "${lan}"
    (( port=port+1 ))
  done && unset j
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
  local names=("${@}")
  local moonraker_count=${#names[@]}
  local printer_data cfg_dir service env_file service_name

  for service in "${names[@]}"; do
    printer_data=$(get_data_folder "${service}" "klipper")

    cfg_dir="${printer_data}/config"
    service_name="${service/"klipper"/"moonraker"}" 
    service="${SYSTEMD}/${service_name}"
    env_file="${printer_data}/systemd/moonraker.env"

    ### create required folder structure
    create_required_folders "${printer_data}"

    ### write multi instance service
    write_moonraker_service "${service_name}" "${printer_data}" "${service}" "${env_file}"
    ok_msg "Moonraker instance '${service_name}' created!"
  done && unset i

  ### enable mainsails remoteMode if mainsail is found
  if [[ -d ${MAINSAIL_DIR} ]]; then
    enable_mainsail_remotemode
  fi
}

function write_moonraker_service() {
  local i=${1} printer_data=${2} service=${3} env_file=${4}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker.service"
  local env_template="${KIAUH_SRCDIR}/resources/moonraker.env"
  local instance_name=$(get_instance_name "${i}")

  ### replace all placeholders
  if [[ ! -f ${service} ]]; then
    status_msg "Creating Moonraker Service ${i} ..."
    sudo cp "${service_template}" "${service}"
    sudo cp "${env_template}" "${env_file}"

    sudo sed -i "s|%INST%|${instance_name}|" "${service}"
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

function get_moonraker_next_port() {
  local port=7125
  local moonraker_services=$(moonraker_systemd) moonraker_ports=()
  for service in ${moonraker_services}
  do
    service_name=$(basename ${service})
    moonraker_ports+=( "$(get_moonraker_port ${service_name})" )
  done
  while true; do
    if [[ ! " ${moonraker_ports[*]} " =~ " ${port} " ]]; then
      break
    fi
    (( port=port+1 ))
  done
  echo "${port}"
}

function get_moonraker_port() {
  local service=${1}
  local printer_data=$(get_data_folder ${service} moonraker)
  local port=$(grep "^port:" "${printer_data}/config/moonraker.conf" | cut -f 2 -d " ")
  echo "${port}"
}

function get_moonraker_address() {
  local ip=$(hostname -I | cut -d" " -f1)
  local port=$(get_moonraker_port ${1})
  echo "${ip}:${port}"
}

function print_moonraker_addresses() {
  local service_name moonraker_services=$(moonraker_systemd)
  for service in ${moonraker_services}
  do
    service_name=$(basename ${service})
    echo "   ${cyan}● ${service_name}:${white} $(get_moonraker_address ${service_name})"
  done
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
  status_msg "Removing Moonraker Systemd Services ..."

  for service in "${@}"; do
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
  local printer_data file
  for service in "${@}"; do
    printer_data=$(get_data_folder ${service} moonraker)
    file="${printer_data}/systemd/moonraker.env"
    status_msg "Removing ${file} ..."
    rm -f "${file}"
    ok_msg "${file} removed!"
  done
}

function remove_moonraker_logs() {
  local printer_data file
  for service in "${@}"; do
    printer_data=$(get_data_folder ${service} moonraker)
    file="${printer_data}/systemd/moonraker.lo"*
    status_msg "Removing ${file} ..."
    rm -f "${file}"
    ok_msg "${file} removed!"
  done
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

  local moonraker_services=$(moonraker_systemd)
  if [[ -z ${moonraker_services} ]]; then
    print_error "Moonraker not installed, nothing to do!"
    return
  fi

  local moonraker_services=$(moonraker_systemd)
  if [[ -z ${moonraker_services} ]]; then
    print_error "Moonraker not installed, nothing to do!"
    return
  fi

  top_border
  echo -e "|     ${red}~~~~~~~ [ Moonraker instance remover ] ~~~~~~${white}     |"
  hr

  local user_input=() moonraker_names=()
  local moonraker_services_count="$(moonraker_systemd | wc -w)"
  if (( moonraker_services_count == 1 )); then
    service_name=$(basename ${moonraker_services})
    moonraker_names+=( "${service_name}" )
    printf "| 0) %-51s|\n" "${service_name}"
  else
    printf "| 0) %-51s|\n" "Remove all"
    local i=1 service_name
    for name in ${moonraker_services}; do
      service_name=$(basename ${name})
      moonraker_names+=( "${service_name}" )
      printf "| ${i}) %-51s|\n" "${service_name}"
      (( i=i+1 ))
    done
  fi
  back_footer

  local option
  while true; do
    read -p "${cyan}Remove Moonraker instance:${white} " option
    if [[ ${option} == "B" || ${option} == "b" ]]; then
      return
    elif [[ $((option)) != $option ]]; then
      error_msg "Invalid command!"
    elif (( option >= 0 && option < ${#moonraker_names[@]} )); then
      break
    else
      error_msg "Invalid command!"
    fi
  done

  if (( option == 0 )); then
    user_input=( ${moonraker_names[@]} )
  else
    user_input=( "${moonraker_names[(( option-1 ))]}" )
  fi

  remove_moonraker_systemd "${user_input[@]}"
  remove_moonraker_env_file "${user_input[@]}"
  remove_moonraker_logs "${user_input[@]}"

  remove_legacy_moonraker_logs

  if (( ${moonraker_services_count} == 1 )) || [[ "${moonraker_count}" == "0" ]]; then
    remove_moonraker_api_key
    remove_moonraker_polkit
    remove_moonraker_dir
    remove_moonraker_env
  fi

  print_confirm "Moonraker was successfully removed!"
  return
}

#==================================================#
#================ UPDATE MOONRAKER ================#
#==================================================#

function update_moonraker() {
  do_action_service "stop" "moonraker"

  if [[ ! -d ${MOONRAKER_DIR} ]]; then
    error_msg "Nothing to update, Moonraker directory doesn't exists! Please install Moonraker first."
    return
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
