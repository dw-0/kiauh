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

#=================================================#
#=============== INSTALL OCTOPRINT ===============#
#=================================================#

function octoprint_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/octoprint(-[0-9a-zA-Z]+)?.service" | sort)
  echo "${services}"
}

function octoprint_setup_dialog() {
  status_msg "Initializing OctoPrint installation ..."

  local klipper_services
  klipper_services=$(klipper_systemd)
  if [[ -z ${klipper_services} ]]; then
    local error="Klipper not installed! Please install Klipper first!"
    log_error "OctoPrint setup started without Klipper being installed. Aborting setup."
    print_error "${error}" && return
  fi

  local klipper_count user_input=() klipper_names=()
  klipper_count=$(echo "${klipper_services}" | wc -w )
  for service in ${klipper_services}; do
    klipper_names+=( "$(get_instance_name "${service}")" )
  done

  local octoprint_count
  if (( klipper_count == 1 )); then
    ok_msg "Klipper installation found!\n"
    octoprint_count=1

  elif (( klipper_count > 1 )); then
    top_border
    printf "|${green}%-55s${white}|\n" " ${klipper_count} Klipper instances found!"
    for name in "${klipper_names[@]}"; do
      printf "|${cyan}%-57s${white}|\n" " ● ${name}"
    done
    blank_line
    echo -e "| The setup will apply the same names to OctoPrint!     |"
    blank_line
    echo -e "| Please select the number of OctoPrint instances to    |"
    echo -e "| install. Usually one OctoPrint instance per Klipper   |"
    echo -e "| instance is required, but you may not install more    |"
    echo -e "| OctoPrint instances than available Klipper instances. |"
    bottom_border

    local re="^[1-9][0-9]*$"
    while [[ ! ${octoprint_count} =~ ${re} || ${octoprint_count} -gt ${klipper_count} ]]; do
      read -p "${cyan}###### Number of OctoPrint instances to set up:${white} " -i "${klipper_count}" -e octoprint_count
      ### break if input is valid
      [[ ${octoprint_count} =~ ${re} ]] && break
      ### conditional error messages
      [[ ! ${octoprint_count} =~ ${re} ]] && error_msg "Input not a number"
      (( octoprint_count > klipper_count )) && error_msg "Number of OctoPrint instances larger than existing Klipper instances"
    done && select_msg "${octoprint_count}"

  else
    log_error "Internal error. klipper_count of '${klipper_count}' not equal or grather than one!"
    return 1
  fi

  user_input+=("${octoprint_count}")

  ### confirm instance amount
  local yn
  while true; do
    (( octoprint_count == 1 )) && local question="Install OctoPrint?"
    (( octoprint_count > 1 )) && local question="Install ${octoprint_count} OctoPrint instances?"
    read -p "${cyan}###### ${question} (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        abort_msg "Exiting OctoPrint setup ...\n"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done

  ### write existing klipper names into user_input array to use them as names for octoprint
  if (( klipper_count > 1 )); then
    for name in "${klipper_names[@]}"; do
      user_input+=("${name}")
    done
  fi

  (( octoprint_count > 1 )) && status_msg "Installing ${octoprint_count} OctoPrint instances ..."
  (( octoprint_count == 1 )) && status_msg "Installing OctoPrint ..."
  octoprint_setup "${user_input[@]}"
}

function octoprint_setup() {
  local instance_arr=("${@}")
  ### check and install all dependencies
  local dep=(
    git
    wget
    python3-pip
    python3-dev
    libyaml-dev
    build-essential
    python3-setuptools
    python3-virtualenv
  )
  dependency_check "${dep[@]}"

  ### step 1: check for tty and dialout usergroups and add reboot permissions
  check_usergroups
  add_reboot_permission

  ### step 2: install octoprint
  install_octoprint "${instance_arr[@]}"

  ### step 3: set up service
  create_octoprint_service "${instance_arr[@]}"

  ### step 4: enable and start all instances
  do_action_service "enable" "octoprint"
  do_action_service "start" "octoprint"

  ### confirm message
  local confirm=""
  (( instance_arr[0] == 1 )) && confirm="OctoPrint has been set up!"
  (( instance_arr[0] > 1 )) && confirm="${instance_arr[0]} OctoPrint instances have been set up!"
  print_confirm "${confirm}" && print_op_ip_list "${instance_arr[0]}" && return
}

function install_octoprint() {

  function install_octoprint_python_env() {
    local tmp="${1}"
    ### create and activate the virtualenv
    status_msg "Installing python virtual environment..."

    if [[ ! -d ${tmp} ]]; then
      mkdir -p "${tmp}"
    else
      error_msg "Cannot create temporary directory in ${HOME}!"
      error_msg "Folder 'TMP_OCTO_ENV' exists and may not be empty!"
      error_msg "Please remove/rename that folder and start again."
      return 1
    fi

    cd "${tmp}"

    if virtualenv --python=python3 venv; then
      ### activate virtualenv
      source venv/bin/activate
      pip install pip --upgrade
      pip install --no-cache-dir octoprint
      ### leave virtualenv
      deactivate
    else
      log_error "failure while creating python3 OctoPrint env"
      error_msg "Creation of OctoPrint virtualenv failed!"
      exit 1
    fi

    cd "${HOME}"
  }

  local input=("${@}")
  local octoprint_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local j=0 octo_env
  local tmp="${HOME}/TMP_OCTO_ENV"

  ### handle single instance installs
  if (( octoprint_count == 1 )); then
    if install_octoprint_python_env "${tmp}"; then
      status_msg "Installing OctoPrint ..."
      octo_env="${HOME}/OctoPrint"

      ### rename the temporary directory to the correct name
      [[ -d ${octo_env} ]] && rm -rf "${octo_env}"
      mv "${tmp}" "${octo_env}"

      ### replace the temporary directory name with the actual one in ${octo_env}/venv/bin/python/octoprint
      sed -i "s|${tmp}|${octo_env}|" "${octo_env}/venv/bin/octoprint"
    else
      error_msg "OctoPrint installation failed!"
      return 1
    fi
  fi

  ### handle multi instance installs
  if (( octoprint_count > 1 )); then
    if install_octoprint_python_env "${tmp}"; then
      for (( i=1; i <= octoprint_count; i++ )); do
        status_msg "Installing OctoPrint instance ${i}(${names[${j}]}) ..."
        octo_env="${HOME}/OctoPrint_${names[${j}]}"

        ### rename the temporary directory to the correct name
        [[ -d ${octo_env} ]] && rm -rf "${octo_env}"
        cp -r "${tmp}" "${octo_env}"

        ### replace the temporary directory name with the actual one in ${octo_env}/venv/bin/python/octoprint
        sed -i "s|${tmp}|${octo_env}|" "${octo_env}/venv/bin/octoprint"
        j=$(( j + 1 ))
      done && rm -rf "${tmp}"
    else
      error_msg "OctoPrint installation failed!"
      return 1
    fi
  fi
}

function create_octoprint_service() {
  local input=("${@}")
  local octoprint_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local j=0 port=5000
  local printer_data octo_env service basedir printer config_yaml restart_cmd

  for (( i=1; i <= octoprint_count; i++ )); do
    if (( octoprint_count == 1 )); then
      printer_data="${HOME}/printer_data"
      octo_env="${HOME}/OctoPrint"
      service="${SYSTEMD}/octoprint.service"
      basedir="${HOME}/.octoprint"
      printer="${printer_data}/comms/klippy.serial"
      config_yaml="${basedir}/config.yaml"
      restart_cmd="sudo service octoprint restart"
    elif (( octoprint_count > 1 )); then

      local re="^[1-9][0-9]*$"
      if [[ ${names[j]} =~ ${re} ]]; then
        printer_data="${HOME}/printer_${names[${j}]}_data"
      else
        printer_data="${HOME}/${names[${j}]}_data"
      fi

      octo_env="${HOME}/OctoPrint_${names[${j}]}"
      service="${SYSTEMD}/octoprint-${names[${j}]}.service"
      basedir="${HOME}/.octoprint_${names[${j}]}"
      printer="${printer_data}/comms/klippy.serial"
      config_yaml="${basedir}/config.yaml"
      restart_cmd="sudo service octoprint-${names[${j}]} restart"
    fi

    (( octoprint_count == 1 )) && status_msg "Creating OctoPrint Service ..."
    (( octoprint_count > 1 )) && status_msg "Creating OctoPrint Service ${i}(${names[${j}]}) ..."

    sudo /bin/sh -c "cat > ${service}" << OCTOPRINT
[Unit]
Description=Starts OctoPrint on startup
After=network-online.target
Wants=network-online.target

[Service]
Environment="LC_ALL=C.UTF-8"
Environment="LANG=C.UTF-8"
Type=simple
User=${USER}
ExecStart=${octo_env}/venv/bin/octoprint --basedir ${basedir} --config ${config_yaml} --port=${port} serve

[Install]
WantedBy=multi-user.target
OCTOPRINT

    port=$(( port + 1 ))
    j=$(( j + 1 ))
    ok_msg "Ok!"

    ### create config.yaml
    if [[ ! -f ${basedir}/config.yaml ]]; then
      [[ ! -d ${basedir} ]] && mkdir "${basedir}"

      (( octoprint_count == 1 )) && status_msg "Creating config.yaml ..."
      (( octoprint_count > 1 )) && status_msg "Creating config.yaml for instance ${i}(${names[${j}]}) ..."

      /bin/sh -c "cat > ${basedir}/config.yaml" << CONFIGYAML
serial:
    additionalPorts:
    - ${printer}
    disconnectOnErrors: false
    port: ${printer}
server:
    commands:
        serverRestartCommand: ${restart_cmd}
        systemRestartCommand: sudo shutdown -r now
        systemShutdownCommand: sudo shutdown -h now
CONFIGYAML
      ok_msg "Ok!"
    fi
  done
}

function add_reboot_permission() {
  #create a backup if file already exists
  if [[ -f /etc/sudoers.d/octoprint-shutdown ]]; then
    sudo mv /etc/sudoers.d/octoprint-shutdown /etc/sudoers.d/octoprint-shutdown.old
  fi

  #create new permission file
  status_msg "Add reboot permission to user '${USER}' ..."
  cd "${HOME}" && echo "${USER} ALL=NOPASSWD: /sbin/shutdown" > octoprint-shutdown
  sudo chown 0 octoprint-shutdown
  sudo mv octoprint-shutdown /etc/sudoers.d/octoprint-shutdown
  ok_msg "Permission set!"
}

function print_op_ip_list() {
  local ip octoprint_count="${1}" port=5000
  ip=$(hostname -I | cut -d" " -f1)

  for (( i=1; i <= octoprint_count; i++ )); do
    echo -e "   ${cyan}● Instance ${i}:${white} ${ip}:${port}"
    port=$(( port + 1 ))
  done && echo
}

#=================================================#
#=============== REMOVE OCTOPRINT ================#
#=================================================#

function remove_octoprint_service() {
  [[ -z $(octoprint_systemd) ]] && return

  ###remove all octoprint services
  status_msg "Removing OctoPrint Systemd Services ..."

  for service in $(octoprint_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done

  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
}

function remove_octoprint_sudoers() {
  [[ ! -f /etc/sudoers.d/octoprint-shutdown ]] && return

  ### remove sudoers file
  sudo rm -f /etc/sudoers.d/octoprint-shutdown
}

function remove_octoprint_env() {
  local files
  files=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/OctoPrint(_[0-9a-zA-Z]+)?" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoprint_dir() {
  local files
  files=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/.octoprint(_[0-9a-zA-Z]+)?" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoprint() {
  remove_octoprint_service
  remove_octoprint_sudoers
  remove_octoprint_env
  remove_octoprint_dir

  local confirm="OctoPrint was successfully removed!"

  print_confirm "${confirm}" && return
}

#=================================================#
#=============== OCTOPRINT STATUS ================#
#=================================================#

function get_octoprint_status() {
  local sf_count env_count dir_count status
  sf_count="$(octoprint_systemd | wc -w)"
  env_count=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/OctoPrint(_[0-9a-zA-Z]+)?" | wc -w)
  dir_count=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/.octoprint(_[0-9a-zA-Z]+)?" | wc -w)

  if (( sf_count == 0 )) && (( env_count == 0 )) && (( dir_count == 0 )); then
    status="Not installed!"
  elif (( sf_count == env_count )) && (( sf_count == dir_count )); then
    status="Installed: ${sf_count}"
  else
    status="Incomplete!"
  fi

  echo "${status}"
}
