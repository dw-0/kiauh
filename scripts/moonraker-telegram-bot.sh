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
#=========== REMOVE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function install_MoonrakerTelegramBot(){
    MoonrakerTelegramBot_setup
    restart_MoonrakerTelegramBot
}

function MoonrakerTelegramBot_setup(){
  source_kiauh_ini
  export klipper_cfg_loc
  dep=(virtualenv)
  dependency_check
  status_msg "Downloading MoonrakerTelegramBot ..."
  #force remove existing MoonrakerTelegramBot dir 
  [ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] && rm -rf "${MOONRAKER_TELEGRAM_BOT_DIR}"
  #clone into fresh MoonrakerTelegramBot dir
  cd "${HOME}" && git clone "${NLEF_REPO}"
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
    sudo systemctl stop moonraker-telegram-bot
    sudo systemctl disable moonraker-telegram-bot
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

  CONFIRM_MSG="MoonrakerTelegramBot successfully removed!"
}

#===================================================#
#=========== UPDATE MOONRAKERTELEGRAMBOT ===========#
#===================================================#

function update_MoonrakerTelegramBot(){
  export KLIPPER_CONFIG
  stop_MoonrakerTelegramBot
  cd "${MOONRAKER_TELEGRAM_BOT_DIR}"
  git pull
  /bin/bash "./scripts/install.sh"
  ok_msg "Update complete!"
  start_MoonrakerTelegramBot
}

#===================================================#
#=========== MOONRAKERTELEGRAMBOT STATUS ===========#
#===================================================#

function MoonrakerTelegramBot_status(){
  mtbcount=0
  MoonrakerTelegramBot_data=(
    SERVICE
    "${MOONRAKER_TELEGRAM_BOT_DIR}"
    "${MOONRAKER_TELEGRAM_BOT_ENV_DIR}"
  )

  ### count amount of MoonrakerTelegramBot_data service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "moonraker-telegram-bot" | wc -l)

  ### remove the "SERVICE" entry from the MoonrakerTelegramBot_data array if a MoonrakerTelegramBot service is installed
  [ "${SERVICE_FILE_COUNT}" -gt 0 ] && unset "MoonrakerTelegramBot_data[0]"

  #count+1 for each found data-item from array
  for mtbd in "${MoonrakerTelegramBot_data[@]}"
  do
    if [ -e "${mtbd}" ]; then
      mtbcount=$((mtbcount + 1))
    fi
  done
  if [ "${mtbcount}" == "${#MoonrakerTelegramBot_data[*]}" ]; then
    MOONRAKER_TELEGRAM_BOT_STATUS="${green}Installed!${white}      "
  elif [ "${mtbcount}" == 0 ]; then
    MOONRAKER_TELEGRAM_BOT_STATUS="${red}Not installed!${white}  "
  else
    MOONRAKER_TELEGRAM_BOT_STATUS="${yellow}Incomplete!${white}     "
  fi
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

function compare_prettygcode_versions(){
  unset MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_telegram_bot_commit)"
  remote_ver="$(get_remote_telegram_bot_commit)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker-telegram-bot to the update all array for the update all function in the updater
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="true" && update_arr+=(update_MoonrakerTelegramBot)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}
