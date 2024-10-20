#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

# Error Handling
set -e

function install_spoolman() {

  pushd "${HOME}" &> /dev/null || exit 1

  dependency_check curl jq

  if [[ ! -d "${SPOOLMAN_DIR}" && -z "$(ls -A "${SPOOLMAN_DIR}" 2> /dev/null)" ]]; then
    status_msg "Downloading spoolman..."
    setup_spoolman_folder
    status_msg "Downloading complete"
    start_install_script
    advanced_config_prompt
  else
    ### In case spoolman is "incomplete" rerun install script
    if get_spoolman_status | grep -q "Incomplete!"; then
      start_install_script
      exit 1
    fi

    ok_msg "Spoolman already installed"
    exit 1
  fi

  enable_moonraker_integration_prompt
  patch_spoolman_update_manager

  do_action_service "restart" "moonraker"
}

function update_spoolman() {
  ### stop and disable old spoolman service
  do_action_service "stop" "Spoolman"
  do_action_service "disable" "Spoolman"

  mv "${SPOOLMAN_DIR}" "${SPOOLMAN_DIR}_old"

  setup_spoolman_folder
  cp "${SPOOLMAN_DIR}_old/.env" "${SPOOLMAN_DIR}/.env"

  start_install_script

  rm -rf "${SPOOLMAN_DIR}_old"
}

function remove_spoolman(){
  if [[ -d "${SPOOLMAN_DIR}" ]]; then
    status_msg "Removing spoolman service..."
    do_action_service "stop" "Spoolman"
    do_action_service "disable" "Spoolman"
    sudo rm -f "${SYSTEMD}/Spoolman.service"
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "Spoolman service removed!"

    status_msg "Removing spoolman directory..."
    rm -rf "${SPOOLMAN_DIR}"
    ok_msg "Spoolman directory removed!"
  fi

  print_confirm "Spoolman successfully removed!"
}

function update_moonraker_configs() {
  local moonraker_configs regex
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager Spoolman\]\s*$" "${conf}"; then
      ### add new line to conf if it doesn't end with one
      [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF
${1}
MOONRAKER_CONF
    fi
  done
}

function enable_moonraker_integration() {
  local integration_str env_port
  # get spoolman port from .env
  env_port=$(grep "^SPOOLMAN_PORT=" "${SPOOLMAN_DIR}/.env" | cut -d"=" -f2)

  integration_str="
[spoolman]
server: http://$(hostname -I | cut -d" " -f1):${env_port}
"

  status_msg "Adding Spoolman integration..."
  update_moonraker_configs "${integration_str}"
}

function patch_spoolman_update_manager() {
  local updater_str
  updater_str="
[update_manager Spoolman]
type: zip
channel: stable
repo: Donkie/Spoolman
path: ${SPOOLMAN_DIR}
virtualenv: .venv
requirements: requirements.txt
persistent_files:
  .venv
  .env
managed_services: Spoolman
"

  update_moonraker_configs "${updater_str}"

  # add spoolman service to moonraker.asvc
  local moonraker_asvc regex
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/moonraker\.asvc"
  moonraker_asvc=$(find "${HOME}" -maxdepth 2 -type f -regextype posix-extended -regex "${regex}" | sort)

  if ! grep -q "^Spoolman$" "${moonraker_asvc}"; then
    status_msg "Adding Spoolman service to moonraker.asvc..."
    sed -i '$a''Spoolman' "${moonraker_asvc}"
  fi
}

function advanced_config_prompt() {
  local reply
  while true; do
    read -erp "${cyan}###### Continue with default configuration? (Y/n):${white} " reply
    case "${reply}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        advanced_config
        break;;
      *)
        error_msg "Invalid Input!\n";;
    esac
  done
  return 0
}

function enable_moonraker_integration_prompt() {
  local reply
  while true; do
    read -erp "${cyan}###### Enable Moonraker integration? (Y/n):${white} " reply
    case "${reply}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        enable_moonraker_integration
        break;;
      N|n|No|no)
        select_msg "No"
        break;;
      *)
        error_msg "Invalid Input!\n";;
    esac
  done
  return 0
}

function advanced_config() {
  status_msg "###### Advanced configuration"

  local reply
  while true; do
    read -erp "${cyan}###### Select spoolman port (7912):${white} " reply
    ### set default
    if [[ -z "${reply}" ]]; then
      reply="7912"
    fi

    select_msg "${reply}"
    ### check if port is valid
    if ! [[ "${reply}" =~ ^[0-9]+$ && "${reply}" -ge 1024 && "${reply}" -le 65535 ]]; then
      error_msg "Invalid port number!\n"
      continue
    fi

    ### update .env
    sed -i "s/^SPOOLMAN_PORT=.*$/SPOOLMAN_PORT=${reply}/" "${SPOOLMAN_DIR}/.env"
    do_action_service "restart" "Spoolman"
    break
  done
  return 0
}

function setup_spoolman_folder() {
  local source_url
  ### get latest spoolman release url
  source_url="$(curl -s "${SPOOLMAN_REPO}" | jq -r '.assets[] | select(.name == "spoolman.zip").browser_download_url')"

  mkdir -p "${SPOOLMAN_DIR}"
  curl -sSL "${source_url}" -o /tmp/temp.zip
  unzip /tmp/temp.zip -d "${SPOOLMAN_DIR}" &> /dev/null
  rm /tmp/temp.zip

  chmod +x "${SPOOLMAN_DIR}"/scripts/install.sh
}

function start_install_script() {

  pushd "${SPOOLMAN_DIR}" &> /dev/null || exit 1

  if bash ./scripts/install.sh; then
    ok_msg "Spoolman successfully installed!"
  else
    print_error "Spoolman installation failed!"
    exit 1
  fi
}

function get_spoolman_status() {
  local -a files
  files=(
      "${SPOOLMAN_DIR}"
      "${SYSTEMD}/Spoolman.service"
      "${SPOOLMAN_DB_DIR}"
    )

  local count
  count=0

  for file in "${files[@]}"; do
    [[ -e "${file}" ]] && count=$(( count +1 ))
  done

  if [[ "${count}" -eq "${#files[*]}" ]]; then
    echo "Installed"
  elif [[ "${count}" -gt 0 ]]; then
    echo "Incomplete!"
  else
    echo "Not installed!"
  fi
}

function get_local_spoolman_version() {
  [[ ! -d "${SPOOLMAN_DIR}" ]] && return

  local version
  version=$(grep -o '"version":\s*"[^"]*' "${SPOOLMAN_DIR}"/release_info.json | cut -d'"' -f4)
  echo "${version}"
}

function get_remote_spoolman_version() {
  [[ ! -d "${SPOOLMAN_DIR}" ]] && return

  local version
  version=$(curl -s "${SPOOLMAN_REPO}" | grep -o '"tag_name":\s*"v[^"]*"' | cut -d'"' -f4)
  echo "${version}"
}

function compare_spoolman_versions() {
  local local_ver remote_ver
  local_ver="$(get_local_spoolman_version)"
  remote_ver="$(get_remote_spoolman_version)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add spoolman to application_updates_available in kiauh.ini
    add_to_application_updates "spoolman"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}
