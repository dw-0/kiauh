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
#================== INSTALL FLUIDD =================#
#===================================================#

function install_fluidd(){
  ### exit early if moonraker not found
  if [ -z "$(moonraker_systemd)" ]; then
    local error="Moonraker service not found!\n Please install Moonraker first!"
    print_error "${error}" && return
  fi
  ### checking dependencies
  local dep=(nginx)
  dependency_check "${dep[@]}"
  ### check if moonraker is already installed
  system_check_webui
  ### ask user how to handle OctoPrint, Haproxy, Lighttpd, Apache2 if found
  process_octoprint_dialog
  process_services_dialog
  ### process possible disruptive services
  process_disruptive_services

  status_msg "Initializing Fluidd installation ..."
  ### check for other enabled web interfaces
  unset SET_LISTEN_PORT
  detect_enabled_sites

  ### check if another site already listens to port 80
  fluidd_port_check

  ### ask user to install mjpg-streamer
  if ! ls /etc/systemd/system/webcamd.service 2>/dev/null 1>&2; then
    get_user_selection_mjpg-streamer
  fi

  ### ask user to install the recommended webinterface macros
  if ! ls "${KLIPPER_CONFIG}/kiauh_macros.cfg" 2>/dev/null 1>&2 || ! ls "${KLIPPER_CONFIG}"/printer_*/kiauh_macros.cfg 2>/dev/null 1>&2; then
    get_user_selection_kiauh_macros "Fluidd       "
  fi
  ### create /etc/nginx/conf.d/upstreams.conf
  set_upstream_nginx_cfg
  ### create /etc/nginx/sites-available/<interface config>
  set_nginx_cfg "fluidd"

  ### symlink nginx log
  symlink_webui_nginx_log "fluidd"

  ### copy the kiauh_macros.cfg to the config location
  install_kiauh_macros

  ### install mainsail/fluidd
  fluidd_setup

  ### install mjpg-streamer
  [ "${INSTALL_MJPG}" = "true" ] && install_mjpg-streamer

  fetch_webui_ports #WIP

  ### confirm message
  print_confirm "Fluidd has been set up!"
}

function fluidd_setup(){
  ### get fluidd download url
  FLUIDD_DL_URL=$(curl -s "${FLUIDD_REPO_API}" | grep browser_download_url | cut -d'"' -f4 | head -1)

  ### remove existing and create fresh fluidd folder, then download fluidd
  [ -d "${FLUIDD_DIR}" ] && rm -rf "${FLUIDD_DIR}"
  mkdir "${FLUIDD_DIR}" && cd "${FLUIDD_DIR}"
  status_msg "Downloading Fluidd ${FLUIDD_VERSION} ..."
  wget "${FLUIDD_DL_URL}" && ok_msg "Download complete!"

  ### extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"

  ### delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!"
}

#===================================================#
#================== REMOVE FLUIDD ==================#
#===================================================#

function remove_fluidd(){
  ### remove fluidd dir
  if [ -d "${FLUIDD_DIR}" ]; then
    status_msg "Removing Fluidd directory ..."
    rm -rf "${FLUIDD_DIR}" && ok_msg "Directory removed!"
  fi

  ### remove fluidd config for nginx
  if [ -e "/etc/nginx/sites-available/fluidd" ]; then
    status_msg "Removing Fluidd configuration for Nginx ..."
    sudo rm "/etc/nginx/sites-available/fluidd" && ok_msg "File removed!"
  fi

  ### remove fluidd symlink for nginx
  if [ -L /etc/nginx/sites-enabled/fluidd ]; then
    status_msg "Removing Fluidd Symlink for Nginx ..."
    sudo rm /etc/nginx/sites-enabled/fluidd && ok_msg "File removed!"
  fi

  ### remove mainsail nginx logs and log symlinks
  for log in $(find /var/log/nginx -name "fluidd*"); do
    sudo rm -f "${log}"
  done
  for log in $(find ${HOME}/klipper_logs -name "fluidd*"); do
    rm -f "${log}"
  done

  ### remove fluidd_port from ~/.kiauh.ini
  sed -i "/^fluidd_port=/d" "${INI_FILE}"

  print_confirm "Fluidd successfully removed!"
}

#===================================================#
#================== UPDATE FLUIDD ==================#
#===================================================#

function update_fluidd(){
  bb4u "fluidd"
  status_msg "Updating Fluidd ..."
  fluidd_setup
  match_nginx_configs
  symlink_webui_nginx_log "fluidd"
}

#===================================================#
#================== FLUIDD STATUS ==================#
#===================================================#

function get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s "${FLUIDD_REPO_API}" | grep tag_name | cut -d'"' -f4 | head -1)
}

function fluidd_status(){
  local status

  ### remove the "SERVICE" entry from the data array if a moonraker service is installed
  local data_arr=("${FLUIDD_DIR}" "${NGINX_SA}/fluidd" "${NGINX_SE}/fluidd")

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [ -e "${data}" ] && filecount=$(("${filecount}" + 1))
  done

  if [ "${filecount}" == "${#data_arr[*]}" ]; then
    status="${green}Installed!${white}      "
  elif [ "${filecount}" == 0 ]; then
    status="${red}Not installed!${white}  "
  else
    status="${yellow}Incomplete!${white}     "
  fi
  echo "${status}"
}

function get_local_fluidd_version(){
  local version
  [ ! -f "${FLUIDD_DIR}/.version" ] && return
  version=$(head -n 1 "${FLUIDD_DIR}/.version")
  echo "${version}"
}

function get_remote_fluidd_version(){
  local version
  [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]] && return
  version=$(get_fluidd_download_url | rev | cut -d"/" -f2 | rev)
  echo "${version}"
}

function compare_fluidd_versions(){
  unset FLUIDD_UPDATE_AVAIL
  local versions local_ver remote_ver
  local_ver="$(get_local_fluidd_version)"
  remote_ver="$(get_remote_fluidd_version)"
  if [ "${local_ver}" != "${remote_ver}" ]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add fluidd to the update all array for the update all function in the updater
    FLUIDD_UPDATE_AVAIL="true" && update_arr+=(update_fluidd)
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    FLUIDD_UPDATE_AVAIL="false"
  fi
  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function get_fluidd_download_url() {
  local latest_tag latest_url stable_tag stable_url url
  tags=$(curl -s "${FLUIDD_TAGS}" | grep "name" | cut -d'"' -f4)

  ### latest download url including pre-releases (alpha, beta, rc)
  latest_tag=$(echo "${tags}" | head -1)
  latest_url="https://github.com/fluidd-core/fluidd/releases/download/${latest_tag}/fluidd.zip"

  ### get stable fluidd download url
  stable_tag=$(echo "${tags}" | grep -E "^v([0-9]+\.?){3}$" | head -1)
  stable_url="https://github.com/fluidd-core/fluidd/releases/download/${stable_tag}/fluidd.zip"

  read_kiauh_ini
  if [ "${fluidd_install_unstable}" == "true" ]; then
    url="${latest_url}"
    echo "${url}"
  else
    url="${stable_url}"
    echo "${url}"
  fi
}

function fluidd_port_check(){
  if [ "${FLUIDD_ENABLED}" = "false" ]; then
    if [ "${SITE_ENABLED}" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "${OCTOPRINT_ENABLED}" = "true" ] && echo "   ${cyan}● OctoPrint - Port: ${OCTOPRINT_PORT}${default}"
      [ "${MAINSAIL_ENABLED}" = "true" ] && echo "   ${cyan}● Mainsail - Port: ${MAINSAIL_PORT}${default}"
      if [ "${MAINSAIL_PORT}" = "80" ] || [ "${OCTOPRINT_PORT}" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_fluidd_port
      fi
    else
      DEFAULT_PORT=$(grep listen "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=${DEFAULT_PORT}
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

function select_fluidd_port(){
  if [ "${PORT_80_BLOCKED}" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for Fluidd!${default}       |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "${OCTOPRINT_PORT}" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "${MAINSAIL_PORT}" = "80" ] && echo "|  ● Mainsail                                           |"
    blank_line
    echo -e "| Make sure you don't choose a port which was already   |"
    echo -e "| assigned to one of the other webinterfaces and do ${red}NOT${default} |"
    echo -e "| use ports in the range of 4750 or above!              |"
    blank_line
    echo -e "| Be aware: there is ${red}NO${default} sanity check for the following  |"
    echo -e "| input. So make sure to choose a valid port!           |"
    bottom_border
    while true; do
      read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
      if [ "${NEW_PORT}" != "${MAINSAIL_PORT}" ] && [ "${NEW_PORT}" != "${OCTOPRINT_PORT}" ]; then
        echo "Setting port ${NEW_PORT} for Fluidd!"
        SET_LISTEN_PORT=${NEW_PORT}
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}