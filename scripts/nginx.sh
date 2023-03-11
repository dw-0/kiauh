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
#=================== REMOVE NGINX ==================#
#===================================================#

function remove_nginx() {
  if [[ $(dpkg -s nginx  2>/dev/null | grep "Status") = *\ installed ]]; then
    status_msg "Stopping NGINX service ..."
    if systemctl is-active nginx -q; then
      sudo systemctl stop nginx && ok_msg "Service stopped!"
    else
      warn_msg "NGINX service not active!"
    fi

    status_msg "Removing NGINX from system ..."
    if sudo apt-get remove nginx -y && sudo update-rc.d -f nginx remove; then
      ok_msg "NGINX removed!"
    else
      error_msg "Removing NGINX from system failed!"
    fi
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
  local interface path access_log error_log regex logpaths

  interface=${1}
  access_log="/var/log/nginx/${interface}-access.log"
  error_log="/var/log/nginx/${interface}-error.log"
  regex="${HOME//\//\\/}\/([A-Za-z0-9_]+)\/logs"
  logpaths=$(find "${HOME}" -maxdepth 2 -type d -regextype posix-extended -regex "${regex}" | sort)

  for path in ${logpaths}; do
    [[ ! -d ${path} ]] && mkdir -p "${path}"

    if [[ -f ${access_log} && ! -L "${path}/${interface}-access.log" ]]; then
      status_msg "Creating symlink for ${access_log} ..."
      ln -s "${access_log}" "${path}"
      ok_msg "Symlink created: ${path}/${interface}-access.log"
    fi

    if [[ -f ${error_log} && ! -L "${path}/${interface}-error.log" ]]; then
      status_msg "Creating symlink for ${error_log} ..."
      ln -s "${error_log}" "${path}"
      ok_msg "Symlink created: ${path}/${interface}-error.log"
    fi
  done
}

function match_nginx_configs() {
  read_kiauh_ini "${FUNCNAME[0]}"
  local require_service_restart="false"
  local upstreams="${NGINX_CONFD}/upstreams.conf"
  local common_vars="${NGINX_CONFD}/common_vars.conf"
  local mainsail_nginx_cfg="/etc/nginx/sites-available/mainsail"
  local fluidd_nginx_cfg="/etc/nginx/sites-available/fluidd"
  local upstreams_webcams
  local mainsail_webcams
  local fluidd_webcams

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
  fi

  ### check for outdated mainsail config
  if [[ -e ${mainsail_nginx_cfg} ]] && (( upstreams_webcams > mainsail_webcams )); then
    status_msg "Outdated Mainsail config found! Updating ..."

    sudo rm -f "${mainsail_nginx_cfg}"
    sudo cp "${RESOURCES}/mainsail" "${mainsail_nginx_cfg}"
    sudo sed -i "s/<<UI>>/mainsail/g" "${mainsail_nginx_cfg}"
    sudo sed -i "/root/s/pi/${USER}/" "${mainsail_nginx_cfg}"
    sudo sed -i "s/listen\s[0-9]*;/listen ${mainsail_port};/" "${mainsail_nginx_cfg}"
    sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${mainsail_port};/" "${mainsail_nginx_cfg}"

    require_service_restart="true"
  fi

  ### check for outdated fluidd config
  if [[ -e ${fluidd_nginx_cfg} ]] && (( upstreams_webcams > fluidd_webcams )); then
    status_msg "Outdated Fluidd config found! Updating ..."

    sudo rm -f "${fluidd_nginx_cfg}"
    sudo cp "${RESOURCES}/fluidd" "${fluidd_nginx_cfg}"
    sudo sed -i "s/<<UI>>/fluidd/g" "${fluidd_nginx_cfg}"
    sudo sed -i "/root/s/pi/${USER}/" "${fluidd_nginx_cfg}"
    sudo sed -i "s/listen\s[0-9]*;/listen ${fluidd_port};/" "${fluidd_nginx_cfg}"
    sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${fluidd_port};/" "${fluidd_nginx_cfg}"

    require_service_restart="true"
  fi

  ### only restart nginx if configs were updated
  if [[ ${require_service_restart} == "true" ]]; then
    sudo systemctl restart nginx.service
  fi

  ok_msg "Done!"
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
    status_msg "Removing haproxy from system ..."
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
  [[ $(dpkg -s apache2  2>/dev/null | grep "Status") = *\ installed ]] && apache="true"
  ### check system for an installed haproxy service
  [[ $(dpkg -s haproxy  2>/dev/null | grep "Status") = *\ installed ]] && haproxy="true"

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
      echo -e "| ${green}1) Remove packages (recommend)${white}                        |"
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
          error_msg "Invalid command!";;
      esac
    done
  fi
}

function set_nginx_cfg() {
  local interface=${1}

  if [[ ${SET_NGINX_CFG} == "true" ]]; then
    #check for dependencies
    local dep=(nginx)
    dependency_check "${dep[@]}"

    local cfg_src="${RESOURCES}/${interface}"
    local cfg_dest="/etc/nginx/sites-available/${interface}"

    status_msg "Creating NGINX configuration for ${interface^} ..."

    # copy config to destination and set correct username
    [[ -f ${cfg_dest} ]] && sudo rm -f "${cfg_dest}"
    sudo cp "${cfg_src}" "${cfg_dest}"
    sudo sed -i "/root/s/pi/${USER}/" "${cfg_dest}"

    if [[ ${SET_LISTEN_PORT} != "${DEFAULT_PORT}" ]]; then
      sudo sed -i "s/listen\s[0-9]*;/listen ${SET_LISTEN_PORT};/" "${cfg_dest}"
      sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${SET_LISTEN_PORT};/" "${cfg_dest}"
    fi

    #remove nginx default config
    if [[ -e "/etc/nginx/sites-enabled/default" ]]; then
      sudo rm "/etc/nginx/sites-enabled/default"
    fi

    #create symlink for own sites
    if [[ ! -e "/etc/nginx/sites-enabled/${interface}" ]]; then
      sudo ln -s "/etc/nginx/sites-available/${interface}" "/etc/nginx/sites-enabled/"
    fi

    if [[ -n ${SET_LISTEN_PORT} ]]; then
      ok_msg "${interface^} configured for port ${SET_LISTEN_PORT}!"
    else
      ok_msg "${interface^} configured for default port ${DEFAULT_PORT}!"
    fi

    sudo systemctl restart nginx.service

    ok_msg "NGINX configuration for ${interface^} was set!"
  fi
}

###
# check if permissions of the users home directory
# grant execution rights to group and other which is
# required for NGINX to be able to serve Mainsail/Fluidd
#
function set_nginx_permissions() {
  local homedir_perm
  local exec_perms_count

  homedir_perm=$(ls -ld "${HOME}")
  exec_perms_count=$(echo "${homedir_perm}" | cut -d" " -f1 | grep -c "x")

  if (( exec_perms_count < 3 )); then
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