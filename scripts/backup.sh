#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

function get_date() {
  local current_date
  current_date=$(date +"%y%m%d-%H%M")
  echo "${current_date}"
}

function check_for_backup_dir() {
  [[ -d ${BACKUP_DIR} ]] && return

  status_msg "Create KIAUH backup directory ..."
  mkdir -p "${BACKUP_DIR}" && ok_msg "Directory created!"
}

function backup_before_update() {
  read_kiauh_ini "${FUNCNAME[0]}"
  local state="${backup_before_update}"
  [[ ${state} = "false" ]] && return
  backup_"${1}"
}

function backup_config_dir() {
  check_for_backup_dir
  local current_date config_pathes

  config_pathes=$(get_config_folders)

  if [[ -n "${config_pathes}" ]]; then
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"

    local i=0 folder folder_name target_dir
    for folder in ${config_pathes}; do
      if [[ -d ${folder} ]]; then
        status_msg "Create backup of ${folder} ..."
  
        folder_name=$(echo "${folder}" | rev | cut -d"/" -f2 | rev)
        target_dir="${BACKUP_DIR}/configs/${current_date}/${folder_name}"
        mkdir -p "${target_dir}"
        cp -r "${folder}" "${target_dir}"
        i=$(( i + 1 ))
  
        ok_msg "Backup created in:\n${target_dir}"
      fi
    done
  else
    ok_msg "No config directory found! Skipping backup ..."
  fi
}

function backup_moonraker_database() {
  check_for_backup_dir
  local current_date db_pathes

  db_pathes=$(get_instance_folder_path "database")

  if [[ -n ${db_pathes} ]]; then
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"

    local i=0 database folder_name target_dir
    for database in ${db_pathes}; do
      status_msg "Create backup of ${database} ..."

      folder_name=$(echo "${database}" | rev | cut -d"/" -f2 | rev)
      target_dir="${BACKUP_DIR}/moonraker_databases/${current_date}/${folder_name}"
      mkdir -p "${target_dir}"
      cp -r "${database}" "${target_dir}"
      i=$(( i + 1 ))

      ok_msg "Backup created in:\n${target_dir}"
    done
  else
    print_error "No Moonraker database found! Skipping backup ..."
  fi
}

function backup_klipper() {
  local current_date

  if [[ -d ${KLIPPER_DIR} && -d ${KLIPPY_ENV} ]]; then
    status_msg "Creating Klipper backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipper-backups/${current_date}"
    cp -r "${KLIPPER_DIR}" "${_}" && cp -r "${KLIPPY_ENV}" "${_}"
    print_confirm "Klipper backup complete!"
  else
    print_error "Can't back up 'klipper' and/or 'klipper-env' directory! Not found!"
  fi
}

function backup_mainsail() {
  local current_date

  if [[ -d ${MAINSAIL_DIR} ]]; then
    status_msg "Creating Mainsail backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/mainsail-backups/${current_date}"
    cp -r "${MAINSAIL_DIR}" "${_}"
    print_confirm "Mainsail backup complete!"
  else
    print_error "Can't back up 'mainsail' directory! Not found!"
  fi
}

function backup_fluidd() {
  local current_date

  if [[ -d ${FLUIDD_DIR} ]]; then
    status_msg "Creating Fluidd backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/fluidd-backups/${current_date}"
    cp -r "${FLUIDD_DIR}" "${_}"
    print_confirm "Fluidd backup complete!"
  else
    print_error "Can't back up 'fluidd' directory! Not found!"
  fi
}

function backup_moonraker() {
  local current_date

  if [[ -d ${MOONRAKER_DIR} && -d ${MOONRAKER_ENV} ]]; then
    status_msg "Creating Moonraker backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/moonraker-backups/${current_date}"
    cp -r "${MOONRAKER_DIR}" "${_}" && cp -r "${MOONRAKER_ENV}" "${_}"
    print_confirm "Moonraker backup complete!"
  else
    print_error "Can't back up moonraker and/or moonraker-env directory! Not found!"
  fi
}

function backup_octoprint() {
  local current_date

  if [[ -d ${OCTOPRINT_DIR} && -d ${OCTOPRINT_CFG_DIR} ]]; then
    status_msg "Creating OctoPrint backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/octoprint-backups/${current_date}"
    cp -r "${OCTOPRINT_DIR}" "${_}" && cp -r "${OCTOPRINT_CFG_DIR}" "${_}"
    print_confirm " OctoPrint backup complete!"
  else
    print_error "Can't back up OctoPrint and/or .octoprint directory!\n Not found!"
  fi
}

function backup_klipperscreen() {
  local current_date
  if [[ -d ${KLIPPERSCREEN_DIR} ]] ; then
    status_msg "Creating KlipperScreen backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipperscreen-backups/${current_date}"
    cp -r "${KLIPPERSCREEN_DIR}" "${_}"
    print_confirm "KlipperScreen backup complete!"
  else
    print_error "Can't back up KlipperScreen directory!\n Not found!"
  fi
}

function backup_telegram_bot() {
  local current_date

  if [[ -d ${TELEGRAM_BOT_DIR} ]] ; then
    status_msg "Creating MoonrakerTelegramBot backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/MoonrakerTelegramBot-backups/${current_date}"
    cp -r "${TELEGRAM_BOT_DIR}" "${_}"
    print_confirm "MoonrakerTelegramBot backup complete!"
  else
    print_error "Can't back up MoonrakerTelegramBot directory!\n Not found!"
  fi
}

function backup_octoeverywhere() {
  local current_date

  if [[ -d ${OCTOEVERYWHERE_DIR} ]] ; then
    status_msg "Creating OctoEverywhere backup ..."
    check_for_backup_dir
    current_date=$(get_date)
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/OctoEverywhere-backups/${current_date}"
    cp -r "${OCTOEVERYWHERE_DIR}" "${_}" && cp -r "${OCTOEVERYWHERE_ENV}" "${_}"
    print_confirm "OctoEverywhere backup complete!"
  else
    print_error "Can't back up OctoEverywhere directory!\n Not found!"
  fi
}
