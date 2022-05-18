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

function process_disruptive_services() {
  #handle haproxy service
  if [[ ${DISABLE_HAPROXY} == "true" || ${REMOVE_HAPROXY} == "true" ]]; then
    if systemctl is-active haproxy -q; then
      status_msg "Stopping haproxy service ..."
      sudo systemctl stop haproxy && ok_msg "Service stopped!"
    fi

    ### disable haproxy
    if [[ ${DISABLE_HAPROXY} == "true" ]]; then
      status_msg "Disabling haproxy ..."
      sudo systemctl disable haproxy && ok_msg "Haproxy service disabled!"

      ### remove haproxy
      if [[ ${REMOVE_HAPROXY} == "true" ]]; then
        status_msg "Removing haproxy ..."
        sudo apt-get remove haproxy -y && sudo update-rc.d -f haproxy remove && ok_msg "Haproxy removed!"
      fi
    fi
  fi

  ### handle lighttpd service
  if [[ ${DISABLE_LIGHTTPD} == "true" || ${REMOVE_LIGHTTPD} == "true" ]]; then
    if systemctl is-active lighttpd -q; then
      status_msg "Stopping lighttpd service ..."
      sudo systemctl stop lighttpd && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [[ ${DISABLE_LIGHTTPD} == "true" ]]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable lighttpd && ok_msg "Lighttpd service disabled!"

      ### remove lighttpd
      if [[ ${REMOVE_LIGHTTPD} == "true" ]]; then
        status_msg "Removing lighttpd ..."
        sudo apt-get remove lighttpd -y && sudo update-rc.d -f lighttpd remove && ok_msg "Lighttpd removed!"
      fi
    fi
  fi

  ### handle apache2 service
  if [[ ${DISABLE_APACHE2} == "true" || ${REMOVE_APACHE2} == "true" ]]; then
    if systemctl is-active apache2 -q; then
      status_msg "Stopping apache2 service ..."
      sudo systemctl stop apache2 && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [[ ${DISABLE_APACHE2} == "true" ]]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable apache2 && ok_msg "Apache2 service disabled!"

      ### remove lighttpd
      if [[ ${REMOVE_APACHE2} == "true" ]]; then
        status_msg "Removing apache2 ..."
        sudo apt-get remove apache2 -y && sudo update-rc.d -f apache2 remove && ok_msg "Apache2 removed!"
      fi
    fi
  fi
}

function process_services_dialog() {
  #notify user about haproxy or lighttpd services found and possible issues
  if [[ ${HAPROXY_FOUND} == "true" || ${LIGHTTPD_FOUND} == "true" || ${APACHE2_FOUND} == "true" ]]; then
    while true; do
      echo
      top_border
      echo -e "| ${red}Possibly disruptive/incompatible services found!${white}      |"
      hr
      if [[ ${HAPROXY_FOUND} == "true" ]]; then
        echo -e "| ● haproxy                                             |"
      fi
      if [[ ${LIGHTTPD_FOUND} == "true" ]]; then
        echo -e "| ● lighttpd                                            |"
      fi
      if [[ ${APACHE2_FOUND} == "true" ]]; then
        echo -e "| ● apache2                                             |"
      fi
      hr
      echo -e "| Having those packages installed can lead to unwanted  |"
      echo -e "| behaviour. It's recommended to remove those packages. |"
      echo -e "|                                                       |"
      echo -e "| 1) Remove packages (recommend)                        |"
      echo -e "| 2) Disable only (may cause issues)                    |"
      echo -e "| ${red}3) Skip this step (not recommended)${white}                   |"
      bottom_border

      local action
      read -p "${cyan}###### Please choose:${white} " action
      case "${action}" in
        1)
          echo -e "###### > Remove packages"
          REMOVE_HAPROXY="true"
          REMOVE_LIGHTTPD="true"
          REMOVE_APACHE2="true"
          break;;
        2)
          echo -e "###### > Disable only"
          DISABLE_HAPROXY="true"
          DISABLE_LIGHTTPD="true"
          DISABLE_APACHE2="true"
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

function read_listen_port() {
  local port interface=${1}
  port=$(grep listen "/etc/nginx/sites-enabled/${interface}" | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
  echo "${port}"
}

function detect_enabled_sites() {
  MAINSAIL_ENABLED="false" FLUIDD_ENABLED="false" OCTOPRINT_ENABLED="false"
  #check if there is another UI config already installed and reads the port they are listening on
  if [[ -e "/etc/nginx/sites-enabled/mainsail" ]]; then
    SITE_ENABLED="true" && MAINSAIL_ENABLED="true"
    MAINSAIL_PORT=$(read_listen_port "mainsail")
  fi
  if [[ -e "/etc/nginx/sites-enabled/fluidd" ]]; then
    SITE_ENABLED="true" && FLUIDD_ENABLED="true"
    FLUIDD_PORT=$(read_listen_port "fluidd")

  fi
  if [[ -e "/etc/nginx/sites-enabled/octoprint" ]]; then
    SITE_ENABLED="true" && OCTOPRINT_ENABLED="true"
    OCTOPRINT_PORT=$(read_listen_port "octoprint")
  fi
}