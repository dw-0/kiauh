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
#=============== INSTALL OCTOPRINT ===============#
#=================================================#

function octoprint_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/octoprint(-[^0])?[0-9]*.service")
  echo "${services}"
}

function octoprint_setup_dialog(){
  local klipper_count
  klipper_count=$(klipper_systemd | wc -w)

  status_msg "Initializing OctoPrint installation ..."
  top_border
  if [ -f "${INITD}/klipper" ] || [ -f "${SYSTEMD}/klipper.service" ]; then
    printf "|${green}%-55s${white}|\n" " 1 Klipper instance was found!"
  elif [ "${klipper_count}" -gt 1 ]; then
    printf "|${green}%-55s${white}|\n" " ${klipper_count} Klipper instances were found!"
  else
    echo -e "| ${yellow}INFO: No existing Klipper installation found!${default}         |"
  fi
  echo -e "| Usually you need one OctoPrint instance per Klipper   |"
  echo -e "| instance. Though you can install as many as you wish. |"
  bottom_border

  local count
  while [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; do
    read -p "${cyan}###### Number of OctoPrint instances to set up:${default} " count
    if [[ ! (${count} =~ ^[1-9]+((0)+)?$) ]]; then
      error_msg "Invalid Input!\n"
    else
      echo
      while true; do
        read -p "${cyan}###### Install ${count} instance(s)? (Y/n):${default} " yn
        case "${yn}" in
          Y|y|Yes|yes|"")
            select_msg "Yes"
            status_msg "Installing ${count} OctoPrint instance(s) ... \n"
            octoprint_setup "${count}"
            break;;
          N|n|No|no)
            select_msg "No"
            error_msg "Exiting OctoPrint setup ...\n"
            break;;
          *)
            error_msg "Invalid Input!\n";;
        esac
      done
    fi
  done
}

function octoprint_setup(){
  local instances="${1}"
  ### check and install all dependencies
  dep=(
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

  ### check for tty and dialout usergroups and add reboot permissions
  check_usergroups
  add_reboot_permission

  ### install octoprint
  install_octoprint "${instances}"

  ### set up service
  create_octoprint_service "${instances}"

  ### step 6: enable and start all instances
  do_action_service "enable" "octoprint"
  do_action_service "start" "octoprint"

  ### confirm message
  [ "${instances}" -eq 1 ] && confirm_msg="OctoPrint has been set up!"
  [ "${instances}" -gt 1 ] && confirm_msg="${instances} OctoPrint instances have been set up!"
  print_confirm "${confirm_msg}"
  print_op_ip_list "${instances}"
}

function install_octoprint(){
  local i=1 instances=${1} octo_env
  while (( i <= instances )); do
    (( instances == 1 )) && octo_env="${HOME}/OctoPrint"
    (( instances > 1 )) && octo_env="${HOME}/OctoPrint_${i}"
    ### create and activate the virtualenv
    status_msg "Installing python virtual environment..."
    [ ! -d "${octo_env}" ] && mkdir -p "${octo_env}"
    cd "${octo_env}" && virtualenv --python=python3 venv
    ### activate virtualenv
    source venv/bin/activate
    (( instances == 1 )) && status_msg "Installing OctoPrint ..."
    (( instances > 1 )) && status_msg "Installing OctoPrint instance ${i} ..."
    pip install pip --upgrade
    pip install --no-cache-dir octoprint
    ok_msg "Ok!"
    ### leave virtualenv
    deactivate
    i=$((i+1))
  done
}

function create_octoprint_service(){
  local i=1 instances=${1} port=5000
  local octo_env service basedir tmp_printer config_yaml restart_cmd

  while (( i <= instances )); do
    if (( instances == 1 )); then
      octo_env="${HOME}/OctoPrint"
      service="${SYSTEMD}/octoprint.service"
      basedir="${HOME}/.octoprint"
      tmp_printer="/tmp/printer"
      config_yaml="${basedir}/config.yaml"
      restart_cmd="sudo service octoprint restart"
    elif (( instances > 1 )); then
      octo_env="${HOME}/OctoPrint_${i}"
      service="${SYSTEMD}/octoprint-${i}.service"
      basedir="${HOME}/.octoprint_${i}"
      tmp_printer="/tmp/printer-${i}"
      config_yaml="${basedir}/config.yaml"
      restart_cmd="sudo service octoprint-${i} restart"
    fi
    (( instances == 1 )) && status_msg "Creating OctoPrint service ..."
    (( instances > 1 )) && status_msg "Creating OctoPrint service ${i} ..."
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
  ok_msg "Ok!"

  ### create config.yaml
  if [ ! -f "${basedir}/config.yaml" ]; then
    [ ! -d "${basedir}" ] && mkdir "${basedir}"
    status_msg "Creating config.yaml ..."
    /bin/sh -c "cat > ${basedir}/config.yaml" << CONFIGYAML
serial:
    additionalPorts:
    - ${tmp_printer}
    disconnectOnErrors: false
    port: ${tmp_printer}
server:
    commands:
        serverRestartCommand: ${restart_cmd}
        systemRestartCommand: sudo shutdown -r now
        systemShutdownCommand: sudo shutdown -h now
CONFIGYAML
    ok_msg "Ok!"
  fi

  port=$((port+1))
  i=$((i+1))
  done
}

function add_reboot_permission(){
  #create a backup if file already exists
  if [ -f /etc/sudoers.d/octoprint-shutdown ]; then
    sudo mv /etc/sudoers.d/octoprint-shutdown /etc/sudoers.d/octoprint-shutdown.old
  fi
  #create new permission file
  status_msg "Add reboot permission to user '${USER}' ..."
  cd "${HOME}" && echo "${USER} ALL=NOPASSWD: /sbin/shutdown" > octoprint-shutdown
  sudo chown 0 octoprint-shutdown
  sudo mv octoprint-shutdown /etc/sudoers.d/octoprint-shutdown
  ok_msg "Permission set!"
}

function print_op_ip_list(){
  local ip instances="${1}" i=1 port=5000
  ip=$(hostname -I | cut -d" " -f1)
  while [ "${i}" -le "${instances}" ] ; do
    echo -e "   ${cyan}● Instance ${i}:${white} ${ip}:${port}"
    port=$((port+1))
    i=$((i+1))
  done && echo
}

#=================================================#
#=============== REMOVE OCTOPRINT ================#
#=================================================#

function remove_octoprint_service(){
  ###remove all octoprint services
  [ -z "$(octoprint_systemd)" ] && return
  status_msg "Removing OctoPrint Systemd Services ..."
  for service in $(octoprint_systemd | cut -d"/" -f5)
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
}

function remove_octoprint_sudoers(){
  [ ! -f /etc/sudoers.d/octoprint-shutdown ] && return
  ### remove sudoers file
  sudo rm -f /etc/sudoers.d/octoprint-shutdown
}

function remove_octoprint_env(){
  local files
  files=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/OctoPrint(_[^0])?[0-9]*")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoprint_dir(){
  local files
  files=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/.octoprint(_[^0])?[0-9]*")
  if [ -n "${files}" ]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -rf "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_octoprint(){
  remove_octoprint_service
  remove_octoprint_sudoers
  remove_octoprint_env
  remove_octoprint_dir

  ### remove octoprint_port from ~/.kiauh.ini
  sed -i "/^octoprint_port=/d" "${INI_FILE}"

  local confirm="OctoPrint was successfully removed!"
  print_confirm "${confirm}" && return
}

#=================================================#
#=============== OCTOPRINT STATUS ================#
#=================================================#

function octoprint_status(){
  local sf_count env_count dir_count status
  sf_count="$(octoprint_systemd | wc -w)"
  env_count=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/OctoPrint(_[^0])?[0-9]*" | wc -w)
  dir_count=$(find "${HOME}" -maxdepth 1 -regextype posix-extended -regex "${HOME}/.octoprint(_[^0])?[0-9]*" | wc -w)

  if (( sf_count == env_count)) && (( sf_count == dir_count)); then
    status="$(printf "${green}Installed: %-5s${white}" "${sf_count}")"
  elif (( sf_count == 0 )) && (( env_count == 0 )) && (( dir_count == 0 )); then
    status="${red}Not installed!${white}  "
  else
    status="${yellow}Incomplete!${white}     "
  fi
  echo "${status}"
}