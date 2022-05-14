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

#===================================================#
#========== INSTALL MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function telegram_bot_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-telegram-bot(-[^0])?[0-9]*.service" | sort)
  echo "${services}"
}

function telegram_bot_setup_dialog(){
  status_msg "Initializing Telegram Bot installation ..."

  ### return early if moonraker is not installed
  local moonraker_services
  moonraker_services=$(moonraker_systemd)
  if [[ -z "${moonraker_services}" ]]; then
    local error="Moonraker not installed! Please install Moonraker first!"
    log_error "Telegram Bot setup started without Moonraker being installed. Aborting setup."
    print_error "${error}" && return
  fi

  local moonraker_count user_input=() moonraker_names=()
  moonraker_count=$(echo "${moonraker_services}" | wc -w )
  for service in ${moonraker_services}; do
    moonraker_names+=( "$(get_instance_name "${service}")" )
  done

  local telegram_bot_count
  if (( moonraker_count == 1 )); then
    ok_msg "Moonraker installation found!\n"
    telegram_bot_count=1
  elif (( moonraker_count > 1 )); then
    top_border
    printf "|${green}%-55s${white}|\n" " ${moonraker_count} Moonraker instances found!"
    for name in "${moonraker_names[@]}"; do
      printf "|${cyan}%-57s${white}|\n" " ● ${name}"
    done
    blank_line
    echo -e "| The setup will apply the same names to Telegram Bot!  |"
    blank_line
    echo -e "| Please select the number of Telegram Bot instances to |"
    echo -e "| install. Usually one Telegram Bot instance per        |"
    echo -e "| Moonraker instance is required but you may not        |"
    echo -e "| install more Telegram Bot instances than available    |"
    echo -e "| Moonraker instances.                                  |"
    bottom_border

    ### ask for amount of instances
    local re="^[1-9][0-9]*$"
    while ! [[ ${telegram_bot_count} =~ ${re} && ${telegram_bot_count} -le ${moonraker_count} ]]; do
      read -p "${cyan}###### Number of Telegram Bot instances to set up:${white} " -i "${moonraker_count}" -e telegram_bot_count
      ### break if input is valid
      [[ ${telegram_bot_count} =~ ${re} && ${telegram_bot_count} -le ${moonraker_count} ]] && break
      ### conditional error messages
      error_msg "Invalid input:"
      ! [[ ${telegram_bot_count} =~ ${re} ]] && error_msg "● Input not a number"
      ((telegram_bot_count > moonraker_count)) && error_msg "● Number of Telegram Bot instances larger than existing Moonraker instances"
    done && select_msg "${telegram_bot_count}"
  else
    log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grather than one!"
    return 1
  fi

  user_input+=("${telegram_bot_count}")

### confirm instance amount
  while true; do
    ((telegram_bot_count == 1)) && local question="Install Telegram Bot?"
    ((telegram_bot_count > 1)) && local question="Install ${telegram_bot_count} Telegram Bot instances?"
    read -p "${cyan}###### ${question} (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        break;;
      N|n|No|no)
        select_msg "No"
        abort_msg "Exiting Telegram Bot setup ...\n"
        return;;
      *)
        error_msg "Invalid Input!";;
    esac
  done

  ### write existing klipper names into user_input array to use them as names for moonraker
  if (( moonraker_count > 1 )); then
    for name in "${moonraker_names[@]}"; do
      user_input+=("${name}")
    done
  fi

  ((telegram_bot_count > 1)) && status_msg "Installing ${telegram_bot_count} Telegram Bot instances ..."
  ((telegram_bot_count == 1)) && status_msg "Installing Telegram Bot ..."
  telegram_bot_setup "${user_input[@]}"
}

function install_telegram_bot_dependencies(){
  local packages
  local install_script="${MOONRAKER_TELEGRAM_BOT_DIR}/scripts/install.sh"

  ### read PKGLIST from official install script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package info
  status_msg "Updating lists of packages..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install required packages
  status_msg "Installing packages..."
  sudo apt-get install --yes "${packages[@]}"
}

function create_telegram_bot_virtualenv(){
  status_msg "Installing python virtual environment..."
  ### always create a clean virtualenv
  [[ -d ${MOONRAKER_TELEGRAM_BOT_ENV_DIR} ]] && rm -rf "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"
  virtualenv -p /usr/bin/python3 --system-site-packages "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"
  "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"/bin/pip install -r "${MOONRAKER_TELEGRAM_BOT_DIR}/scripts/requirements.txt"
}

function telegram_bot_setup(){
  local instance_arr=("${@}")
  ### checking dependencies
  local dep=(git virtualenv)
  dependency_check "${dep[@]}"

  ### step 1: clone telegram bot
  status_msg "Downloading Moonraker-Telegram-Bot ..."
  ### force remove existing Moonraker-Telegram-Bot dir
  [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ]] && rm -rf "${MOONRAKER_TELEGRAM_BOT_DIR}"
  cd "${HOME}" && git clone "${MOONRAKER_TELEGRAM_BOT_REPO}"

  ### step 2: install telegram bot dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_telegram_bot_dependencies
  create_telegram_bot_virtualenv

  ### step 3: create telegram.conf
  create_telegram_conf "${instance_arr[@]}"

  ### step 4: create telegram bot instances
  create_telegram_bot_service "${instance_arr[@]}"

  ### step 5: enable and start all instances
  do_action_service "enable" "moonraker-telegram-bot"
  do_action_service "start" "moonraker-telegram-bot"

  ### confirm message
  local confirm=""
  (( instance_arr[0] == 1)) && confirm="Telegram Bot has been set up!"
  (( instance_arr[0] > 1)) && confirm="${instance_arr[0]} Telegram Bot instances have been set up!"
  print_confirm "${confirm}" && return
}

function create_telegram_conf(){
  local input=("${@}")
  local telegram_bot_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local log="${KLIPPER_LOGS}"

  if (( telegram_bot_count == 1 )); then
    cfg_dir="${KLIPPER_CONFIG}"
    cfg="${cfg_dir}/telegram.conf"
    ### write single instance config
    write_telegram_conf "${cfg_dir}" "${cfg}" "${log}"

  elif (( telegram_bot_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for ((i=1; i <= telegram_bot_count; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      ### write multi instance config
      write_telegram_conf "${cfg_dir}" "${cfg}" "${log}"
      port=$((port+1))
      j=$((j+1))
    done && unset j

  else
    return 1
  fi
}

function write_telegram_conf(){
  local cfg_dir=${1} cfg=${2} log=${3}
  local conf_template="${MOONRAKER_TELEGRAM_BOT_DIR}/scripts/base_install_template"
  ! [[ -d "${cfg_dir}" ]] && mkdir -p "${cfg_dir}"

  if ! [[ -f "${cfg}" ]]; then
    status_msg "Creating telegram.conf in ${cfg_dir} ..."
    cp "${conf_template}" "${cfg}"
    sed -i "s|some_log_path|${log}|g" "${cfg}"
    ok_msg "telegram.conf created!"
  else
    status_msg "File '${cfg}' already exists!\nSkipping..."
  fi
}

function create_telegram_bot_service(){
  local input=("${@}")
  local instances=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local cfg_dir cfg service
  if (( instances == 1 )); then
    cfg_dir="${KLIPPER_CONFIG}"
    cfg="${cfg_dir}/telegram.conf"
    service="${SYSTEMD}/moonraker-telegram-bot.service"
    ### write single instance service
    write_telegram_bot_service "" "${cfg}" "${service}"
    ok_msg "Single Telegram Bot instance created!"

  elif (( instances > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for ((i=1; i <= instances; i++ )); do

      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        cfg_dir="${KLIPPER_CONFIG}/printer_${names[${j}]}"
      else
        cfg_dir="${KLIPPER_CONFIG}/${names[${j}]}"
      fi

      cfg="${cfg_dir}/telegram.conf"
      service="${SYSTEMD}/moonraker-telegram-bot-${names[${j}]}.service"
      ### write multi instance service
      write_telegram_bot_service "${i}(${names[${j}]})" "${cfg}" "${service}"
      ok_msg "Telegram Bot instance #${i}(${names[${j}]}) created!"
      j=$((j+1))

    done && unset j

  else
    return 1
  fi
}

function write_telegram_bot_service(){
  local i=${1} cfg=${2} service=${3}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker-telegram-bot.service"

  ### replace all placeholders
  if ! [[ -f "${service}" ]]; then
    status_msg "Creating Telegram Bot Service ${i} ..."
    sudo cp "${service_template}" "${service}"
    [[ -z ${i} ]] && sudo sed -i "s|instance %INST% ||" "${service}"
    [[ -n ${i} ]] && sudo sed -i "s|%INST%|${i}|" "${service}"
    sudo sed -i "s|%USER%|${USER}|; s|%ENV%|${MOONRAKER_TELEGRAM_BOT_ENV_DIR}|; s|%DIR%|${MOONRAKER_TELEGRAM_BOT_DIR}|" "${service}"
    sudo sed -i "s|%CFG%|${cfg}|" "${service}"
  fi
}


#===================================================#
#=========== REMOVE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function remove_telegram_bot_systemd() {
  [[ -z "$(telegram_bot_systemd)" ]] && return
  status_msg "Removing Telegram Bot Systemd Services ..."
  for service in $(telegram_bot_systemd | cut -d"/" -f5); do
    status_msg "Removing ${service} ..."
    sudo systemctl stop "${service}"
    sudo systemctl disable "${service}"
    sudo rm -f "${SYSTEMD}/${service}"
    ok_msg "Done!"
  done
  ### reloading units
  sudo systemctl daemon-reload
  sudo systemctl reset-failed
  ok_msg "Telegram Bot Services removed!"
}

function remove_telegram_bot_dir() {
  ! [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ]] && return
  status_msg "Removing Moonraker-Telegram-Bot directory ..."
  rm -rf "${MOONRAKER_TELEGRAM_BOT_DIR}"
  ok_msg "Directory removed!"
}

function remove_telegram_bot_env() {
  ! [[ -d "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}" ]] && return
  status_msg "Removing moonraker-telegram-bot-env directory ..."
  rm -rf "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"
  ok_msg "Directory removed!"
}

function remove_telegram_bot_logs() {
  if [[ -f "/tmp/telegram.log"|| -f "${HOME}/klipper_logs/telegram.log" ]]; then
    status_msg "Removing Moonraker-Telegram-Bot log file ..."
    rm -f "/tmp/telegram.log" "${HOME}/klipper_logs/telegram.log"
    ok_msg "File removed!"
  fi
}

function remove_telegram_bot(){
  remove_telegram_bot_systemd
  remove_telegram_bot_dir
  remove_telegram_bot_env
  remove_telegram_bot_logs

  local confirm="Moonraker-Telegram-Bot was successfully removed!"
  print_confirm "${confirm}" && return
}

#===================================================#
#=========== UPDATE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function update_telegram_bot(){
  do_action_service "stop" "moonraker-telegram-bot"
  if ! [[ -d ${MOONRAKER_TELEGRAM_BOT_DIR} ]]; then
    cd "${HOME}" && git clone "${MOONRAKER_TELEGRAM_BOT_REPO}"
  else
    backup_before_update "moonraker-telegram-bot"
    status_msg "Updating Moonraker ..."
    cd "${MOONRAKER_TELEGRAM_BOT_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_telegram_bot_dependencies
    ### install possible new python dependencies
    "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"/bin/pip install -r "${MOONRAKER_TELEGRAM_BOT_DIR}/scripts/requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "start" "moonraker-telegram-bot"
}

#===================================================#
#=========== MOONRAKERTELEGRAMBOT STATUS ===========#
#===================================================#

function get_telegram_bot_status(){
  local sf_count status
  sf_count="$(telegram_bot_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${MOONRAKER_TELEGRAM_BOT_DIR}" "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}")
  ((sf_count > 0)) && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && filecount=$((filecount + 1))
  done

  if ((filecount == ${#data_arr[*]})); then
    status="Installed: ${sf_count}"
  elif ((filecount == 0)); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi
  echo "${status}"
}

function get_local_telegram_bot_commit(){
  local commit
  ! [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ]] || ! [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}"/.git ]] && return
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_telegram_bot_commit(){
  local commit
  ! [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ]] || ! [[ -d "${MOONRAKER_TELEGRAM_BOT_DIR}"/.git ]] && return
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_telegram_bot_versions(){
  unset MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_telegram_bot_commit)"
  remote_ver="$(get_remote_telegram_bot_commit)"
  if [[ "${local_ver}" != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker-telegram-bot to the update all array for the update all function in the updater
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="true" && update_arr+=(update_telegram_bot)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}
