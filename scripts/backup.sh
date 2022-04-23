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

function get_date(){
  current_date=$(date +"%y%m%d-%H%M")
  echo "${current_date}"
}

function check_for_backup_dir(){
  [ -d "${BACKUP_DIR}" ] && return
  status_msg "Create KIAUH backup directory ..."
  mkdir -p "${BACKUP_DIR}" && ok_msg "Directory created!"
}

function backup_before_update(){
  read_kiauh_ini
  # shellcheck disable=SC2154
  local state="${backup_before_update}"
  [ "${state}" = "false" ] && return
  backup_"${1}"
}

function backup_printer_cfg(){
  check_for_backup_dir
  local current_date
  if [ -f "${PRINTER_CFG}" ]; then
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    status_msg "Create backup of printer.cfg ..."
    cp "${PRINTER_CFG}" "${BACKUP_DIR}/printer.cfg.${current_date}.backup" && ok_msg "Backup complete!"
  else
    ok_msg "No printer.cfg found! Skipping backup ..."
  fi
}

function backup_klipper_config_dir(){
  check_for_backup_dir
  local current_date
  if [ -d "${KLIPPER_CONFIG}" ]; then
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    status_msg "Create backup of the Klipper config directory ..."
    config_folder_name="$(echo "${KLIPPER_CONFIG}" | rev | cut -d"/" -f1 | rev)"
    mkdir -p "${BACKUP_DIR}/${config_folder_name}/${current_date}"
    cp -r "${KLIPPER_CONFIG}" "${_}"
    print_confirm "Configuration directory backup complete!"
  else
    ok_msg "No config directory found! Skipping backup ..."
  fi
}

function backup_moonraker_database(){
  check_for_backup_dir
  local current_date databases target_dir

  databases=$(find "${HOME}" -maxdepth 1 -type d -regextype posix-extended -regex "${HOME}/.moonraker_database(_[^0])?[0-9]*" | sort)
  if [ -n "${databases}" ]; then
    current_date=$(get_date)
    target_dir="${BACKUP_DIR}/moonraker_database_backup/${current_date}"
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${target_dir}"
    for database in ${databases}; do
      status_msg "Create backup of ${database} ..."
      cp -r "${database}" "${target_dir}"
      ok_msg "Done!"
    done
    print_confirm "Moonraker database backup complete!"
  else
    print_error "No Moonraker database found! Skipping backup ..."
  fi
  return
}

function backup_klipper(){
  local current_date
  if [ -d "${KLIPPER_DIR}" ] && [ -d "${KLIPPY_ENV}" ]; then
    status_msg "Creating Klipper backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipper-backups/${current_date}"
    cp -r "${KLIPPER_DIR}" "${_}" && cp -r "${KLIPPY_ENV}" "${_}"
    print_confirm "Klipper backup complete!"
  else
    print_error "Can't backup klipper and/or klipper-env directory! Not found!"
  fi
}

function backup_mainsail(){
  local current_date
  if [ -d "${MAINSAIL_DIR}" ]; then
    status_msg "Creating Mainsail backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/mainsail-backups/${current_date}"
    cp -r "${MAINSAIL_DIR}" "${_}"
    print_confirm "Mainsail backup complete!"
  else
    print_error "Can't backup mainsail directory! Not found!"
  fi
}

function backup_fluidd(){
  local current_date
  if [ -d "${FLUIDD_DIR}" ]; then
    status_msg "Creating Fluidd backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/fluidd-backups/${current_date}"
    cp -r "${FLUIDD_DIR}" "${_}"
    print_confirm "Fluidd backup complete!"
  else
    print_error "Can't backup fluidd directory! Not found!"
  fi
}

function backup_moonraker(){
  local current_date
  if [ -d "${MOONRAKER_DIR}" ] && [ -d "${MOONRAKER_ENV}" ]; then
    status_msg "Creating Moonraker backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/moonraker-backups/${current_date}"
    cp -r "${MOONRAKER_DIR}" "${_}" && cp -r "${MOONRAKER_ENV}" "${_}"
    print_confirm "Moonraker backup complete!"
  else
    print_error "Can't backup moonraker and/or moonraker-env directory! Not found!"
  fi
}

function backup_octoprint(){
  local current_date
  if [ -d "${OCTOPRINT_DIR}" ] && [ -d "${OCTOPRINT_CFG_DIR}" ]; then
    status_msg "Creating OctoPrint backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/octoprint-backups/${current_date}"
    cp -r "${OCTOPRINT_DIR}" "${_}" && cp -r "${OCTOPRINT_CFG_DIR}" "${_}"
    print_confirm " OctoPrint backup complete!"
  else
    print_error "Can't backup OctoPrint and/or .octoprint directory!\n Not found!"
  fi
}

function backup_klipperscreen(){
  local current_date
  if [ -d "${KLIPPERSCREEN_DIR}" ] ; then
    status_msg "Creating KlipperScreen backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipperscreen-backups/${current_date}"
    cp -r "${KLIPPERSCREEN_DIR}" "${_}"
    print_confirm "KlipperScreen backup complete!"
  else
    print_error "Can't backup KlipperScreen directory!\n Not found!"
  fi
}

function backup_telegram_bot(){
  local current_date
  if [ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] ; then
    status_msg "Creating MoonrakerTelegramBot backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/MoonrakerTelegramBot-backups/${current_date}"
    cp -r "${MOONRAKER_TELEGRAM_BOT_DIR}" "${_}"
    print_confirm "MoonrakerTelegramBot backup complete!"
  else
    print_error "Can't backup MoonrakerTelegramBot directory!\n Not found!"
  fi
}
