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
#=================== REMOVE NGINX ==================#
#===================================================#

function remove_nginx() {
  if [[ -f "${SYSTEMD}/nginx.service" ]]; then
    status_msg "Stopping Nginx service ..."
    sudo systemctl stop nginx && sudo systemctl disable nginx
    ok_msg "Service stopped and disabled!"

    status_msg "Purging Nginx from system ..."
    sudo apt-get purge nginx nginx-common -y
    sudo update-rc.d -f nginx remove

    print_confirm "Nginx successfully removed!"
  else
    print_error "Looks like Nginx was already removed!\n Skipping..."
  fi
}

#===================================================#
#===================== HELPERS =====================#
#===================================================#

function set_upstream_nginx_cfg() {
  local current_date
  local upstreams="${NGINX_CONFD}/upstreams.conf"
  local common_vars="${NGINX_CONFD}/common_vars.conf"

  current_date=$(get_date)

  ### backup existing nginx configs
  [[ ! -d "${BACKUP_DIR}/nginx_cfg" ]] && mkdir -p "${BACKUP_DIR}/nginx_cfg"

  if [[ -f ${upstreams} ]]; then
    sudo mv "${upstreams}" "${BACKUP_DIR}/nginx_cfg/${current_date}_upstreams.conf"
  fi

  if [[ -f ${common_vars} ]]; then
    sudo mv "${common_vars}" "${BACKUP_DIR}/nginx_cfg/${current_date}_common_vars.conf"
  fi

  ### transfer ownership of backed up files from root to ${USER}
  local files
  files=$(find "${BACKUP_DIR}/nginx_cfg")

  for file in ${files}; do
    if [[ $(stat -c "%U" "${file}") != "${USER}" ]]; then
      log_info "chown for user: ${USER} on file: ${file}"
      sudo chown "${USER}" "${file}"
    fi
  done

  ### copy nginx configs to target destination
  [[ ! -f ${upstreams} ]] && sudo cp "${RESOURCES}/upstreams.conf" "${upstreams}"
  [[ ! -f ${common_vars} ]] && sudo cp "${RESOURCES}/common_vars.conf" "${common_vars}"
}

function symlink_webui_nginx_log() {
  local interface=${1} path="${KLIPPER_LOGS}"
  local access_log="/var/log/nginx/${interface}-access.log"
  local error_log="/var/log/nginx/${interface}-error.log"

  [[ ! -d ${path} ]] && mkdir -p "${path}"

  if [[ -f ${access_log} && ! -L "${path}/${interface}-access.log" ]]; then
    status_msg "Creating symlink for ${access_log} ..."
    ln -s "${access_log}" "${path}"
    ok_msg "Done!"
  fi

  if [[ -f ${error_log} && ! -L "${path}/${interface}-error.log" ]]; then
    status_msg "Creating symlink for ${error_log} ..."
    ln -s "${error_log}" "${path}"
    ok_msg "Done!"
  fi
}

function match_nginx_configs() {
  read_kiauh_ini "${FUNCNAME[0]}"
  local require_service_restart="false"
  local upstreams="${NGINX_CONFD}/upstreams.conf"
  local common_vars="${NGINX_CONFD}/common_vars.conf"
  local mainsail_nginx_cfg="/etc/nginx/sites-available/mainsail"
  local fluidd_nginx_cfg="/etc/nginx/sites-available/fluidd"
  local upstreams_webcams mainsail_webcams fluidd_webcams

  ### reinstall nginx configs if the amount of upstreams don't match anymore
  upstreams_webcams=$(grep -Ec "mjpgstreamer" "/etc/nginx/conf.d/upstreams.conf")
  mainsail_webcams=$(grep -Ec "mjpgstreamer" "${mainsail_nginx_cfg}" 2>/dev/null || echo "0")
  fluidd_webcams=$(grep -Ec "mjpgstreamer" "${fluidd_nginx_cfg}" 2>/dev/null || echo "0")

  status_msg "Checking validity of NGINX configurations ..."

  ### check for outdated upstreams.conf
  if (( upstreams_webcams < mainsail_webcams || upstreams_webcams < fluidd_webcams )); then
    status_msg "Outdated upstreams.conf found! Updating ..."

    sudo rm -f "${upstreams}" "${common_vars}"
    set_upstream_nginx_cfg

    require_service_restart="true"
    ok_msg "Done!"
  fi

  ### check for outdated mainsail config
  if [[ -e ${mainsail_nginx_cfg} ]] && (( upstreams_webcams > mainsail_webcams )); then
    status_msg "Outdated Mainsail config found! Updating ..."

    sudo rm -f "${mainsail_nginx_cfg}"
    sudo cp "${RESOURCES}/klipper_webui_nginx.cfg" "${mainsail_nginx_cfg}"
    sudo sed -i "s/<<UI>>/mainsail/g" "${mainsail_nginx_cfg}"
    sudo sed -i "/root/s/pi/${USER}/" "${mainsail_nginx_cfg}"
    sudo sed -i "s/listen\s[0-9]*;/listen ${mainsail_port};/" "${mainsail_nginx_cfg}"
    sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${mainsail_port};/" "${mainsail_nginx_cfg}"

    require_service_restart="true"
    ok_msg "Done!"
  fi

  ### check for outdated fluidd config
  if [[ -e ${fluidd_nginx_cfg} ]] && (( upstreams_webcams > fluidd_webcams )); then
    status_msg "Outdated Fluidd config found! Updating ..."

    sudo rm -f "${fluidd_nginx_cfg}"
    sudo cp "${RESOURCES}/klipper_webui_nginx.cfg" "${fluidd_nginx_cfg}"
    sudo sed -i "s/<<UI>>/fluidd/g" "${fluidd_nginx_cfg}"
    sudo sed -i "/root/s/pi/${USER}/" "${fluidd_nginx_cfg}"
    sudo sed -i "s/listen\s[0-9]*;/listen ${fluidd_port};/" "${fluidd_nginx_cfg}"
    sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${fluidd_port};/" "${fluidd_nginx_cfg}"

    require_service_restart="true"
    ok_msg "Done!"
  fi

  ### only restart nginx if configs were updated
  [[ ${require_service_restart} == "true" ]] && sudo systemctl restart nginx.service
}

function remove_conflicting_packages() {
  local apache=${1} haproxy=${2}

  ### disable services before removing them
  disable_conflicting_packages "${apache}" "${haproxy}"

  if [[ ${apache} == "true" ]]; then
    status_msg "Removing Apache2 from system ..."
    if sudo apt-get remove apache2 -y && sudo update-rc.d -f apache2 remove; then
      ok_msg "Apache2 removed!"
    else
      error_msg "Removing Apache2 from system failed!"
    fi
  fi

  if [[ ${haproxy} == "true" ]]; then
    status_msg "Removing haproxy ..."
    if sudo apt-get remove haproxy -y && sudo update-rc.d -f haproxy remove; then
      ok_msg "Haproxy removed!"
    else
      error_msg "Removing Haproxy from system failed!"
    fi
  fi
}

function disable_conflicting_packages() {
  local apache=${1} haproxy=${2}

  if [[ ${apache} == "true" ]]; then
    status_msg "Stopping Apache2 service ..."
    if systemctl is-active apache2 -q; then
      sudo systemctl stop apache2 && ok_msg "Service stopped!"
    else
      warn_msg "Apache2 service not active!"
    fi

    status_msg "Disabling Apache2 service ..."
    if sudo systemctl disable apache2; then
      ok_msg "Apache2 service disabled!"
    else
      error_msg "Disabling Apache2 service failed!"
    fi
  fi

  if [[ ${haproxy} == "true" ]]; then
    status_msg "Stopping Haproxy service ..."
    if systemctl is-active haproxy -q; then
      sudo systemctl stop haproxy && ok_msg "Service stopped!"
    else
      warn_msg "Haproxy service not active!"
    fi

    status_msg "Disabling Haproxy service ..."
    if sudo systemctl disable haproxy; then
      ok_msg "Haproxy service disabled!"
    else
      error_msg "Disabling Haproxy service failed!"
    fi
  fi
}

function detect_conflicting_packages() {
  local apache="false" haproxy="false"

  ### check system for an installed apache2 service
  [[ $(dpkg-query -f'${Status}' --show apache2 2>/dev/null) = *\ installed ]] && apache="true"
  ### check system for an installed haproxy service
  [[ $(dpkg-query -f'${Status}' --show haproxy 2>/dev/null) = *\ installed ]] && haproxy="true"

  #notify user about haproxy or apache2 services found and possible issues
  if [[ ${haproxy} == "false" && ${apache} == "false" ]]; then
    return
  else
    while true; do
      echo
      top_border
      echo -e "| ${red}Conflicting package installations found:${white}              |"
      [[ ${apache} == "true" ]] && \
      echo -e "| ${red}● apache2${white}                                             |"
      [[ ${haproxy} == "true" ]] && \
      echo -e "| ${red}● haproxy${white}                                             |"
      blank_line
      echo -e "| Having those packages installed can lead to unwanted  |"
      echo -e "| behaviour. It's recommended to remove those packages. |"
      echo -e "|                                                       |"
      echo -e "| 1) Remove packages (recommend)                        |"
      echo -e "| 2) Disable only (may still cause issues)              |"
      echo -e "| ${red}3) Skip this step (not recommended)${white}                   |"
      bottom_border

      local action
      read -p "${cyan}###### Please choose:${white} " action
      case "${action}" in
        1)
          echo -e "###### > Remove packages"
          remove_conflicting_packages "${apache}" "${haproxy}"
          break;;
        2)
          echo -e "###### > Disable only"
          disable_conflicting_packages "${apache}" "${haproxy}"
          break;;
        3)
          echo -e "###### > Skip"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

function set_nginx_cfg() {
  local interface=${1}
  if [[ ${SET_NGINX_CFG} == "true" ]]; then
    local cfg="${RESOURCES}/${interface}"
    #check for dependencies
    local dep=(nginx)
    dependency_check "${dep[@]}"

    status_msg "Creating Nginx configuration for ${interface^} ..."
    cat "${RESOURCES}/klipper_webui_nginx.cfg" > "${cfg}"
    sed -i "s/<<UI>>/${interface}/g" "${cfg}"

    if [[ ${SET_LISTEN_PORT} != "${DEFAULT_PORT}" ]]; then
      status_msg "Configuring port for ${interface^} ..."
      sed -i "s/listen\s[0-9]*;/listen ${SET_LISTEN_PORT};/" "${cfg}"
      sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${SET_LISTEN_PORT};/" "${cfg}"
    fi

    #set correct user
    if [[ ${interface} == "mainsail" || ${interface} == "fluidd" ]]; then
      sudo sed -i "/root/s/pi/${USER}/" "${cfg}"
    fi

    #moving the config file into correct directory
    sudo mv "${cfg}" "/etc/nginx/sites-available/${interface}"
    ok_msg "Nginx configuration for ${interface^} was set!"
    if [[ -n ${SET_LISTEN_PORT} ]]; then
      ok_msg "${interface^} configured for port ${SET_LISTEN_PORT}!"
    else
      ok_msg "${interface^} configured for default port ${DEFAULT_PORT}!"
    fi

    #remove nginx default config
    if [[ -e "/etc/nginx/sites-enabled/default" ]]; then
      sudo rm "/etc/nginx/sites-enabled/default"
    fi

    #create symlink for own sites
    if [[ ! -e "/etc/nginx/sites-enabled/${interface}" ]]; then
      sudo ln -s "/etc/nginx/sites-available/${interface}" "/etc/nginx/sites-enabled/"
    fi
    sudo systemctl restart nginx.service
  fi
}

function set_nginx_permissions() {
  local distro_name version_id

  distro_name=$(grep -E "^NAME=" /etc/os-release | cut -d'"' -f2)
  version_id=$(grep -E "^VERSION_ID=" /etc/os-release | cut -d'"' -f2)

  if [[ ${distro_name} == "Ubuntu" && ( ${version_id} == "21.10" || ${version_id} == "22.04") ]]; then
    status_msg "Granting NGINX the required permissions ..."
    chmod og+x "${HOME}" && ok_msg "Done!"
  fi

  return
}

function read_listen_port() {
  local port interface=${1}
  port=$(grep listen "/etc/nginx/sites-enabled/${interface}" | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
  echo "${port}"
}

function detect_enabled_sites() {
  MAINSAIL_ENABLED="false" FLUIDD_ENABLED="false"
  #check if there is another UI config already installed and reads the port they are listening on
  if [[ -e "/etc/nginx/sites-enabled/mainsail" ]]; then
    SITE_ENABLED="true" && MAINSAIL_ENABLED="true"
    MAINSAIL_PORT=$(read_listen_port "mainsail")
  fi
  if [[ -e "/etc/nginx/sites-enabled/fluidd" ]]; then
    SITE_ENABLED="true" && FLUIDD_ENABLED="true"
    FLUIDD_PORT=$(read_listen_port "fluidd")

  fi
}