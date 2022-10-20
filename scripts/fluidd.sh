#!/usr/bin/env bash

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

function install_fluidd() {
  ### exit early if moonraker not found
  if [[ -z $(moonraker_systemd) ]]; then
    local error="Moonraker not installed! Please install Moonraker first!"
    print_error "${error}" && return
  fi

  ### checking dependencies
  local dep=(wget nginx)
  dependency_check "${dep[@]}"
  ### detect conflicting Haproxy and Apache2 installations
  detect_conflicting_packages

  status_msg "Initializing Fluidd installation ..."
  ### first, we create a backup of the full klipper_config dir - safety first!
  backup_klipper_config_dir

  ### check for other enabled web interfaces
  unset SET_LISTEN_PORT
  detect_enabled_sites

  ### check if another site already listens to port 80
  fluidd_port_check

#  ### ask user to install mjpg-streamer
#  local install_mjpg_streamer
#  if [[ ! -f "${SYSTEMD}/webcamd.service" ]]; then
#    while true; do
#      echo
#      top_border
#      echo -e "| Install MJPG-Streamer for webcam support?             |"
#      bottom_border
#      read -p "${cyan}###### Please select (y/N):${white} " yn
#      case "${yn}" in
#        Y|y|Yes|yes)
#          select_msg "Yes"
#          install_mjpg_streamer="true"
#          break;;
#        N|n|No|no|"")
#          select_msg "No"
#          install_mjpg_streamer="false"
#          break;;
#        *)
#          error_msg "Invalid command!";;
#      esac
#    done
#  fi

  ### download fluidd
  download_fluidd

  ### ask user to install the recommended webinterface macros
  install_fluidd_macros

  ### create /etc/nginx/conf.d/upstreams.conf
  set_upstream_nginx_cfg
  ### create /etc/nginx/sites-available/<interface config>
  set_nginx_cfg "fluidd"
  ### nginx on ubuntu 21 and above needs special permissions to access the files
  set_nginx_permissions

  ### symlink nginx log
  symlink_webui_nginx_log "fluidd"

  ### add fluidd to the update manager in moonraker.conf
  patch_fluidd_update_manager

  ### install mjpg-streamer
#  [[ ${install_mjpg_streamer} == "true" ]] && install_mjpg-streamer

  fetch_webui_ports #WIP

  ### confirm message
  print_confirm "Fluidd has been set up!"
}

function install_fluidd_macros() {
  while true; do
    echo
    top_border
    echo -e "| It is recommended to have some important macros in    |"
    echo -e "| your printer configuration to have Fluidd fully       |"
    echo -e "| functional and working.                               |"
    blank_line
    echo -e "| The recommended macros for Fluidd can be found here:  |"
    echo -e "| https://docs.fluidd.xyz/configuration/initial_setup   |"
    blank_line
    echo -e "| If you already have these macros in your config file, |"
    echo -e "| skip this step and answer with 'no'.                  |"
    echo -e "| Otherwise you should consider to answer with 'yes' to |"
    echo -e "| add the recommended example macros to your config.    |"
    bottom_border
    read -p "${cyan}###### Add the recommended macros? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        select_msg "Yes"
        download_fluidd_macros
        break;;
      N|n|No|no)
        select_msg "No"
        break;;
      *)
        print_error "Invalid command!";;
    esac
  done
  return
}

function download_fluidd_macros() {
  local fluidd_cfg path configs regex

  fluidd_cfg="https://raw.githubusercontent.com/fluidd-core/FluiddPI/master/src/modules/fluidd/filesystem/home/pi/klipper_config/fluidd.cfg"
  regex="\/home\/${USER}\/([A-Za-z0-9_]+)\/config\/printer\.cfg"
  configs=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -n ${configs} ]]; then
    for config in ${configs}; do
      path=$(echo "${config}" | rev | cut -d"/" -f2- | rev)
      if [[ ! -f "${path}/fluidd.cfg" ]]; then
        status_msg "Downloading fluidd.cfg to ${path} ..."
        log_info "downloading fluidd.cfg to: ${path}"
        wget "${fluidd_cfg}" -O "${path}/fluidd.cfg"

        ### replace user 'pi' with current username to prevent issues in cases where the user is not called 'pi'
        log_info "modify fluidd.cfg"
        sed -i "/^path: \/home\/pi\/gcode_files/ s/\/home\/pi/\/home\/${USER}/" "${path}/fluidd.cfg"

        ### write include to the very first line of the printer.cfg
        if ! grep -Eq "^[include fluidd.cfg]$" "${path}/printer.cfg"; then
          log_info "modify printer.cfg"
          sed -i "1 i [include fluidd.cfg]" "${path}/printer.cfg"
        fi
        ok_msg "Done!"
      fi
    done
  else
    log_error "execution stopped! reason: no printer.cfg found"
    return
  fi
}

function download_fluidd() {
  local url
  url=$(get_fluidd_download_url)

  status_msg "Downloading Fluidd from ${url} ..."

  if [[ -d ${FLUIDD_DIR} ]]; then
    rm -rf "${FLUIDD_DIR}"
  fi

  mkdir "${FLUIDD_DIR}" && cd "${FLUIDD_DIR}"

  if wget "${url}"; then
    ok_msg "Download complete!"
    status_msg "Extracting archive ..."
    unzip -q -o ./*.zip && ok_msg "Done!"
    status_msg "Remove downloaded archive ..."
    rm -rf ./*.zip && ok_msg "Done!"
  else
    print_error "Downloading Fluidd from\n ${url}\n failed!"
    exit 1
  fi
}

#===================================================#
#================== REMOVE FLUIDD ==================#
#===================================================#

function remove_fluidd_dir() {
  [[ ! -d ${FLUIDD_DIR} ]] && return

  status_msg "Removing Fluidd directory ..."
  rm -rf "${FLUIDD_DIR}" && ok_msg "Directory removed!"
}

function remove_fluidd_config() {
  if [[ -e "/etc/nginx/sites-available/fluidd" ]]; then
    status_msg "Removing Fluidd configuration for Nginx ..."
    sudo rm "/etc/nginx/sites-available/fluidd" && ok_msg "File removed!"
  fi
  if [[ -L "/etc/nginx/sites-enabled/fluidd" ]]; then
    status_msg "Removing Fluidd Symlink for Nginx ..."
    sudo rm "/etc/nginx/sites-enabled/fluidd" && ok_msg "File removed!"
  fi
}

function remove_fluidd_logs() {
  local files
  files=$(find /var/log/nginx -name "fluidd*" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      sudo rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_fluidd_log_symlinks() {
  local files regex

  regex="\/home\/${USER}\/([A-Za-z0-9_]+)\/logs\/fluidd-.*"
  files=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_legacy_fluidd_log_symlinks() {
  local files
  files=$(find "${HOME}/klipper_logs" -name "fluidd*" 2> /dev/null | sort)

  if [[ -n ${files} ]]; then
    for file in ${files}; do
      status_msg "Removing ${file} ..."
      rm -f "${file}"
      ok_msg "${file} removed!"
    done
  fi
}

function remove_fluidd() {
  remove_fluidd_dir
  remove_fluidd_config
  remove_fluidd_logs
  remove_fluidd_log_symlinks
  remove_legacy_fluidd_log_symlinks

  ### remove fluidd_port from ~/.kiauh.ini
  sed -i "/^fluidd_port=/d" "${INI_FILE}"

  print_confirm "Fluidd successfully removed!"
}

#===================================================#
#================== UPDATE FLUIDD ==================#
#===================================================#

function update_fluidd() {
  backup_before_update "fluidd"
  status_msg "Updating Fluidd ..."
  download_fluidd
  match_nginx_configs
  symlink_webui_nginx_log "fluidd"
  print_confirm "Fluidd successfully updated!"
}

#===================================================#
#================== FLUIDD STATUS ==================#
#===================================================#

function get_fluidd_status() {
  local status
  local data_arr=("${FLUIDD_DIR}" "${NGINX_SA}/fluidd" "${NGINX_SE}/fluidd")

  ### count+1 for each found data-item from array
  local filecount=0
  for data in "${data_arr[@]}"; do
    [[ -e ${data} ]] && filecount=$(( filecount + 1 ))
  done

  if (( filecount == ${#data_arr[*]} )); then
    status="Installed!"
  elif (( filecount == 0 )); then
    status="Not installed!"
  else
    status="Incomplete!"
  fi
  echo "${status}"
}

function get_local_fluidd_version() {
  [[ ! -f "${FLUIDD_DIR}/.version" ]] && return

  local version
  version=$(head -n 1 "${FLUIDD_DIR}/.version")
  echo "${version}"
}

function get_remote_fluidd_version() {
  [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]] && return

  local version
  version=$(get_fluidd_download_url | rev | cut -d"/" -f2 | rev)
  echo "${version}"
}

function compare_fluidd_versions() {
  local versions local_ver remote_ver
  local_ver="$(get_local_fluidd_version)"
  remote_ver="$(get_remote_fluidd_version)"

  if [[ ${local_ver} != "${remote_ver}" && ${local_ver} != "" ]]; then
    versions="${yellow}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
    # add moonraker to application_updates_available in kiauh.ini
    add_to_application_updates "fluidd"
  else
    versions="${green}$(printf " %-14s" "${local_ver}")${white}"
    versions+="|${green}$(printf " %-13s" "${remote_ver}")${white}"
  fi

  echo "${versions}"
}

#================================================#
#=================== HELPERS ====================#
#================================================#

function get_fluidd_download_url() {
  local tags latest_tag latest_url stable_tag stable_url url
  tags=$(curl -s "${FLUIDD_TAGS}" | grep "name" | cut -d'"' -f4)

  ### latest download url including pre-releases (alpha, beta, rc)
  latest_tag=$(echo "${tags}" | head -1)
  latest_url="https://github.com/fluidd-core/fluidd/releases/download/${latest_tag}/fluidd.zip"

  ### get stable fluidd download url
  stable_tag=$(echo "${tags}" | grep -E "^v([0-9]+\.?){3}$" | head -1)
  stable_url="https://github.com/fluidd-core/fluidd/releases/download/${stable_tag}/fluidd.zip"

  read_kiauh_ini "${FUNCNAME[0]}"
  if [[ ${fluidd_install_unstable} == "true" ]]; then
    url="${latest_url}"
    echo "${url}"
  else
    url="${stable_url}"
    echo "${url}"
  fi
}

function fluidd_port_check() {
  if [[ ${FLUIDD_ENABLED} == "false" ]]; then

    if [[ ${SITE_ENABLED} == "true" ]]; then
      status_msg "Detected other enabled interfaces:"

      [[ ${MAINSAIL_ENABLED} == "true" ]] && \
      echo "   ${cyan}● Mainsail - Port: ${MAINSAIL_PORT}${white}"

      if [[ ${MAINSAIL_PORT} == "80" ]]; then
        PORT_80_BLOCKED="true"
        select_fluidd_port
      fi
    else
      DEFAULT_PORT=$(grep listen "${KIAUH_SRCDIR}/resources/fluidd" | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=${DEFAULT_PORT}
    fi
    SET_NGINX_CFG="true"

  else
    SET_NGINX_CFG="false"
  fi
}

function select_fluidd_port() {
  if [[ ${PORT_80_BLOCKED} == "true" ]]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${white}                      |"
    echo -e "| ${red}You need to choose a different port for Fluidd!${white}       |"
    echo -e "| ${red}The following web interface is listening at port 80:${white}  |"
    blank_line
    [[ ${MAINSAIL_PORT} == "80" ]] && echo "|  ● Mainsail                                           |"
    blank_line
    echo -e "| Make sure you don't choose a port which is already    |"
    echo -e "| assigned to another webinterface!                     |"
    blank_line
    echo -e "| Be aware: there is ${red}NO${white} sanity check for the following  |"
    echo -e "| input. So make sure to choose a valid port!           |"
    bottom_border

    local new_port re="^[0-9]+$"
    while true; do
      read -p "${cyan}Please enter a new Port:${white} " new_port
      if [[ ${new_port} =~ ${re} && ${new_port} != "${MAINSAIL_PORT}" ]]; then
        select_msg "Setting port ${new_port} for Fluidd!"
        SET_LISTEN_PORT=${new_port}
        break
      else
        if [[ ! ${new_port} =~ ${re}  ]]; then
          error_msg "Invalid input!"
        else
          error_msg "Port already taken! Select a different one!"
        fi
      fi
    done
  fi
}

function patch_fluidd_update_manager() {
  local patched moonraker_configs regex
  regex="\/home\/${USER}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  patched="false"
  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager fluidd\]$" "${conf}"; then
      ### add new line to conf if it doesn't end with one
      [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"

      ### add Fluidds update manager section to moonraker.conf
      status_msg "Adding Fluidd to update manager in file:\n       ${conf}"
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF

[update_manager fluidd]
type: web
channel: stable
repo: fluidd-core/fluidd
path: ~/fluidd
MOONRAKER_CONF

    fi

    patched="true"
  done

  if [[ ${patched} == "true" ]]; then
    do_action_service "restart" "moonraker"
  fi
}
