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
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-obico(-[0-9a-zA-Z]+)?.service")
  echo "${services}"
}

function cfg_dir() {
  local name=${1}
  if [[ -z ${name} || ${name} == "moonraker" || ${name} == "moonraker-obico" ]]; then
    echo "${KLIPPER_CONFIG}"
  else
    local re="^[1-9][0-9]*$"
    ### overwrite config folder if name is only a number
    if [[ ${name} =~ ${re} ]]; then
      echo "${KLIPPER_CONFIG}/printer_${name}"
    else
      echo "${KLIPPER_CONFIG}/${name}"
    fi
  fi
}

function is_moonraker_obico_linked() {
  local name=${1}
  moonraker_obico_cfg="$(cfg_dir ${name})/moonraker-obico.cfg"
  grep -s -E "^[^#]" "${moonraker_obico_cfg}" | grep -q 'auth_token'
  return $?
}

function get_moonraker_names() {
  local moonraker_services
  moonraker_services=$(moonraker_systemd)
  if [[ -z ${moonraker_services} ]]; then
    echo '' && return
  fi

  for service in ${moonraker_services}; do
    get_instance_name "${service}" moonraker
  done
}

function obico_server_url_prompt() {
  top_border
  printf "|${green}%-55s${white}|\n" " Obico Server URL"
  blank_line
  echo -e "| You can use a self-hosted Obico Server or the Obico   |"
  echo -e "| Cloud. For more information, please visit:            |"
  echo -e "| https://obico.io.                                     |"
  blank_line
  echo -e "| For the Obico Cloud, leave it as the default:         |"
  printf "|${cyan}%-55s${white}|\n" " https://app.obico.io"
  blank_line
  echo -e "| For self-hosted server, specify:                      |"
  printf "|${cyan}%-55s${white}|\n" " http://server_ip:port"
  echo -e "| For instance, \`http://192.168.0.5:3334\`.              |"
  bottom_border
}

function moonraker_obico_setup_dialog() {
  status_msg "Initializing Moonraker-obico installation ..."

  ### return early if moonraker is not installed
  local moonraker_count moonraker_names
  moonraker_names=($(get_moonraker_names))
  moonraker_count=${#moonraker_names[@]}
  if (( moonraker_count == 0 )); then
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error "Moonraker-obico setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  fi

  local moonraker_obico_services moonraker_obico_names=()
  moonraker_obico_services=$(moonraker_obico_systemd)
  existing_moonraker_obico_count=$(echo "${moonraker_obico_services}" | wc -w )
  for service in ${moonraker_obico_services}; do
    moonraker_obico_names+=( "$(get_instance_name "${service}" moonraker-obico)" )
  done

  local allowed_moonraker_obico_count=$(( moonraker_count - existing_moonraker_obico_count ))
  if (( allowed_moonraker_obico_count > 0 )); then

    ### Step 1: Ask for the number of moonraker-obico instances to install
    if (( moonraker_count == 1 )); then
      ok_msg "Moonraker installation found!\n"
      new_moonraker_obico_count=1
    elif (( moonraker_count > 1 )); then
      top_border
      printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
      for name in "${moonraker_names[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ●moonraker-${name}"
      done
      blank_line
      if (( existing_moonraker_obico_count > 0 )); then
        printf "|${green}%-55s${white}|\n" " ${existing_moonraker_obico_count} Moonraker-obico instances already installed!"
        for name in "${moonraker_obico_names[@]}"; do
          printf "|${cyan}%-57s${white}|\n" " ●moonraker-obico-${name}"
        done
      fi
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
      local new_moonraker_obico_count re="^[1-9][0-9]*$"
      while [[ ! ${new_moonraker_obico_count} =~ ${re} || ${new_moonraker_obico_count} -gt ${allowed_moonraker_obico_count} ]]; do
        read -p "${cyan}###### Number of new Moonraker-obico instances to set up:${white} " -i "${allowed_moonraker_obico_count}" -e new_moonraker_obico_count
        ### break if input is valid
        [[ ${new_moonraker_obico_count} =~ ${re} && ${new_moonraker_obico_count} -le ${allowed_moonraker_obico_count} ]] && break
        ### conditional error messages
        [[ ! ${new_moonraker_obico_count} =~ ${re} ]] && error_msg "Input not a number"
        (( new_moonraker_obico_count > allowed_moonraker_obico_count )) && error_msg "Number of Moonraker-obico instances larger than installed Moonraker instances"
      done && select_msg "${new_moonraker_obico_count}"
    else
      log_error "Internal error. new_moonraker_obico_count of '${new_moonraker_obico_count}' not equal or grather than one!"
      return 1
    fi

    ### Step 2: Confirm instance amount
    local yn
    while true; do
      (( new_moonraker_obico_count == 1 )) && local question="Install Moonraker-obico?"
      (( new_moonraker_obico_count > 1 )) && local question="Install ${new_moonraker_obico_count} Moonraker-obico instances?"
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
  fi

  if (( new_moonraker_obico_count > 0 )); then

    ### Step 3: Ask for the Obico server URL
    obico_server_url_prompt
    local obico_server_url
    while true; do
      read -p "${cyan}###### Obico Server URL:${white} " -i "https://app.obico.io" -e obico_server_url
      if echo "${obico_server_url}" | grep -qE "^(http|https)://[a-zA-Z0-9./?=_%:-]*"; then
        break
      else
        error_msg "Invalid server URL!"
      fi
    done

    (( new_moonraker_obico_count > 1 )) && status_msg "Installing ${new_moonraker_obico_count} Moonraker-obico instances ..."
    (( new_moonraker_obico_count == 1 )) && status_msg "Installing Moonraker-obico ..."

    ### Step 4: Install dependencies
    local dep=(git dfu-util virtualenv python3 python3-pip python3-venv ffmpeg)
    dependency_check "${dep[@]}"

    ### Step 5: Clone the moonraker-obico repo
    clone_or_update_moonraker_obico "${MOONRAKER_OBICO_REPO}"

    ### step 6: call moonrake-obico/install.sh with the correct params
    local log="${KLIPPER_LOGS}"
    local port=7125 moonraker_cfg

    if (( moonraker_count == 1 )); then
      moonraker_cfg="$(cfg_dir '')/moonraker.conf"
      "${MOONRAKER_OBICO_DIR}/install.sh" -C "${moonraker_cfg}" -p ${port} -H 127.0.0.1 -l "${KLIPPER_LOGS}" -s -L -S "${obico_server_url}"
    elif (( moonraker_count > 1 )); then
      local j=${existing_moonraker_obico_count}

      for (( i=1; i <= new_moonraker_obico_count; i++ )); do
        local name=${moonraker_names[${j}]}
        moonraker_cfg="$(cfg_dir ${name})/moonraker.conf"

        "${MOONRAKER_OBICO_DIR}/install.sh" -n "${name}" -C "${moonraker_cfg}" -p $((port+j)) -H 127.0.0.1 -l "${KLIPPER_LOGS}" -s -L -S "${obico_server_url}"
        j=$(( j + 1 ))
      done && unset j
    fi
  fi

  ### Step 7: Link to the Obico server if necessary
  local not_linked_instances=()
  # Refetch systemd service again since additional services may have been newly installed
  for service in $(moonraker_obico_systemd); do
      local instance_name="$(get_instance_name "${service}" moonraker-obico)"
      if ! is_moonraker_obico_linked "${instance_name}"; then
          not_linked_instances+=( "${instance_name}" )
      fi
  done
  if (( ${#not_linked_instances[@]} > 0 )); then
    top_border
    if (( moonraker_count == 1 )); then
      printf "|${green}%-55s${white}|\n" " Moonraker-obico not linked to the server!"
    else
      printf "|${green}%-55s${white}|\n" " ${#not_linked_instances[@]} Moonraker-obico instances not linked to the server!"
      for name in "${not_linked_instances[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ●moonraker-obico-${name}"
      done
    fi
    blank_line
    echo -e "| To link to your Obico Server account, you need to     |"
    echo -e "| obtain the 6-digit verification code in the Obico     |"
    echo -e "| mobile or web app. For more information, visit:       |"
    echo -e "| https://www.obico.io/docs/user-guides/klipper-setup/  |"
    blank_line
    echo -e "| If you don't want to link the printer now, you can    |"
    echo -e "| restart the linking process later by:                 |"
    echo -e "| 1. \`cd ~/kiauh && ./kiauh.sh\` to launch KIAUH.        |"
    echo -e "| 2. Select ${green}[Install]${white}                                   |"
    echo -e "| 3. Select ${green}[Link to Obico Server]${white}                      |"
    bottom_border
  fi

  while true; do
    read -p "${cyan}###### Link to your Obico Server account now? (Y/n):${white} " yn
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

  for name in "${not_linked_instances[@]}"; do
    status_msg "Link moonraker-obico-${name} to the Obico Server..."
    moonraker_obico_cfg="$(cfg_dir ${name})/moonraker-obico.cfg"
    if (( moonraker_count == 1 )); then
      "${MOONRAKER_OBICO_DIR}/scripts/link.sh" -q -c "${moonraker_obico_cfg}"
    else
      "${MOONRAKER_OBICO_DIR}/scripts/link.sh" -q -n "${name}" -c "${moonraker_obico_cfg}"
    fi
  done

}

function clone_or_update_moonraker_obico() {
  local repo=${1}

  if [[ -d ${MOONRAKER_OBICO_DIR} ]]; then
    status_msg "Updating ${MOONRAKER_OBICO_DIR} ..."
    cd ${MOONRAKER_OBICO_DIR} && git pull
  else
    status_msg "Cloning Moonraker-obico from ${repo} ..."
    cd "${HOME}" || exit 1
    if ! git clone "${MOONRAKER_OBICO_REPO}" "${MOONRAKER_OBICO_DIR}"; then
      print_error "Cloning Moonraker-obico from\n ${repo}\n failed!"
      exit 1
    fi
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
  local files regex="moonraker-obico(-[0-9a-zA-Z]+)?\.log([.-0-9]+)?"
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
  [[ ! -d "${HOME}/moonraker-obico-env" ]] && return

  status_msg "Removing moonraker-obico-env directory ..."
  rm -rf "${HOME}/moonraker-obico-env"
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

function update_moonraker_obico() {
  for service in $(moonraker_obico_systemd | cut -d"/" -f5); do
    do_action_service "stop" "${service}"
  done

  clone_or_update_moonraker_obico "${MOONRAKER_OBICO_REPO}"
  ok_msg "Update complete!"

  for service in $(moonraker_obico_systemd | cut -d"/" -f5); do
    do_action_service "restart" "${service}"
  done
}

#===================================================#
#============= MOONRAKER-OBICO STATUS ==============#
#===================================================#

function get_moonraker_obico_status() {
  local moonraker_obico_services sf_count status
  moonraker_obico_services=$(moonraker_obico_systemd)
  sf_count=$(echo "${moonraker_obico_services}" | wc -w )

  if (( sf_count == 0 )); then
    status="Not installed!"
  elif [[ ! -e "${MOONRAKER_OBICO_DIR}" ]]; then
    status="Incomplete!"
  else
    status="Installed!"
    for service in ${moonraker_obico_services}; do
      if ! is_moonraker_obico_linked "$(get_instance_name "${service}" moonraker-obico)"; then
        status="Not linked!"
      fi
    done
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
