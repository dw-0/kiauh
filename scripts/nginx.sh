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
NGINX_SA="/etc/nginx/sites-available"
NGINX_SE="/etc/nginx/sites-enabled"
NGINX_CONFD="/etc/nginx/conf.d"

#===================================================#
#=================== REMOVE NGINX ==================#
#===================================================#

function remove_nginx(){
  if [ -f "${SYSTEMD}/nginx.service" ]; then
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

function set_upstream_nginx_cfg(){
  local current_date
  current_date=$(get_date)
  ### backup existing nginx configs
  [ ! -d "${BACKUP_DIR}/nginx_cfg" ] && mkdir -p "${BACKUP_DIR}/nginx_cfg"
  [ -f "${NGINX_CONFD}/upstreams.conf" ] && sudo mv "${NGINX_CONFD}/upstreams.conf" "${BACKUP_DIR}/nginx_cfg/${current_date}_upstreams.conf"
  [ -f "${NGINX_CONFD}/common_vars.conf" ] && sudo mv "${NGINX_CONFD}/common_vars.conf" "${BACKUP_DIR}/nginx_cfg/${current_date}_common_vars.conf"
  ### transfer ownership of backed up files from root to ${USER}
  local files
  files=$(find "${BACKUP_DIR}/nginx_cfg")
  for file in ${files}; do
    if [ "$(stat -c "%U" "${file}" )" != "${USER}" ]; then
      log_info "chown for user: ${USER} on file: ${file}"
      sudo chown "${USER}" "${file}"
    fi
  done
  ### copy nginx configs to target destination
  if [ ! -f "${NGINX_CONFD}/upstreams.conf" ]; then
    sudo cp "${SRCDIR}/kiauh/resources/upstreams.conf" "${NGINX_CONFD}"
  fi
  if [ ! -f "${NGINX_CONFD}/common_vars.conf" ]; then
    sudo cp "${SRCDIR}/kiauh/resources/common_vars.conf" "${NGINX_CONFD}"
  fi
}

function symlink_webui_nginx_log(){
  local path="${HOME}/klipper_logs"
  local access_log="/var/log/nginx/${1}-access.log"
  local error_log="/var/log/nginx/${1}-error.log"
  [ ! -d "${path}" ] && mkdir -p "${path}"
  if [ -f "${access_log}" ] &&  [ ! -L "${path}/${1}-access.log" ]; then
    status_msg "Creating symlink for ${access_log} ..."
    ln -s "${access_log}" "${path}"
    ok_msg "OK!"
  fi
  if [ -f "${error_log}" ] &&  [ ! -L "${path}/${1}-error.log" ]; then
    status_msg "Creating symlink for ${error_log} ..."
    ln -s "${error_log}" "${path}"
    ok_msg "OK!"
  fi
}

function match_nginx_configs(){
  local cfg_updated="false"
  ### reinstall nginx configs if the amount of upstreams don't match anymore
  read_kiauh_ini
  mainsail_nginx_cfg="/etc/nginx/sites-available/mainsail"
  fluidd_nginx_cfg="/etc/nginx/sites-available/fluidd"
  upstreams_webcams=$(grep -E "mjpgstreamer" /etc/nginx/conf.d/upstreams.conf | wc -l)
  status_msg "Checking validity of NGINX configurations ..."
  if [ -e "${mainsail_nginx_cfg}" ]; then
    mainsail_webcams=$(grep -E "mjpgstreamer" "${mainsail_nginx_cfg}" | wc -l)
  fi
  if [ -e "${fluidd_nginx_cfg}" ]; then
    fluidd_webcams=$(grep -E "mjpgstreamer" "${fluidd_nginx_cfg}" | wc -l)
  fi
  ### check for outdated upstreams.conf
  if [[ "${upstreams_webcams}" -lt "${mainsail_webcams}" ]] || [[ "${upstreams_webcams}" -lt "${fluidd_webcams}" ]]; then
    status_msg "Outdated upstreams.conf found! Updating ..."
    sudo rm -f "${NGINX_CONFD}/upstreams.conf"
    sudo rm -f "${NGINX_CONFD}/common_vars.conf"
    set_upstream_nginx_cfg
    cfg_updated="true"
  fi
  ### check for outdated mainsail config
  if [ -e "${mainsail_nginx_cfg}" ]; then
    if [[ "${upstreams_webcams}" -gt "${mainsail_webcams}" ]]; then
      status_msg "Outdated Mainsail config found! Updating ..."
      sudo rm -f "${mainsail_nginx_cfg}"
      sudo cp "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" "${mainsail_nginx_cfg}"
      sudo sed -i "s/<<UI>>/mainsail/g" "${mainsail_nginx_cfg}"
      sudo sed -i "/root/s/pi/${USER}/" "${mainsail_nginx_cfg}"
      sudo sed -i "s/listen\s[0-9]*;/listen ${mainsail_port};/" "${mainsail_nginx_cfg}"
      sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${mainsail_port};/" "${mainsail_nginx_cfg}"
      cfg_updated="true" && ok_msg "Done!"
    fi
  fi
  ### check for outdated fluidd config
  if [ -e "${fluidd_nginx_cfg}" ]; then
    if [[ "${upstreams_webcams}" -gt "${fluidd_webcams}" ]]; then
      status_msg "Outdated Fluidd config found! Updating ..."
      sudo rm -f "${fluidd_nginx_cfg}"
      sudo cp "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" "${fluidd_nginx_cfg}"
      sudo sed -i "s/<<UI>>/fluidd/g" "${fluidd_nginx_cfg}"
      sudo sed -i "/root/s/pi/${USER}/" "${fluidd_nginx_cfg}"
      sudo sed -i "s/listen\s[0-9]*;/listen ${fluidd_port};/" "${fluidd_nginx_cfg}"
      sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${fluidd_port};/" "${fluidd_nginx_cfg}"
      cfg_updated="true" && ok_msg "Done!"
    fi
  fi
  ### only restart nginx if configs were updated
  [ "${cfg_updated}" == "true" ] && do_action_service "restart" "nginx"
}

function process_disruptive_services(){
  #handle haproxy service
  if [ "${DISABLE_HAPROXY}" = "true" ] || [ "${REMOVE_HAPROXY}" = "true" ]; then
    if systemctl is-active haproxy -q; then
      status_msg "Stopping haproxy service ..."
      sudo systemctl stop haproxy && ok_msg "Service stopped!"
    fi

    ### disable haproxy
    if [ "${DISABLE_HAPROXY}" = "true" ]; then
      status_msg "Disabling haproxy ..."
      sudo systemctl disable haproxy && ok_msg "Haproxy service disabled!"

      ### remove haproxy
      if [ "${REMOVE_HAPROXY}" = "true" ]; then
        status_msg "Removing haproxy ..."
        sudo apt-get remove haproxy -y && sudo update-rc.d -f haproxy remove && ok_msg "Haproxy removed!"
      fi
    fi
  fi

  ### handle lighttpd service
  if [ "${DISABLE_LIGHTTPD}" = "true" ] || [ "${REMOVE_LIGHTTPD}" = "true" ]; then
    if systemctl is-active lighttpd -q; then
      status_msg "Stopping lighttpd service ..."
      sudo systemctl stop lighttpd && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [ "${DISABLE_LIGHTTPD}" = "true" ]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable lighttpd && ok_msg "Lighttpd service disabled!"

      ### remove lighttpd
      if [ "${REMOVE_LIGHTTPD}" = "true" ]; then
        status_msg "Removing lighttpd ..."
        sudo apt-get remove lighttpd -y && sudo update-rc.d -f lighttpd remove && ok_msg "Lighttpd removed!"
      fi
    fi
  fi

  ### handle apache2 service
  if [ "${DISABLE_APACHE2}" = "true" ] || [ "${REMOVE_APACHE2}" = "true" ]; then
    if systemctl is-active apache2 -q; then
      status_msg "Stopping apache2 service ..."
      sudo systemctl stop apache2 && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [ "${DISABLE_APACHE2}" = "true" ]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable apache2 && ok_msg "Apache2 service disabled!"

      ### remove lighttpd
      if [ "${REMOVE_APACHE2}" = "true" ]; then
        status_msg "Removing apache2 ..."
        sudo apt-get remove apache2 -y && sudo update-rc.d -f apache2 remove && ok_msg "Apache2 removed!"
      fi
    fi
  fi
}

function process_services_dialog(){
  #notify user about haproxy or lighttpd services found and possible issues
  if [ "${HAPROXY_FOUND}" = "true" ] || [ "${LIGHTTPD_FOUND}" = "true" ] || [ "${APACHE2_FOUND}" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "| ${red}Possibly disruptive/incompatible services found!${white}      |"
      hr
      if [ "${HAPROXY_FOUND}" = "true" ]; then
        echo -e "| ● haproxy                                             |"
      fi
      if [ "${LIGHTTPD_FOUND}" = "true" ]; then
        echo -e "| ● lighttpd                                            |"
      fi
      if [ "${APACHE2_FOUND}" = "true" ]; then
        echo -e "| ● apache2                                             |"
      fi
      hr
      echo -e "| Having those packages installed can lead to unwanted  |"
      echo -e "| behaviour. It is recommend to remove those packages.  |"
      echo -e "|                                                       |"
      echo -e "| 1) Remove packages (recommend)                        |"
      echo -e "| 2) Disable only (may cause issues)                    |"
      echo -e "| ${red}3) Skip this step (not recommended)${white}                   |"
      bottom_border
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

function set_nginx_cfg(){
  if [ "${SET_NGINX_CFG}" = "true" ]; then
    local cfg="${SRCDIR}/kiauh/resources/${1}"
    #check for dependencies
    dep=(nginx)
    dependency_check "${dep[@]}"
    #execute operations
    status_msg "Creating Nginx configuration for ${1} ..."
    #copy content from resources to the respective nginx config file
    cat "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" > "${cfg}"
    ##edit the nginx config file before moving it
    sed -i "s/<<UI>>/${1}/g" "${cfg}"
    if [ "${SET_LISTEN_PORT}" != "${DEFAULT_PORT}" ]; then
      status_msg "Configuring port for $1 ..."
      #set listen port ipv4
      sed -i "s/listen\s[0-9]*;/listen ${SET_LISTEN_PORT};/" "${cfg}"
      #set listen port ipv6
      sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:${SET_LISTEN_PORT};/" "${cfg}"
    fi
    #set correct user
    if [ "${1}" = "mainsail" ] || [ "${1}" = "fluidd" ]; then
      sudo sed -i "/root/s/pi/${USER}/" "${cfg}"
    fi
    #moving the config file into correct directory
    sudo mv "${cfg}" "/etc/nginx/sites-available/${1}"
    ok_msg "Nginx configuration for $1 was set!"
    if [ -n "${SET_LISTEN_PORT}" ]; then
      ok_msg "${1} listening on port ${SET_LISTEN_PORT}!"
    else
      ok_msg "${1} listening on default port ${DEFAULT_PORT}!"
    fi
    #remove nginx default config
    [ -e "/etc/nginx/sites-enabled/default" ] && sudo rm "/etc/nginx/sites-enabled/default"
    #create symlink for own sites
    [ ! -e "/etc/nginx/sites-enabled/${1}" ] && sudo ln -s "/etc/nginx/sites-available/${1}" "/etc/nginx/sites-enabled/"

    do_action_service "restart" "nginx"
  fi
}

function read_listen_port(){
  LISTEN_PORT=$(grep listen "/etc/nginx/sites-enabled/${1}" | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
}

function detect_enabled_sites(){
  #check if there is another UI config already installed
  #and reads the port they are listening on
  if [ -e "/etc/nginx/sites-enabled/mainsail" ]; then
    SITE_ENABLED="true" && MAINSAIL_ENABLED="true"
    read_listen_port "mainsail"
    MAINSAIL_PORT=${LISTEN_PORT}
    #echo "debug: Mainsail listens on port: $MAINSAIL_PORT"
  else
    MAINSAIL_ENABLED="false"
  fi
  if [ -e /etc/nginx/sites-enabled/fluidd ]; then
    SITE_ENABLED="true" && FLUIDD_ENABLED="true"
    read_listen_port "fluidd"
    FLUIDD_PORT=${LISTEN_PORT}
    #echo "debug: Fluidd listens on port: $FLUIDD_PORT"
  else
    FLUIDD_ENABLED="false"
  fi
  if [ -e /etc/nginx/sites-enabled/octoprint ]; then
    SITE_ENABLED="true" && OCTOPRINT_ENABLED="true"
    read_listen_port "octoprint"
    OCTOPRINT_PORT=${LISTEN_PORT}
    #echo "debug: OctoPrint listens on port: $OCTOPRINT_PORT"
  else
    OCTOPRINT_ENABLED="false"
  fi
}