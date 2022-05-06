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

#=================================================#
#================ INSTALL KLIPPER ================#
#=================================================#

### check for existing klipper service installations
function klipper_initd() {
  local services
  services=$(find "${INITD}" -maxdepth 1 -regextype posix-extended -regex "${INITD}/klipper(-[^0])?[0-9]*" | sort)
  echo "${services}"
}

function klipper_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/klipper(-[0-9a-zA-Z]+)?.service" | sort)
  echo "${services}"
}

function klipper_exists() {
  local services
  [ -n "$(klipper_initd)" ] && services+="$(klipper_initd) "
  [ -n "$(klipper_systemd)" ] && services+="$(klipper_systemd)"
  echo "${services}"
}

function klipper_setup_dialog(){
  local python_version="${1}" user_input=()
  user_input+=("${python_version}")

  status_msg "Initializing Klipper installation ..."

  ### return early if klipper already exists
  local klipper_services
  klipper_services=$(klipper_exists)
  if [ -n "${klipper_services}" ]; then
    local error="At least one Klipper service is already installed:"
    for s in ${klipper_services}; do
      log_info "Found Klipper service: ${s}"
      error="${error}\n ➔ ${s}"
    done
    print_error "${error}" && return
  fi

  ### ask for amount of instances to create
  top_border
  echo -e "| Please select the number of Klipper instances to set  |"
  echo -e "| up. The number of Klipper instances will determine    |"
  echo -e "| the amount of printers you can run from this host.    |"
  blank_line
  echo -e "| ${yellow}WARNING:${white}                                              |"
  echo -e "| ${yellow}Setting up too many instances may crash your system.${white}  |"
  bottom_border

  ### ask for amount of instances
  local klipper_count re="^[1-9][0-9]*$"
  while ! [[ ${klipper_count} =~ ${re} ]]; do
    read -p "${cyan}###### Number of Klipper instances to set up:${white} " -i "1" -e klipper_count
    if ! [[ ${klipper_count} =~ ${re} ]]; then
      error_msg "Invalid input!"
    else
      select_msg "${klipper_count}"
      user_input+=("${klipper_count}")
      break
    fi
  done

  ### confirm instance amount
  while true; do
    read -p "${cyan}###### Install ${klipper_count} instance(s)? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        abort_msg "Exiting Klipper setup ...\n"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done

  ### ask for custom names
  if (( klipper_count > 1 )); then
    local custom_names="false"
    top_border
    echo -e "| You can give each instance a custom name or skip.     |"
    echo -e "| If skipped, KIAUH will automatically assign an index  |"
    echo -e "| to each instance in ascending order, starting at '1'. |"
    blank_line
    echo -e "| Info:                                                 |"
    echo -e "| Only alphanumeric characters will be allowed.         |"
    bottom_border
    while true; do
      read -p "${cyan}###### Use custom names? (y/N):${white} " yn
      case "${yn}" in
        Y|y|Yes|yes)
          select_msg "Yes"
          custom_names="true"
          break;;
        N|n|No|no|"")
          select_msg "No"
          break;;
        *)
          error_msg "Invalid Input!";;
      esac
    done

    ### get user input for custom names
    if [[ "${custom_names}" == "true" ]]; then
      local i=1 name="" re="^[0-9a-zA-Z]+$"
      while ! [[ ${name} =~ ${re} && ${i} -gt ${klipper_count} ]]; do
        read -p "${cyan}###### Name for instance #${i}:${white} " name
        if [[ ${name} =~ ${re} ]]; then
          select_msg "Name: ${name}"
          user_input+=("${name}")
          i=$(( i + 1 ))
        else
          error_msg "Invalid Input!"
        fi
      done
    else
      ### if no custom names are used, add the respective amount of indices to the user_input array
      for ((i=1; i <= klipper_count; i++)); do
        user_input+=("${i}")
      done
    fi
  fi


  ((klipper_count > 1)) && status_msg "Installing ${klipper_count} Klipper instances ..."
  ((klipper_count == 1)) && status_msg "Installing single Klipper instance ..."

  klipper_setup "${user_input[@]}"
}

function install_klipper_packages(){
  local packages python_version="${1}"
  local install_script="${HOME}/klipper/scripts/install-octopi.sh"

  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages=$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')
  ### replace python-dev with python3-dev if python3 was selected
  [ "${python_version}" == "python3" ] && packages="${packages//python-dev/python3-dev}"
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
  local python_version="${1}" py2_ver py3_ver
  if [ "${python_version}" == "python2" ]; then
    py2_ver=$(python2 -V)
    status_msg "Installing ${py2_ver} virtual environment..."
    [ -d "${KLIPPY_ENV}" ] && rm -rf "${KLIPPY_ENV}"
    virtualenv -p python2 "${KLIPPY_ENV}"
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}"/scripts/klippy-requirements.txt
  fi
  if [ "${python_version}" == "python3" ]; then
    py3_ver=$(python3 -V)
    status_msg "Installing ${py3_ver} virtual environment..."
    virtualenv -p python3 "${KLIPPY_ENV}"
    ### upgrade pip
    "${KLIPPY_ENV}"/bin/pip install -U pip
    "${KLIPPY_ENV}"/bin/pip install -r "${KLIPPER_DIR}"/scripts/klippy-requirements.txt
  fi
  return
}

function klipper_setup(){
  read_kiauh_ini "${FUNCNAME[0]}"
  ### index 0: python version, index 1: instance count, index 2-n: instance names (optional)
  local user_input=("${@}")
  local python_version="${user_input[0]}" && unset "user_input[0]"
  local instance_arr=("${user_input[@]}") && unset "user_input[@]"
  local custom_repo="${custom_klipper_repo}"
  local custom_branch="${custom_klipper_repo_branch}"
  ### checking dependencies
  local dep=(git)
  dependency_check "${dep[@]}"

  ### step 1: clone klipper
  ### force remove existing klipper dir and clone into fresh klipper dir
  [ -d "${KLIPPER_DIR}" ] && rm -rf "${KLIPPER_DIR}"
  if [ -z "${custom_repo}" ]; then
    status_msg "Downloading Klipper ..."
    cd "${HOME}" && git clone "${KLIPPER_REPO}"
  else
    local repo_name
    repo_name=$(echo "${custom_repo}" | sed "s/https:\/\/github\.com\///" | sed "s/\.git$//" )
    status_msg "Downloading Klipper from ${repo_name} ..."
    cd "${HOME}" && git clone "https://github.com/${custom_repo}" "klipper"
    cd "${KLIPPER_DIR}" && git checkout "${custom_branch}"
    cd "${HOME}"
  fi

  ### step 2: install klipper dependencies and create python virtualenv
  install_klipper_packages "${python_version}"
  create_klipper_virtualenv "${python_version}"

  ### step 3: create gcode_files and logs folder
  [ ! -d "${HOME}/gcode_files" ] && mkdir -p "${HOME}/gcode_files"
  [ ! -d "${KLIPPER_LOGS}" ] && mkdir -p "${KLIPPER_LOGS}"

  ### step 4: create klipper instances
  create_klipper_service "${instance_arr[@]}"

  ### step 5: enable and start all instances
  do_action_service "enable" "klipper"
  do_action_service "start" "klipper"

  ### step 6: check for dialout group membership
  check_usergroups

  ### confirm message
  local confirm=""
  (( instance_arr[0] == 1)) && confirm="Klipper has been set up!"
  (( instance_arr[0] > 1)) && confirm="${instance_arr[0]} Klipper instances have been set up!"
  print_confirm "${confirm}" && return
}

function write_klipper_service(){
  local i=${1} cfg=${2} log=${3} printer=${4} uds=${5} service=${6}
  local service_template="${SRCDIR}/kiauh/resources/klipper.service"
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

function write_example_printer_cfg(){
  local cfg_dir=${1} cfg=${2}
  local cfg_template="${SRCDIR}/kiauh/resources/printer.cfg"
  ### create a config directory if it doesn't exist
  [ ! -d "${cfg_dir}" ] && mkdir -p "${cfg_dir}"
  ### create a minimal config if there is no printer.cfg
  [ ! -f "${cfg}" ] && cp "${cfg_template}" "${cfg}"
}

function create_klipper_service(){
  local input=("${@}")
  local klipper_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local cfg_dir cfg log printer uds service

  if (( klipper_count == 1 )); then
    cfg_dir="${KLIPPER_CONFIG}"
    cfg="${cfg_dir}/printer.cfg"
    log="${KLIPPER_LOGS}/klippy.log"
    printer="/tmp/printer"
    uds="/tmp/klippy_uds"
    service="${SYSTEMD}/klipper.service"
    ### write single instance service
    write_klipper_service "" "${cfg}" "${log}" "${printer}" "${uds}" "${service}"
    write_example_printer_cfg "${cfg_dir}" "${cfg}"
    ok_msg "Single Klipper instance created!"

  elif (( klipper_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for ((i=1; i <= klipper_count; i++)); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      cfg="${cfg_dir}/printer.cfg"
      log="${KLIPPER_LOGS}/klippy-${names[${j}]}.log"
      printer="/tmp/printer-${names[${j}]}"
      uds="/tmp/klippy_uds-${names[${j}]}"
      service="${SYSTEMD}/klipper-${names[${j}]}.service"
      ### write multi instance service
      write_klipper_service "${i}(${names[${j}]})" "${cfg}" "${log}" "${printer}" "${uds}" "${service}"
      write_example_printer_cfg "${cfg_dir}" "${cfg}"
      ok_msg "Klipper instance #${i}(${names[${j}]}) created!"
      j=$((j+1))
    done && unset j

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
  files=$(find "${KLIPPER_LOGS}" -maxdepth 1 -regextype posix-extended -regex "${KLIPPER_LOGS}/klippy(-[0-9a-zA-Z]+)?\.log(.*)?" | sort)
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
  files=$(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/klippy_uds(-[0-9a-zA-Z]+)?" | sort)
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
  files=$(find /tmp -maxdepth 1 -regextype posix-extended -regex "/tmp/printer(-[0-9a-zA-Z]+)?" | sort)
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
    backup_before_update "klipper"
    status_msg "Updating Klipper ..."
    cd "${KLIPPER_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages
    ### install possible new python dependencies
    /bin/bash "${KLIPPY_ENV}/bin/pip" install -r "${KLIPPER_DIR}/scripts/klippy-requirements.txt"
  fi
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

  if (( filecount == ${#data_arr[*]})); then
    status="Installed: ${sf_count}"
  elif ((filecount == 0)); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi
  echo "${status}"
}

function get_local_klipper_commit(){
  local commit
  [ ! -d "${KLIPPER_DIR}" ] || [ ! -d "${KLIPPER_DIR}"/.git ] && return
  cd "${KLIPPER_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_klipper_commit(){
  local commit
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

#================================================#
#=================== HELPERS ====================#
#================================================#

function get_klipper_cfg_dir() {
  local cfg_dir
  read_kiauh_ini "${FUNCNAME[0]}"
  if [ -z "${custom_klipper_cfg_loc}" ]; then
    cfg_dir="${HOME}/klipper_config"
  else
    cfg_dir="${custom_klipper_cfg_loc}"
  fi
  echo "${cfg_dir}"
}