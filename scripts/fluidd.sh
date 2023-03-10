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

  fetch_webui_ports #WIP

  ### confirm message
  print_confirm "Fluidd has been set up!"
}

function install_fluidd_macros() {
  local yn
  while true; do
    echo
    top_border
    echo -e "| It is recommended to use special macros in order to   |"
    echo -e "| have Fluidd fully functional and working.             |"
    blank_line
    echo -e "| The recommended macros for Fluidd can be found here:  |"
    echo -e "| https://github.com/fluidd-core/fluidd-config           |"
    blank_line
    echo -e "| If you already use these macros skip this step.       |"
    echo -e "| Otherwise you should consider to answer with 'yes' to |"
    echo -e "| download the recommended macros.                      |"
    bottom_border
    read -p "${cyan}###### Download the recommended macros? (Y/n):${white} " yn
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
  local ms_cfg_repo path configs regex line gcode_dir

  ms_cfg_repo="https://github.com/fluidd-core/fluidd-config.git"
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/printer\.cfg"
  configs=$(find "${HOME}" -maxdepth 3 -regextype posix-extended -regex "${regex}" | sort)

  if [[ -z ${configs} ]]; then
    print_error "No printer.cfg found! Installation of Macros will be skipped ..."
    log_error "execution stopped! reason: no printer.cfg found"
    return
  fi

  status_msg "Cloning fluidd-config ..."
  [[ -d "${HOME}/fluidd-config" ]] && rm -rf "${HOME}/fluidd-config"
  if git clone --recurse-submodules "${ms_cfg_repo}" "${HOME}/fluidd-config"; then
    for config in ${configs}; do
      path=$(echo "${config}" | rev | cut -d"/" -f2- | rev)

      if [[ -e "${path}/fluidd.cfg" && ! -h "${path}/fluidd.cfg" ]]; then
        warn_msg "Attention! Existing fluidd.cfg detected!"
        warn_msg "The file will be renamed to 'fluidd.bak.cfg' to be able to continue with the installation."
        if ! mv "${path}/fluidd.cfg" "${path}/fluidd.bak.cfg"; then
          error_msg "Renaming fluidd.cfg failed! Aborting installation ..."
          return
        fi
      fi

      if [[ -h "${path}/fluidd.cfg" ]]; then
        warn_msg "Recreating symlink in ${path} ..."
        rm -rf "${path}/fluidd.cfg"
      fi

      if ! ln -sf "${HOME}/fluidd-config/client.cfg" "${path}/fluidd.cfg"; then
        error_msg "Creating symlink failed! Aborting installation ..."
        return
      fi

      if ! grep -Eq "^\[include fluidd.cfg\]$" "${path}/printer.cfg"; then
        log_info "${path}/printer.cfg"
        sed -i "1 i [include fluidd.cfg]" "${path}/printer.cfg"
      fi

      line=$(($(grep -n "\[include fluidd.cfg\]" "${path}/printer.cfg" | tail -1 | cut -d: -f1) + 1))
      gcode_dir=${path/config/gcodes}
      if ! grep -Eq "^\[virtual_sdcard\]$" "${path}/printer.cfg"; then
        log_info "${path}/printer.cfg"
        sed -i "${line} i \[virtual_sdcard]\npath: ${gcode_dir}\non_error_gcode: CANCEL_PRINT\n" "${path}/printer.cfg"
      fi
    done
  else
    print_error "Cloning failed! Aborting installation ..."
    log_error "execution stopped! reason: cloning failed"
    return
  fi

  patch_fluidd_config_update_manager

  ok_msg "Done!"
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

function remove_fluidd_nginx_config() {
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

  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs\/fluidd-.*"
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

function remove_fluidd_config() {
  if [[ -d "${HOME}/fluidd-config"  ]]; then
    status_msg "Removing ${HOME}/fluidd-config ..."
    rm -rf "${HOME}/fluidd-config"
    ok_msg "${HOME}/fluidd-config removed!"
    print_confirm "Fluidd-Config successfully removed!"
  fi
}

function remove_fluidd() {
  remove_fluidd_dir
  remove_fluidd_nginx_config
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
  local fl_tags tags latest_tag latest_url stable_tag stable_url url

  fl_tags="https://api.github.com/repos/fluidd-core/fluidd/tags"
  tags=$(curl -s "${fl_tags}" | grep "name" | cut -d'"' -f4)

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
    echo -e "| Make sure you don't choose a port which was already   |"
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
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  patched="false"
  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager fluidd\]\s*$" "${conf}"; then
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

function patch_fluidd_config_update_manager() {
  local patched moonraker_configs regex
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/config\/moonraker\.conf"
  moonraker_configs=$(find "${HOME}" -maxdepth 3 -type f -regextype posix-extended -regex "${regex}" | sort)

  patched="false"
  for conf in ${moonraker_configs}; do
    if ! grep -Eq "^\[update_manager fluidd-config\]\s*$" "${conf}"; then
      ### add new line to conf if it doesn't end with one
      [[ $(tail -c1 "${conf}" | wc -l) -eq 0 ]] && echo "" >> "${conf}"

      ### add Fluidds update manager section to moonraker.conf
      status_msg "Adding Fluidd-Config to update manager in file:\n       ${conf}"
      /bin/sh -c "cat >> ${conf}" << MOONRAKER_CONF

[update_manager fluidd-config]
type: git_repo
primary_branch: master
path: ~/fluidd-config
origin: https://github.com/fluidd-core/fluidd-config.git
managed_services: klipper
MOONRAKER_CONF

    fi

    patched="true"
  done

  if [[ ${patched} == "true" ]]; then
    do_action_service "restart" "moonraker"
  fi
}
