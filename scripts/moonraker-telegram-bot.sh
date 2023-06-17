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
#========== INSTALL MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function telegram_bot_systemd() {
  local services
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-telegram-bot(-[0-9a-zA-Z]+)?.service" | sort)
  echo "${services}"
}

function telegram_bot_setup_dialog() {
  ### return early if moonraker is not installed
  local moonraker_services
  moonraker_services=$(moonraker_systemd)

  if [[ -z ${moonraker_services} ]]; then
    local error="Moonraker not installed! Please install Moonraker first!"
    print_error "${error}" && return
  fi

  status_msg "Initializing Telegram Bot installation ..."
  ### first, we create a backup of the full klipper_config dir - safety first!
  backup_klipper_config_dir

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
    echo -e "| Moonraker instance is required, but you may not       |"
    echo -e "| install more Telegram Bot instances than available    |"
    echo -e "| Moonraker instances.                                  |"
    bottom_border

    ### ask for amount of instances
    local re="^[1-9][0-9]*$"
    while [[ ! ${telegram_bot_count} =~ ${re} || ${telegram_bot_count} -gt ${moonraker_count} ]]; do
      read -p "${cyan}###### Number of Telegram Bot instances to set up:${white} " -i "${moonraker_count}" -e telegram_bot_count
      ### break if input is valid
      [[ ${telegram_bot_count} =~ ${re} && ${telegram_bot_count} -le ${moonraker_count} ]] && break
      ### conditional error messages
      [[ ! ${telegram_bot_count} =~ ${re} ]] && error_msg "Input not a number"
      (( telegram_bot_count > moonraker_count )) && error_msg "Number of Telegram Bot instances larger than existing Moonraker instances"
    done && select_msg "${telegram_bot_count}"
  else
    log_error "Internal error. moonraker_count of '${moonraker_count}' not equal or grather than one!"
    return 1
  fi

  user_input+=("${telegram_bot_count}")

  ### confirm instance amount
  local yn
  while true; do
    (( telegram_bot_count == 1 )) && local question="Install Telegram Bot?"
    (( telegram_bot_count > 1 )) && local question="Install ${telegram_bot_count} Telegram Bot instances?"
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

  (( telegram_bot_count > 1 )) && status_msg "Installing ${telegram_bot_count} Telegram Bot instances ..."
  (( telegram_bot_count == 1 )) && status_msg "Installing Telegram Bot ..."
  telegram_bot_setup "${user_input[@]}"
}

function install_telegram_bot_dependencies() {
  local packages log_name="Telegram Bot"
  local install_script="${TELEGRAM_BOT_DIR}/scripts/install.sh"

  ### read PKGLIST from official install-script
  status_msg "Reading dependencies..."
  # shellcheck disable=SC2016
  packages="$(grep "PKGLIST=" "${install_script}" | cut -d'"' -f2 | sed 's/\${PKGLIST}//g' | tr -d '\n')"

  echo "${cyan}${packages}${white}" | tr '[:space:]' '\n'
  read -r -a packages <<< "${packages}"

  ### Update system package lists if stale
  update_system_package_lists

  ### Install required packages
  install_system_packages "${log_name}" "packages[@]"
}

function create_telegram_bot_virtualenv() {
  status_msg "Installing python virtual environment..."
  ### always create a clean virtualenv
  [[ -d ${TELEGRAM_BOT_ENV} ]] && rm -rf "${TELEGRAM_BOT_ENV}"
  if virtualenv -p /usr/bin/python3 --system-site-packages "${TELEGRAM_BOT_ENV}"; then
    "${TELEGRAM_BOT_ENV}"/bin/pip install -r "${TELEGRAM_BOT_DIR}/scripts/requirements.txt"
  else
    log_error "failure while creating python3 moonraker-telegram-bot-env"
    error_msg "Creation of Moonraker Telegram Bot virtualenv failed!"
    exit 1
  fi
}

function telegram_bot_setup() {
  local instance_arr=("${@}")
  ### checking dependencies
  local dep=(git virtualenv)
  dependency_check "${dep[@]}"

  ### step 1: clone telegram bot
  clone_telegram_bot "${TELEGRAM_BOT_REPO}"

  ### step 2: install telegram bot dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_telegram_bot_dependencies
  create_telegram_bot_virtualenv

  ### step 3: create telegram.conf
  create_telegram_conf "${instance_arr[@]}"

  ### step 4: create telegram bot instances
  create_telegram_bot_service "${instance_arr[@]}"

  ### step 5: add telegram-bot to the update manager in moonraker.conf
  patch_telegram_bot_update_manager

  ### step 6: enable and start all instances
  do_action_service "enable" "moonraker-telegram-bot"
  do_action_service "start" "moonraker-telegram-bot"

  ### confirm message
  local confirm=""
  (( instance_arr[0] == 1 )) && confirm="Telegram Bot has been set up!"
  (( instance_arr[0] > 1 )) && confirm="${instance_arr[0]} Telegram Bot instances have been set up!"
  print_confirm "${confirm}" && return
}

function clone_telegram_bot() {
  local repo=${1}

  status_msg "Cloning Moonraker-Telegram-Bot from ${repo} ..."
  ### force remove existing Moonraker-Telegram-Bot dir
  [[ -d ${repo} ]] && rm -rf "${TELEGRAM_BOT_DIR}"

  cd "${HOME}" || exit 1
  if ! git clone "${repo}" "${TELEGRAM_BOT_DIR}"; then
    print_error "Cloning Moonraker-Telegram-Bot from\n ${repo}\n failed!"
    exit 1
  fi
}

function create_telegram_conf() {
  local input=("${@}")
  local telegram_bot_count=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local printer_data log_dir cfg cfg_dir

  if (( telegram_bot_count == 1 )); then
    printer_data="${HOME}/printer_data"
    log_dir="${printer_data}/logs"
    cfg_dir="${printer_data}/config"
    cfg="${cfg_dir}/telegram.conf"

    ### create required folder structure
    create_required_folders "${printer_data}"

    ### write single instance config
    write_telegram_conf "${cfg_dir}" "${cfg}"

  elif (( telegram_bot_count > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= telegram_bot_count; i++ )); do

      printer_data="${HOME}/${names[${j}]}_data"
      ### prefix instance name with "printer_" if it is only a number
      [[ ${names[j]} =~ ${re} ]] && printer_data="${HOME}/printer_${names[${j}]}_data"


      cfg_dir="${printer_data}/config"
      cfg="${cfg_dir}/telegram.conf"
      log_dir="${printer_data}/logs"

      ### create required folder structure
      create_required_folders "${printer_data}"

      ### write multi instance config
      write_telegram_conf "${cfg_dir}" "${cfg}"

      j=$(( j + 1 ))
    done && unset j

  else
    return 1
  fi
}

function write_telegram_conf() {
  local cfg_dir=${1} cfg=${2}
  local conf_template="${TELEGRAM_BOT_DIR}/scripts/base_install_template"

  if [[ ! -f ${cfg} ]]; then
    status_msg "Creating telegram.conf in ${cfg_dir} ..."
    cp "${conf_template}" "${cfg}"
    ok_msg "telegram.conf created!"
  else
    ok_msg "File '${cfg}' already exists! Skipping..."
  fi
}

function create_telegram_bot_service() {
  local input=("${@}")
  local instances=${input[0]} && unset "input[0]"
  local names=("${input[@]}") && unset "input[@]"
  local printer_data cfg_dir cfg log service env_file

  if (( instances == 1 )); then
    printer_data="${HOME}/printer_data"
    cfg_dir="${printer_data}/config"
    cfg="${cfg_dir}/telegram.conf"
    log="${printer_data}/logs/telegram.log"
    service="${SYSTEMD}/moonraker-telegram-bot.service"
    env_file="${printer_data}/systemd/moonraker-telegram-bot.env"

    ### create required folder structure
    create_required_folders "${printer_data}"

    ### write single instance service
    write_telegram_bot_service "" "${cfg}" "${log}" "${service}" "${env_file}"
    ok_msg "Telegram Bot instance created!"

  elif (( instances > 1 )); then
    local j=0 re="^[1-9][0-9]*$"

    for (( i=1; i <= instances; i++ )); do
      ### overwrite config folder if name is only a number
      if [[ ${names[j]} =~ ${re} ]]; then
        printer_data="${HOME}/printer_${names[${j}]}_data"
      else
        printer_data="${HOME}/${names[${j}]}_data"
      fi

      cfg_dir="${printer_data}/config"
      cfg="${cfg_dir}/telegram.conf"
      log="${printer_data}/logs/telegram.log"
      service="${SYSTEMD}/moonraker-telegram-bot-${names[${j}]}.service"
      env_file="${printer_data}/systemd/moonraker-telegram-bot.env"

      ### create required folder structure
      create_required_folders "${printer_data}"

      ### write multi instance service
      if write_telegram_bot_service "${names[${j}]}" "${cfg}" "${log}" "${service}" "${env_file}"; then
        ok_msg "Telegram Bot instance moonraker-telegram-bot-${names[${j}]} created!"
      else
        error_msg "An error occured during creation of instance moonraker-telegram-bot-${names[${j}]}!"
      fi

      j=$(( j + 1 ))
    done && unset j

  else
    return 1
  fi
}

function write_telegram_bot_service() {
  local i=${1} cfg=${2} log=${3} service=${4} env_file=${5}
  local service_template="${KIAUH_SRCDIR}/resources/moonraker-telegram-bot.service"
  local env_template="${KIAUH_SRCDIR}/resources/moonraker-telegram-bot.env"

  ### replace all placeholders
  if [[ ! -f ${service} ]]; then
    status_msg "Creating service file for instance ${i} ..."
    sudo cp "${service_template}" "${service}"
    if [[ -z ${i} ]]; then
      sudo sed -i "s| %INST%||" "${service}"
    else
      sudo sed -i "s|%INST%|${i}|" "${service}"
    fi
    sudo sed -i "s|%USER%|${USER}|g; s|%TELEGRAM_BOT_DIR%|${TELEGRAM_BOT_DIR}|; s|%ENV%|${TELEGRAM_BOT_ENV}|; s|%ENV_FILE%|${env_file}|" "${service}"

    status_msg "Creating environment file for instance ${i} ..."
    cp "${env_template}" "${env_file}"
    sed -i "s|%USER%|${USER}|; s|%TELEGRAM_BOT_DIR%|${TELEGRAM_BOT_DIR}|; s|%CFG%|${cfg}|; s|%LOG%|${log}|" "${env_file}"
  fi
}


#===================================================#
#=========== REMOVE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function remove_telegram_bot_systemd() {
  [[ -z $(telegram_bot_systemd) ]] && return

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
  [[ ! -d ${TELEGRAM_BOT_DIR} ]] && return

  status_msg "Removing Moonraker-Telegram-Bot directory ..."
  rm -rf "${TELEGRAM_BOT_DIR}"
  ok_msg "Directory removed!"
}

function remove_telegram_bot_env() {
  [[ ! -d ${TELEGRAM_BOT_ENV} ]] && return

  status_msg "Removing moonraker-telegram-bot-env directory ..."
  rm -rf "${TELEGRAM_BOT_ENV}"
  ok_msg "Directory removed!"
}

function remove_telegram_bot_env_file() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/systemd\/moonraker-telegram-bot\.env"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_telegram_bot_logs() {
  local files regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/telegram\.log.*"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_legacy_telegram_bot_logs() {
  local files regex="telegram(-[0-9a-zA-Z]+)?\.log(.*)?"
  files=$(find "${HOME}/klipper_logs" -maxdepth 1 -regextype posix-extended -regex "${HOME}/klipper_logs/${regex}" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_telegram_bot() {
  remove_telegram_bot_systemd
  remove_telegram_bot_dir
  remove_telegram_bot_env
  remove_telegram_bot_env_file
  remove_telegram_bot_logs
  remove_legacy_telegram_bot_logs

  local confirm="Moonraker-Telegram-Bot was successfully removed!"
  print_confirm "${confirm}" && return
}

#===================================================#
#=========== UPDATE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function update_telegram_bot() {
  do_action_service "stop" "moonraker-telegram-bot"

  if [[ ! -d ${TELEGRAM_BOT_DIR} ]]; then
    clone_telegram_bot "${TELEGRAM_BOT_REPO}"
  else
    backup_before_update "moonraker-telegram-bot"
    status_msg "Updating Moonraker ..."
    cd "${TELEGRAM_BOT_DIR}" && git pull
    ### read PKGLIST and install possible new dependencies
    install_telegram_bot_dependencies
    ### install possible new python dependencies
    "${TELEGRAM_BOT_ENV}"/bin/pip install -r "${TELEGRAM_BOT_DIR}/scripts/requirements.txt"
  fi

  ok_msg "Update complete!"
  do_action_service "start" "moonraker-telegram-bot"
}

#===================================================#
#=========== MOONRAKERTELEGRAMBOT STATUS ===========#
#===================================================#

function get_telegram_bot_status() {
  local sf_count status
  sf_count="$(telegram_bot_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${TELEGRAM_BOT_DIR}" "${TELEGRAM_BOT_ENV}")
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

function get_local_telegram_bot_commit() {
  [[ ! -d ${TELEGRAM_BOT_DIR} || ! -d "${TELEGRAM_BOT_DIR}/.git" ]] && return

  local commit
  cd "${TELEGRAM_BOT_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_telegram_bot_commit() {
  [[ ! -d ${TELEGRAM_BOT_DIR} || ! -d "${TELEGRAM_BOT_DIR}/.git" ]] && return

  local commit
  cd "${TELEGRAM_BOT_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_telegram_bot_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_telegram_bot_commit)"
  remote_ver="$(get_remote_telegram_bot_commit)"

  if [[ ${local_ver} != "${remote_ver}" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "telegram_bot"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function patch_telegram_bot_update_manager() {
  local patched moonraker_configs regex
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  patched="false"
  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager moonraker-telegram-bot\]\s*$" "${conf}"; then
      ### add new line to conf if it doesn't end with one
      [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"

      ### add Moonraker-Telegram-Bot update manager section to moonraker.conf
      status_msg "Adding Moonraker-Telegram-Bot to update manager in file:\n       ${conf}"
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF

[update_manager moonraker-telegram-bot]
type: git_repo
path: ~/moonraker-telegram-bot
origin: https://github.com/nlef/moonraker-telegram-bot.git
env: ~/moonraker-telegram-bot-env/bin/python
requirements: scripts/requirements.txt
install_script: scripts/install.sh
MOONRAKER_CONF

    fi

    patched="true"
  done

  if [[ ${patched} == "true" ]]; then
    do_action_service "restart" "moonraker"
  fi
}
