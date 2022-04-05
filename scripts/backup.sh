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
  if [ ! -d "${BACKUP_DIR}" ]; then
    status_msg "Create KIAUH backup directory ..."
    mkdir -p "${BACKUP_DIR}" && ok_msg "Directory created!"
  fi
}

function toggle_backups(){
  read_kiauh_ini
  if [ "${backup_before_update}" = "true" ]; then
    sed -i '/backup_before_update=/s/true/false/' "${INI_FILE}"
    BB4U_STATUS="${green}[Enable]${white} backups before updating                  "
    CONFIRM_MSG=" Backups before updates are now >>> DISABLED <<< !"
  fi
  if [ "${backup_before_update}" = "false" ]; then
    sed -i '/backup_before_update=/s/false/true/' "${INI_FILE}"
    BB4U_STATUS="${red}[Disable]${white} backups before updating                 "
    CONFIRM_MSG=" Backups before updates are now >>> ENABLED <<< !"
  fi
}

function bb4u(){
  read_kiauh_ini
  if [ "${backup_before_update}" = "true" ]; then
    backup_"${1}"
  fi
}

function read_bb4u_stat(){
  read_kiauh_ini
  if [ ! "${backup_before_update}" = "true" ]; then
    BB4U_STATUS="${green}[Enable]${white} backups before updating                  "
  else
    BB4U_STATUS="${red}[Disable]${white} backups before updating                 "
  fi
}

function backup_printer_cfg(){
  check_for_backup_dir
  if [ -f "${PRINTER_CFG}" ]; then
    get_date
    status_msg "Timestamp: ${current_date}"
    status_msg "Create backup of printer.cfg ..."
    cp "${PRINTER_CFG}" "${BACKUP_DIR}/printer.cfg.${current_date}.backup" && ok_msg "Backup complete!"
  else
    ok_msg "No printer.cfg found! Skipping backup ..."
  fi
}

function backup_klipper_config_dir(){
  check_for_backup_dir
  if [ -d "${KLIPPER_CONFIG}" ]; then
    get_date
    status_msg "Timestamp: ${current_date}"
    status_msg "Create backup of the Klipper config directory ..."
    config_folder_name="$(echo "${KLIPPER_CONFIG}" | rev | cut -d"/" -f1 | rev)"
    mkdir -p "${BACKUP_DIR}/${config_folder_name}/${current_date}"
    cp -r "${KLIPPER_CONFIG}" "${_}" && ok_msg "Backup complete!"
    echo
  else
    ok_msg "No config directory found! Skipping backup ..."
    echo
  fi
}

function backup_moonraker_database(){
  check_for_backup_dir
  if ls -d "${HOME}"/.moonraker_database* 2>/dev/null 1>&2; then
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/mr_db_backup/${current_date}"
    for database in $(ls -d ${HOME}/.moonraker_database*)
    do
      status_msg "Create backup of ${database} ..."
      cp -r "${database}" "${BACKUP_DIR}/mr_db_backup/${current_date}"
      ok_msg "Done!"
    done
    ok_msg "Backup complete!\n"
  else
    ok_msg "No Moonraker database found! Skipping backup ..."
  fi
}

function backup_klipper(){
  if [ -d "${KLIPPER_DIR}" ] && [ -d "${KLIPPY_ENV}" ]; then
    status_msg "Creating Klipper backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipper-backups/${current_date}"
    cp -r "${KLIPPER_DIR}" "${_}" && cp -r "${KLIPPY_ENV}" "${_}" && ok_msg "Backup complete!"
  else
    print_error "Can't backup klipper and/or klipper-env directory! Not found!"
  fi
}

function backup_mainsail(){
  if [ -d "${MAINSAIL_DIR}" ]; then
    status_msg "Creating Mainsail backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/mainsail-backups/${current_date}"
    cp -r "${MAINSAIL_DIR}" "${_}" && ok_msg "Backup complete!"
  else
    print_error "Can't backup mainsail directory! Not found!"
  fi
}

function backup_fluidd(){
  if [ -d "${FLUIDD_DIR}" ]; then
    status_msg "Creating Fluidd backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/fluidd-backups/${current_date}"
    cp -r "${FLUIDD_DIR}" "${_}" && ok_msg "Backup complete!"
  else
    print_error "Can't backup fluidd directory! Not found!"
  fi
}

function backup_moonraker(){
  if [ -d "${MOONRAKER_DIR}" ] && [ -d "${MOONRAKER_ENV}" ]; then
    status_msg "Creating Moonraker backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/moonraker-backups/${current_date}"
    cp -r "${MOONRAKER_DIR}" "${_}" && cp -r "${MOONRAKER_ENV}" "${_}" && ok_msg "Backup complete!"
  else
    print_error "Can't backup moonraker and/or moonraker-env directory! Not found!"
  fi
}

function backup_octoprint(){
  if [ -d "${OCTOPRINT_DIR}" ] && [ -d "${OCTOPRINT_CFG_DIR}" ]; then
    status_msg "Creating OctoPrint backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/octoprint-backups/${current_date}"
    cp -r "${OCTOPRINT_DIR}" "${_}" && cp -r "${OCTOPRINT_CFG_DIR}" "${_}"
    ok_msg "Backup complete!"
  else
    print_error "Can't backup OctoPrint and/or .octoprint directory!\n Not found!"
  fi
}

function backup_klipperscreen(){
  if [ -d "${KLIPPERSCREEN_DIR}" ] ; then
    status_msg "Creating KlipperScreen backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/klipperscreen-backups/${current_date}"
    cp -r "${KLIPPERSCREEN_DIR}" "${_}"
    ok_msg "Backup complete!"
  else
    print_error "Can't backup KlipperScreen directory!\n Not found!"
  fi
}

function backup_MoonrakerTelegramBot(){
  if [ -d "${MOONRAKER_TELEGRAM_BOT_DIR}" ] ; then
    status_msg "Creating MoonrakerTelegramBot backup ..."
    check_for_backup_dir
    get_date
    status_msg "Timestamp: ${current_date}"
    mkdir -p "${BACKUP_DIR}/MoonrakerTelegramBot-backups/${current_date}"
    cp -r "${MOONRAKER_TELEGRAM_BOT_DIR}" "${_}"
    ok_msg "Backup complete!"
  else
    print_error "Can't backup MoonrakerTelegramBot directory!\n Not found!"
  fi
}
