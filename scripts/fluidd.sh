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

### global variables
FLUIDD_DIR="${HOME}/fluidd"
FLUIDD_REPO_API="https://api.github.com/repos/fluidd-core/fluidd/releases"
KLIPPER_CONFIG="$(get_klipper_cfg_dir)"

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

update_fluidd(){
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
  fcount=0
  fluidd_data=(
    $FLUIDD_DIR
    $NGINX_SA/fluidd
    $NGINX_SE/fluidd
  )
  #count+1 for each found data-item from array
  for fd in "${fluidd_data[@]}"
  do
    if [ -e $fd ]; then
      fcount=$(expr $fcount + 1)
    fi
  done
  if [ "$fcount" == "${#fluidd_data[*]}" ]; then
    FLUIDD_STATUS="${green}Installed!${white}      "
  elif [ "$fcount" == 0 ]; then
    FLUIDD_STATUS="${red}Not installed!${white}  "
  else
    FLUIDD_STATUS="${yellow}Incomplete!${white}     "
  fi
}

function read_local_fluidd_version(){
  unset FLUIDD_VER_FOUND
  if [ -e "${FLUIDD_DIR}/.version" ]; then
    FLUIDD_VER_FOUND="true"
    FLUIDD_LOCAL_VER=$(head -n 1 "${FLUIDD_DIR}/.version")
  else
    FLUIDD_VER_FOUND="false" && unset FLUIDD_LOCAL_VER
  fi
}

function read_remote_fluidd_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    FLUIDD_REMOTE_VER=${NONE}
  else
    get_fluidd_ver
    FLUIDD_REMOTE_VER=${FLUIDD_VERSION}
  fi
}

function compare_fluidd_versions(){
  unset FLUIDD_UPDATE_AVAIL
  read_local_fluidd_version && read_remote_fluidd_version
  if [[ $FLUIDD_VER_FOUND = "true" ]] && [[ $FLUIDD_LOCAL_VER == $FLUIDD_REMOTE_VER ]]; then
    #printf fits the string for displaying it in the ui to a total char length of 12
    FLUIDD_LOCAL_VER="${green}$(printf "%-12s" "$FLUIDD_LOCAL_VER")${default}"
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
  elif [[ $FLUIDD_VER_FOUND = "true" ]] && [[ $FLUIDD_LOCAL_VER != $FLUIDD_REMOTE_VER ]]; then
    FLUIDD_LOCAL_VER="${yellow}$(printf "%-12s" "$FLUIDD_LOCAL_VER")${default}"
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
    # add fluidd to the update all array for the update all function in the updater
    FLUIDD_UPDATE_AVAIL="true" && update_arr+=(update_fluidd)
  else
    FLUIDD_LOCAL_VER=$NONE
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
    FLUIDD_UPDATE_AVAIL="false"
  fi
}

#================================================#
#=================== HELPERS ====================#
#================================================#

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