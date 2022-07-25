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
#============== INSTALL MOONRAKER-OBICO ============#
#===================================================#

function moonraker_obico_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-obico.*.service")
  echo "${services}"
}

function moonraker_obico_setup_dialog() {
  status_msg "Initializing Moonraker-obico installation ..."

  ### return early if python version check fails
  if [[ $(python3_check) == "false" ]]; then
    local error="Versioncheck failed! Python 3.7 or newer required!\n"
    error="${error} Please upgrade Python."
    print_error "${error}" && return
  fi

  ### return early if moonraker_obico already exists
  local moonraker_obico_services
  moonraker_obico_services=$(moonraker_obico_systemd)
  if [[ -n ${moonraker_obico_services} ]]; then
    local error="At least one Moonraker-obico service is already installed:"
    for s in ${moonraker_obico_services}; do
      log_info "Found Moonraker-obico service: ${s}"
      error="${error}\n ➔ ${s}"
    done
    print_error "${error}" && return
  fi

  ### return early if moonraker is not installed
  local moonraker_services
  moonraker_services=$(moonraker_systemd)
  if [[ -z ${moonraker_services} ]]; then
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error "Moonraker-obico setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  fi

  local moonraker_count user_input=() moonraker_names=()
  moonraker_count=$(echo "${moonraker_services}" | wc -w )
  for service in ${moonraker_services}; do
    moonraker_names+=( "$(get_instance_name "${service}")" )
  done

  local moonraker_obico_count
  if (( moonraker_count == 1 )); then
    ok_msg "Moonraker installation found!\n"
    moonraker_obico_count=1
  elif (( moonraker_count > 1 )); then
    top_border
    printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
    for name in "${moonraker_names[@]}"; do
      printf "|${cyan}%-57s${white}|\n" " ●moonraker-${name}"
    done
    blank_line
    echo -e "| The setup will apply the same names to                |"
    echo -e "| Moonraker-obico!                                      |"
    blank_line
    echo -e "| Please select the number of Moonraker-obico instances |"
    echo -e "| to install. Usually one Moonraker-obico instance per  |"
    echo -e "| Moonraker instance is required, but you may not       |"
    echo -e "| install more Moonraker-obico instances than available |"
    echo -e "| Moonraker instances.                                  |"
    bottom_border

    ### ask for amount of instances
    local re="^[1-9][0-9]*$"
    while [[ ! ${moonraker_obico_count} =~ ${re} || ${moonraker_obico_count} -gt ${moonraker_count} ]]; do
      read -p "${cyan}###### Number of Moonraker-obico instances to set up:${white} " -i "${moonraker_count}" -e moonraker_obico_count
      ### break if input is valid
      [[ ${moonraker_obico_count} =~ ${re} && ${moonraker_obico_count} -le ${moonraker_count} ]] && break
      ### conditional error messages
      [[ ! ${moonraker_obico_count} =~ ${re} ]] && error_msg "Input not a number"
      (( moonraker_obico_count > moonraker_count )) && error_msg "Number of Moonraker-obico instances larger than installed Moonraker instances"
    done && select_msg "${moonraker_obico_count}"
  else
    log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grather than one!"
    return 1
  fi

  user_input+=("${moonraker_obico_count}")

  ### confirm instance amount
  local yn
  while true; do
    (( moonraker_obico_count == 1 )) && local question="Install Moonraker-obico?"
    (( moonraker_obico_count > 1 )) && local question="Install ${moonraker_obico_count} Moonraker-obico instances?"
    read -p "${cyan}###### ${question} (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        abort_msg "Exiting Moonraker-obico setup ...\n"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done

  ### write existing moonraker names into user_input array to use them as names for moonraker-obico
  if (( moonraker_count > 1 )); then
    for name in "${moonraker_names[@]}"; do
      user_input+=("${name}")
    done
  fi

  (( moonraker_obico_count > 1 )) && status_msg "Installing ${moonraker_count} Moonraker-obico instances ..."
  (( moonraker_obico_count == 1 )) && status_msg "Installing Moonraker-obico ..."
  moonraker_obico_setup "${user_input[@]}"

}

function moonraker_obico_setup() {

  ### checking dependencies
  local dep=(git dfu-util virtualenv python3 python3-pip python3-venv ffmpeg)
  dependency_check "${dep[@]}"

  ### step 1: clone moonraker-obico
  clone_moonraker_obico "${MOONRAKER_OBICO_REPO}"

  ### step 2: call moonrake-obico/install.sh with the correct params
  local input=("${@}")
  local moonraker_obico_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local log="${KLIPPER_LOGS}"
  local port=7125 cfg_dir moonraker_cfg

  if (( moonraker_obico_count == 1 )); then
    cfg_dir="${KLIPPER_CONFIG}"
    moonraker_cfg="${cfg_dir}/moonraker.conf"

    # Invoke moonrake-obico/install.sh
    moonraker_obico_install -c "${moonraker_cfg}" -p ${port} -H 127.0.0.1 -l "${KLIPPER_LOGS}"

  elif (( moonraker_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= moonraker_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      moonraker_cfg="${cfg_dir}/moonraker.conf"

      # Invoke moonrake-obico/install.sh
      moonraker_obico_install -c "${moonraker_cfg}" -p ${port} -H 127.0.0.1 -l "${KLIPPER_LOGS}"

      port=$(( port + 1 ))
      j=$(( j + 1 ))
    done && unset j

  else
    return 1
  fi
}

function clone_moonraker_obico() {
  local repo=${1}

  status_msg "Cloning Moonraker-obico from ${repo} ..."

  ### force remove existing moonraker-obico dir and clone into fresh moonraker-obico dir
  [[ -d ${MOONRAKER_OBICO_DIR} ]] && rm -rf "${MOONRAKER_OBICO_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${MOONRAKER_OBICO_REPO}" "${MOONRAKER_OBICO_DIR}"; then
    print_error "Cloning Moonraker-obico from\n ${repo}\n failed!"
    exit 1
  fi
}

function moonraker_obico_install() {
  "${MOONRAKER_OBICO_DIR}/install.sh" $@
}

#===================================================#
#============= REMOVE MOONRAKER-OBICO ==============#
#===================================================#

function remove_moonraker_obico_systemd() {
  [[ -z $(moonraker_obico_systemd) ]] && return
  status_msg "Removing Moonraker-obico Systemd Services ..."

  for service in $(moonraker_obico_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done

  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
  ok_msg "Moonraker-obico Services removed!"
}

function remove_moonraker_obico_logs() {
  local files regex="moonraker-obico(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${KLIPPER_LOGS}" -maxdepth 1 -regextype posix-extended -regex "${KLIPPER_LOGS}/${regex}" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_moonraker_obico_dir() {
  [[ ! -d ${MOONRAKER_OBICO_DIR} ]] && return

  status_msg "Removing Moonraker-obico directory ..."
  rm -rf "${MOONRAKER_OBICO_DIR}"
  ok_msg "Directory removed!"
}

function remove_moonraker_obico_env() {
  [[ ! -d "${HOME}/moonraker-env" ]] && return

  status_msg "Removing moonraker-env directory ..."
  rm -rf "${HOME}/moonraker-env"
  ok_msg "Directory removed!"
}

function remove_moonraker_obico() {
  remove_moonraker_obico_systemd
  remove_moonraker_obico_logs
  remove_moonraker_obico_dir
  remove_moonraker_obico_env

  print_confirm "Moonraker-obico was successfully removed!"
  return
}

#===================================================#
#============= UPDATE MOONRAKER-OBICO ==============#
#===================================================#

function update_moonraker() {
  for service in $(moonraker_obico_systemd | cut -d"/" -f5); do
    do_action_service "stop" "${service}"
  done

  if [[ ! -d ${MOONRAKER_OBICO_DIR} ]]; then
    clone_moonraker_obico "${MOONRAKER_OBICO_REPO}"
  else
    status_msg "Updating Moonraker-obico ..."
    cd "${MOONRAKER_OBICO_DIR}" && git pull
    "${MOONRAKER_OBICO_DIR}/install.sh" -u
  fi

  ok_msg "Update complete!"
  for service in $(moonraker_obico_systemd | cut -d"/" -f5); do
    do_action_service "restart" "${service}"
  done
}

#===================================================#
#============= MOONRAKER-OBICO STATUS ==============#
#===================================================#

function get_obico_status() {
  local sf_count status
  sf_count="$(klipperscreen_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${KLIPPERSCREEN_DIR}" "${KLIPPERSCREEN_ENV}")
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

function get_local_moonraker_obico_commit() {
  [[ ! -d ${MOONRAKER_OBICO_DIR} || ! -d "${MOONRAKER_OBICO_DIR}/.git" ]] && return

  local commit
  cd "${MOONRAKER_OBICO_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_moonraker_obico_commit() {
  [[ ! -d ${MOONRAKER_OBICO_DIR} || ! -d "${MOONRAKER_OBICO_DIR}/.git" ]] && return

  local commit
  cd "${MOONRAKER_OBICO_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_moonraker_obico_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_moonraker_obico_commit)"
  remote_ver="$(get_remote_moonraker_obico_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "moonraker_obico"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}
