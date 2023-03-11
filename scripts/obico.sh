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
#============== INSTALL MOONRAKER-OBICO ============#
#===================================================#

function moonraker_obico_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-obico(-[0-9a-zA-Z]+)?.service")
  echo "${services}"
}

function moonraker_obico_config() {
  local moonraker_cfg_dirs

  read -r -a moonraker_cfg_dirs <<< "$(get_instance_folder_path "config")"

  if (( ${#moonraker_cfg_dirs[@]} > 0 )); then
    echo "${moonraker_cfg_dirs[${1}]}/moonraker-obico.cfg"
  else
    echo ""
  fi
}

function moonraker_obico_needs_linking() {
  local moonraker_obico_cfg=${1}
  if [[ ! -f "${moonraker_obico_cfg}" ]]; then
    return 1
  fi
  if grep -s -E "^[^#]" "${moonraker_obico_cfg}" | grep -q 'auth_token'; then
    return 1
  else
    return 0
  fi
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
  echo -e "| For instance, 'http://192.168.0.5:3334'.              |"
  bottom_border
}

function moonraker_obico_setup_dialog() {
  status_msg "Initializing Moonraker-obico installation ..."

  local moonraker_count
  local moonraker_names

  moonraker_count=$(moonraker_systemd | wc -w)

  if (( moonraker_count == 0 )); then
    ### return early if moonraker is not installed
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error "Moonraker-obico setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  elif (( moonraker_count > 1 )); then
    # moonraker_names is valid only in case of multi-instance
    read -r -a moonraker_names <<< "$(get_multi_instance_names)"
  fi

  local moonraker_obico_services
  local existing_moonraker_obico_count
  moonraker_obico_services=$(moonraker_obico_systemd)
  existing_moonraker_obico_count=$(echo "${moonraker_obico_services}" | wc -w )
  local allowed_moonraker_obico_count=$(( moonraker_count - existing_moonraker_obico_count ))
  if (( allowed_moonraker_obico_count > 0 )); then
    local new_moonraker_obico_count

    ### Step 1: Ask for the number of moonraker-obico instances to install
    if (( moonraker_count == 1 )); then
      ok_msg "Moonraker installation found!\n"
      new_moonraker_obico_count=1
    elif (( moonraker_count > 1 )); then
      top_border
      printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
      for name in "${moonraker_names[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ● moonraker-${name}"
      done
      blank_line
      if (( existing_moonraker_obico_count > 0 )); then
        printf "|${green}%-55s${white}|\n" " ${existing_moonraker_obico_count} Moonraker-obico instances already installed!"
        for svc in ${moonraker_obico_services}; do
          printf "|${cyan}%-57s${white}|\n" " ● moonraker-obco-$(get_instance_name "${svc}")"
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
      local re="^[1-9][0-9]*$"
      while [[ ! ${new_moonraker_obico_count} =~ ${re} || ${new_moonraker_obico_count} -gt ${allowed_moonraker_obico_count} ]]; do
        read -p "${cyan}###### Number of new Moonraker-obico instances to set up:${white} " -i "${allowed_moonraker_obico_count}" -e new_moonraker_obico_count
        ### break if input is valid
        [[ ${new_moonraker_obico_count} =~ ${re} && ${new_moonraker_obico_count} -le ${allowed_moonraker_obico_count} ]] && break
        ### conditional error messages
        [[ ! ${new_moonraker_obico_count} =~ ${re} ]] && error_msg "Input not a number"
        (( new_moonraker_obico_count > allowed_moonraker_obico_count )) && error_msg "Number of Moonraker-obico instances larger than installed Moonraker instances"
      done && select_msg "${new_moonraker_obico_count}"
    else
      log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grather than one!"
      return 1
    fi  # (( moonraker_count == 1 ))

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
  fi  # (( allowed_moonraker_obico_count > 0 ))

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
    clone_moonraker_obico "${MOONRAKER_OBICO_REPO}"

    ### step 6: call moonrake-obico/install.sh with the correct params
    local port=7125
    local instance_cfg_dirs
    local instance_log_dirs

    read -r -a instance_cfg_dirs <<< "$(get_instance_folder_path "config")"
    read -r -a instance_log_dirs <<< "$(get_instance_folder_path "logs")"

    if (( moonraker_count == 1 )); then
      "${MOONRAKER_OBICO_DIR}/install.sh"\
      -C "${instance_cfg_dirs[0]}/moonraker.conf"\
      -p "${port}" -H 127.0.0.1 -l\
      "${instance_log_dirs[0]}"\
      -L -S "${obico_server_url}"
    elif (( moonraker_count > 1 )); then
      local j=${existing_moonraker_obico_count}

      for (( i=1; i <= new_moonraker_obico_count; i++ )); do
        "${MOONRAKER_OBICO_DIR}/install.sh"\
        -n "${moonraker_names[${j}]}"\
        -C "${instance_cfg_dirs[${j}]}/moonraker.conf"\
        -p $((port+j))\
        -H 127.0.0.1\
        -l "${instance_log_dirs[${j}]}"\
        -L -S "${obico_server_url}"
        j=$(( j + 1 ))
      done && unset j
    fi # (( moonraker_count == 1 ))
  fi  # (( new_moonraker_obico_count > 0 ))

  ### Step 7: Link to the Obico server if necessary
  local not_linked_instances=()
  if (( moonraker_count == 1 )); then
    if moonraker_obico_needs_linking "$(moonraker_obico_config 0)"; then
      not_linked_instances+=("0")
    fi
  elif (( moonraker_count > 1 )); then
    for (( i=0; i <= moonraker_count; i++ )); do
      if moonraker_obico_needs_linking "$(moonraker_obico_config "${i}")"; then
        not_linked_instances+=("${i}")
      fi
    done
  fi  # (( moonraker_count == 1 ))

  if (( ${#not_linked_instances[@]} > 0 )); then
    top_border
    if (( moonraker_count == 1 )); then
      printf "|${green}%-55s${white}|\n" " Moonraker-obico not linked to the server!"
    else
      printf "|${green}%-55s${white}|\n" " ${#not_linked_instances[@]} Moonraker-obico instances not linked to the server!"
      for i in "${not_linked_instances[@]}"; do
        printf "|${cyan}%-57s${white}|\n" " ● moonraker-obico-${moonraker_names[${i}]}"
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
    echo -e "| 1. 'cd ~/kiauh && ./kiauh.sh' to launch KIAUH.        |"
    echo -e "| 2. Select ${green}[Install]${white}                                   |"
    echo -e "| 3. Select ${green}[Link to Obico Server]${white}                      |"
    bottom_border

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

    if (( moonraker_count == 1 )); then
      status_msg "Link moonraker-obico to the Obico Server..."
      "${MOONRAKER_OBICO_DIR}/scripts/link.sh" -q -c "$(moonraker_obico_config 0)"
    elif (( moonraker_count > 1 )); then
      for i in "${not_linked_instances[@]}"; do
        local name="${moonraker_names[i]}"
        status_msg "Link moonraker-obico-${name} to the Obico Server..."
        "${MOONRAKER_OBICO_DIR}/scripts/link.sh" -q -n "${name}" -c "$(moonraker_obico_config "${i}")"
      done
    fi  # (( moonraker_count == 1 ))
  fi  # (( ${#not_linked_instances[@]} > 0 ))
}

function clone_moonraker_obico() {
  local repo=${1}

  status_msg "Cloning Moonraker-obico from ${repo} ..."
  ### force remove existing Moonraker-obico dir
  [[ -d "${MOONRAKER_OBICO_DIR}" ]] && rm -rf "${MOONRAKER_OBICO_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${repo}" "${MOONRAKER_OBICO_DIR}"; then
    print_error "Cloning Moonraker-obico from\n ${repo}\n failed!"
    exit 1
  fi
}

function moonraker_obico_install() {
  "${MOONRAKER_OBICO_DIR}/install.sh" "$@"
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
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/moonraker-obico(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_legacy_moonraker_obico_logs() {
  local files regex="moonraker-obico(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/${regex}" 2> /dev/null | sort)

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
  do_action_service "stop" "moonraker-obico"

  if [[ ! -d ${MOONRAKER_OBICO_DIR} ]]; then
    clone_moonraker_obico "${MOONRAKER_OBICO_REPO}"
  else
    status_msg "Updating Moonraker-obico ..."
    cd "${MOONRAKER_OBICO_DIR}" && git pull
  fi

  ok_msg "Update complete!"
  do_action_service "restart" "moonraker-obico"
}

#===================================================#
#============= MOONRAKER-OBICO STATUS ==============#
#===================================================#

function get_moonraker_obico_status() {
  local status
  local service_count
  local is_linked
  local moonraker_obico_services

  moonraker_obico_services=$(moonraker_obico_systemd)
  service_count=$(echo "${moonraker_obico_services}" | wc -w )

  is_linked="true"
  if [[ -n ${moonraker_obico_services} ]]; then
    for cfg_dir in $(get_instance_folder_path "config"); do
      if moonraker_obico_needs_linking "${cfg_dir}/moonraker-obico.cfg"; then
        is_linked="false"
      fi
    done
  fi

  if (( service_count == 0 )); then
    status="Not installed!"
  elif [[ ! -d "${MOONRAKER_OBICO_DIR}" ]]; then
    status="Incomplete!"
  elif [[ ${is_linked} == "false" ]]; then
    status="Not linked!"
  else
    status="Installed!"
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

###
# it is possible, that moonraker_obico is installed in a so called
# "non-linked" state. the linking can be achieved by running the
# installation script again. this function will check the obico
# installation status and returns the correctly formulated menu title
#
function obico_install_title() {
  if [[ $(get_moonraker_obico_status) == "Not linked!" ]]; then
    echo "[Link to Obico Server]"
  else
    echo "[Obico for Klipper]   "
  fi
}

