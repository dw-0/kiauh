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
  services=$(find "${SYSTEMD}" -maxdepth 1 -regextype posix-extended -regex "${SYSTEMD}/moonraker-telegram-bot(-[^0])?[0-9]*.service")
  echo "${services}"
}

function install_MoonrakerTelegramBot(){
    MoonrakerTelegramBot_setup
    do_action_service "restart" "moonraker-telegram-bot"
}

function MoonrakerTelegramBot_setup(){
  local klipper_cfg_loc
  klipper_cfg_loc="$(get_klipper_cfg_dir)"
  export klipper_cfg_loc
  local dep=(virtualenv)
  dependency_check "${dep[@]}"
  status_msg "Downloading MoonrakerTelegramBot ..."
  #force remove existing MoonrakerTelegramBot dir 
  [ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] && rm -rf "${MOONRAKER_TELEGRAM_BOT_DIR}"
  #clone into fresh MoonrakerTelegramBot dir
  cd "${HOME}" && git clone "${MOONRAKER_TELEGRAM_BOT_REPO}"
  ok_msg "Download complete!"
  status_msg "Installing MoonrakerTelegramBot ..."
  /bin/bash "${MOONRAKER_TELEGRAM_BOT_DIR}/scripts/install.sh"
  echo; ok_msg "MoonrakerTelegramBot successfully installed!"
}


#===================================================#
#=========== REMOVE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function remove_MoonrakerTelegramBot(){
  ### remove MoonrakerTelegramBot dir
  if [ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ]; then
    status_msg "Removing MoonrakerTelegramBot directory ..."
    rm -rf "${MOONRAKER_TELEGRAM_BOT_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove MoonrakerTelegramBot VENV dir
  if [ -d "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}" ]; then
    status_msg "Removing MoonrakerTelegramBot VENV directory ..."
    rm -rf "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove MoonrakerTelegramBot service
  if [ -e "${SYSTEMD}/moonraker-telegram-bot.service" ]; then
    status_msg "Removing MoonrakerTelegramBot service ..."
    do_action_service "stop" "moonraker-telegram-bot"
    do_action_service "disable" "moonraker-telegram-bot"
    sudo rm -f "${SYSTEMD}/moonraker-telegram-bot.service"
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "MoonrakerTelegramBot Service removed!"
  fi

  ### remove MoonrakerTelegramBot log
  if [ -e "/tmp/telegram.log" ] || [ -e "${HOME}/klipper_logs/telegram.log" ]; then
    status_msg "Removing MoonrakerTelegramBot log file ..."
    rm -f "/tmp/telegram.log" "${HOME}/klipper_logs/telegram.log"  && ok_msg "File removed!"
  fi

  ### remove MoonrakerTelegramBot log symlink in config dir
  if [ -e "${KLIPPER_CONFIG}/telegram.log" ]; then
    status_msg "Removing MoonrakerTelegramBot log symlink ..."
    rm -f "${KLIPPER_CONFIG}/telegram.log" && ok_msg "File removed!"
  fi

  print_confirm "MoonrakerTelegramBot successfully removed!"
}

#===================================================#
#=========== UPDATE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function update_telegram_bot(){
  local klipper_cfg_loc
  klipper_cfg_loc="$(get_klipper_cfg_dir)"
  do_action_service "stop" "moonraker-telegram-bot"
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}" && git pull
  /bin/bash "./scripts/install.sh"
  do_action_service "start" "moonraker-telegram-bot"
  ok_msg "Update complete!"
}

#===================================================#
#=========== MOONRAKERTELEGRAMBOT STATUS ===========#
#===================================================#

function get_telegram_bot_status(){
  local sf_count status
  sf_count="$(telegram_bot_systemd | wc -w)"

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=(SERVICE "${MOONRAKER_TELEGRAM_BOT_DIR}" "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}")
  [ "${sf_count}" -gt 0 ] && unset "data_arr[0]"

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [ -e "${data}" ] && filecount=$(("${filecount}" + 1))
  done

  if [ "${filecount}" == "${#data_arr[*]}" ]; then
    status="$(printf "${green}Installed: %-5s${white}" "${sf_count}")"
  elif [ "${filecount}" == 0 ]; then
    status="${red}Not installed!${white}  "
  else
    status="${yellow}Incomplete!${white}     "
  fi
  echo "${status}"
}

function get_local_telegram_bot_commit(){
  local commit
  [ ! -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] || [ ! -d "${MOONRAKER_TELEGRAM_BOT_DIR}"/.git ] && return
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}"
  commit="$(git describe HEAD --always --tags | cut -d "-" -f 1,2)"
  echo "${commit}"
}

function get_remote_telegram_bot_commit(){
  local commit
  [ ! -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] || [ ! -d "${MOONRAKER_TELEGRAM_BOT_DIR}"/.git ] && return
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}" && git fetch origin -q
  commit=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  echo "${commit}"
}

function compare_telegram_bot_versions(){
  unset MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_telegram_bot_commit)"
  remote_ver="$(get_remote_telegram_bot_commit)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
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
