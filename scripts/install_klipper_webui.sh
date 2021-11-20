MAINSAIL_REPO_API="https://api.github.com/repos/mainsail-crew/mainsail/releases"
FLUIDD_REPO_API="https://api.github.com/repos/fluidd-core/fluidd/releases"

system_check_webui(){
  ### check system for installed moonraker service
  if ls /etc/systemd/system/moonraker.service 2>/dev/null 1>&2 || ls /etc/systemd/system | grep -q -E "moonraker-[[:digit:]]+.service"; then
    moonraker_chk_ok="true"
  else
    moonraker_chk_ok="false"
  fi

  ### check system for an installed and enabled octoprint service
  if sudo systemctl list-unit-files | grep -E "octoprint.*" | grep "enabled" &>/dev/null; then
    OCTOPRINT_ENABLED="true"
  fi

  ### check system for an installed haproxy service
  if [[ $(dpkg-query -f'${Status}' --show haproxy 2>/dev/null) = *\ installed ]]; then
    HAPROXY_FOUND="true"
  fi

  ### check system for an installed lighttpd service
  if [[ $(dpkg-query -f'${Status}' --show lighttpd 2>/dev/null) = *\ installed ]]; then
    LIGHTTPD_FOUND="true"
  fi
}

get_user_selection_mjpg-streamer(){
  while true; do
    unset INSTALL_MJPG
    echo
    top_border
    echo -e "|  Install MJGP-Streamer for webcam support?            |"
    bottom_border
    read -p "${cyan}###### Install MJPG-Streamer? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        INSTALL_MJPG="true"
        break;;
      N|n|No|no)
        echo -e "###### > No"
        INSTALL_MJPG="false"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

get_user_selection_kiauh_macros(){
  #ask user for webui default macros
  while true; do
    unset ADD_KIAUH_MACROS
    echo
    top_border
    echo -e "| It is recommended to have some important macros set   |"
    echo -e "| up in your printer configuration to have $1|"
    echo -e "| fully functional and working.                         |"
    blank_line
    echo -e "| Those macros are:                                     |"
    echo -e "| ${cyan}● [gcode_macro PAUSE]${default}                                 |"
    echo -e "| ${cyan}● [gcode_macro RESUME]${default}                                |"
    echo -e "| ${cyan}● [gcode_macro CANCEL_PRINT]${default}                          |"
    blank_line
    echo -e "| If you already have these macros in your config file  |"
    echo -e "| you can skip this step and choose 'no'.               |"
    echo -e "| Otherwise you should consider to answer with 'yes' to |"
    echo -e "| add the recommended example macros to your config.    |"
    bottom_border
    read -p "${cyan}###### Add the recommended macros? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        ADD_KIAUH_MACROS="true"
        break;;
      N|n|No|no)
        echo -e "###### > No"
        ADD_KIAUH_MACROS="false"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

install_webui(){
  source_kiauh_ini
  ### checking dependencies
  dep=(nginx)
  dependency_check
  ### check if moonraker is already installed
  system_check_webui
  ### ask user how to handle OctoPrint, Haproxy and Lighttpd if found
  process_octoprint_dialog
  process_haproxy_lighttpd_dialog
  ### process possible disruptive services
  process_haproxy_lighttpd_services

  [ $1 == "mainsail" ] && IF_NAME1="Mainsail" && IF_NAME2="Mainsail     "
  [ $1 == "fluidd" ] && IF_NAME1="Fluidd" && IF_NAME2="Fluidd       "

  ### exit mainsail/fluidd setup if moonraker not found
  if [ $moonraker_chk_ok = "false" ]; then
    ERROR_MSG="Moonraker service not found!\n Please install Moonraker first!"
    print_msg && clear_msg && return 0
  fi

  status_msg "Initializing $IF_NAME1 installation ..."
  ### check for other enabled web interfaces
  unset SET_LISTEN_PORT
  detect_enabled_sites

  ### check if another site already listens to port 80
  $1_port_check

  ### ask user to install mjpg-streamer
  if ls /etc/systemd/system/webcamd.service 2>/dev/null 1>&2; then
    get_user_selection_mjpg-streamer
  fi

  ### ask user to install the recommended webinterface macros
  if ! ls $klipper_cfg_loc/kiauh_macros.cfg 2>/dev/null 1>&2 || ! ls $klipper_cfg_loc/printer_*/kiauh_macros.cfg 2>/dev/null 1>&2; then
    get_user_selection_kiauh_macros "$IF_NAME2"
  fi
  ### create /etc/nginx/conf.d/upstreams.conf
  set_upstream_nginx_cfg
  ### create /etc/nginx/sites-available/<interface config>
  set_nginx_cfg "$1"

  ### symlink nginx log
  symlink_webui_nginx_log "$1"

  ### copy the kiauh_macros.cfg to the config location
  install_kiauh_macros

  ### install mainsail/fluidd
  $1_setup

  ### install mjpg-streamer
  [ "$INSTALL_MJPG" = "true" ] && install_mjpg-streamer

  fetch_webui_ports #WIP

  ### confirm message
  CONFIRM_MSG="$IF_NAME1 has been set up!"
  print_msg && clear_msg
}

symlink_webui_nginx_log(){
  LPATH="${HOME}/klipper_logs"
  UI_ACCESS_LOG="/var/log/nginx/$1-access.log"
  UI_ERROR_LOG="/var/log/nginx/$1-error.log"
  [ ! -d "$LPATH" ] && mkdir -p "$LPATH"
  if [ -f "$UI_ACCESS_LOG" ] &&  [ ! -L "$LPATH/$1-access.log" ]; then
    status_msg "Creating symlink for $UI_ACCESS_LOG ..."
    ln -s $UI_ACCESS_LOG "$LPATH"
    ok_msg "OK!"
  fi
  if [ -f "$UI_ERROR_LOG" ] &&  [ ! -L "$LPATH/$1-error.log" ]; then
    status_msg "Creating symlink for $UI_ERROR_LOG ..."
    ln -s $UI_ERROR_LOG "$LPATH"
    ok_msg "OK!"
  fi
}

install_kiauh_macros(){
  source_kiauh_ini
  ### copy kiauh_macros.cfg
  if [ "$ADD_KIAUH_MACROS" = "true" ]; then
    ### create a backup of the config folder
    backup_klipper_config_dir
    ### handle multi printer.cfg
    if ls $klipper_cfg_loc/printer_* 2>/dev/null 1>&2; then
      for config in $(find $klipper_cfg_loc/printer_*/printer.cfg); do
        path=$(echo $config | rev | cut -d"/" -f2- | rev)
        if [ ! -f $path/kiauh_macros.cfg ]; then
          ### copy kiauh_macros.cfg to config location
          status_msg "Creating macro config file ..."
          cp ${SRCDIR}/kiauh/resources/kiauh_macros.cfg $path
          ### write the include to the very first line of the printer.cfg
          sed -i "1 i [include kiauh_macros.cfg]" $path/printer.cfg
          ok_msg "$path/kiauh_macros.cfg created!"
        fi
      done
    ### handle single printer.cfg
    elif [ -f $klipper_cfg_loc/printer.cfg ] && [ ! -f $klipper_cfg_loc/kiauh_macros.cfg ]; then
      ### copy kiauh_macros.cfg to config location
      status_msg "Creating macro config file ..."
      cp ${SRCDIR}/kiauh/resources/kiauh_macros.cfg $klipper_cfg_loc
      ### write the include to the very first line of the printer.cfg
      sed -i "1 i [include kiauh_macros.cfg]" $klipper_cfg_loc/printer.cfg
      ok_msg "$klipper_cfg_loc/kiauh_macros.cfg created!"
    fi
    ### restart klipper service to parse the modified printer.cfg
    do_action_service "restart" "klipper"
  fi
}

mainsail_port_check(){
  if [ "$MAINSAIL_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo -e "   ${cyan}● OctoPrint - Port: $OCTOPRINT_PORT${default}"
      [ "$FLUIDD_ENABLED" = "true" ] && echo -e "   ${cyan}● Fluidd - Port: $FLUIDD_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo -e "   ${cyan}● DWC2 - Port: $DWC2_PORT${default}"
      if [ "$FLUIDD_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_mainsail_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

fluidd_port_check(){
  if [ "$FLUIDD_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo "   ${cyan}● OctoPrint - Port: $OCTOPRINT_PORT${default}"
      [ "$MAINSAIL_ENABLED" = "true" ] && echo "   ${cyan}● Mainsail - Port: $MAINSAIL_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo "   ${cyan}● DWC2 - Port: $DWC2_PORT${default}"
      if [ "$MAINSAIL_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_fluidd_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

select_mainsail_port(){
  if [ "$PORT_80_BLOCKED" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for Mainsail!${default}     |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "$OCTOPRINT_PORT" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "$FLUIDD_PORT" = "80" ] && echo "|  ● Fluidd                                             |"
    [ "$DWC2_PORT" = "80" ] && echo "|  ● DWC2                                               |"
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
      if [ "$NEW_PORT" != "$FLUIDD_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
        echo "Setting port $NEW_PORT for Mainsail!"
        SET_LISTEN_PORT=$NEW_PORT
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}

select_fluidd_port(){
  if [ "$PORT_80_BLOCKED" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for Fluidd!${default}       |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "$OCTOPRINT_PORT" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "$MAINSAIL_PORT" = "80" ] && echo "|  ● Mainsail                                           |"
    [ "$DWC2_PORT" = "80" ] && echo "|  ● DWC2                                               |"
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
      if [ "$NEW_PORT" != "$MAINSAIL_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
        echo "Setting port $NEW_PORT for Fluidd!"
        SET_LISTEN_PORT=$NEW_PORT
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}

get_mainsail_ver(){
  MAINSAIL_VERSION=$(curl -s $MAINSAIL_REPO_API | grep tag_name | cut -d'"' -f4 | head -1)
}

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s $FLUIDD_REPO_API | grep tag_name | cut -d'"' -f4 | head -1)
}

mainsail_setup(){
  ### get mainsail download url
  MAINSAIL_DL_URL=$(curl -s $MAINSAIL_REPO_API | grep browser_download_url | cut -d'"' -f4 | head -1)

  ### remove existing and create fresh mainsail folder, then download mainsail
  [ -d $MAINSAIL_DIR ] && rm -rf $MAINSAIL_DIR
  mkdir $MAINSAIL_DIR && cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail $MAINSAIL_VERSION ..."
  wget $MAINSAIL_DL_URL && ok_msg "Download complete!"

  ### extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"

  ### delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!"

  ### check for moonraker multi-instance and if multi-instance was found, enable mainsails remoteMode
  if [ $(ls /etc/systemd/system/moonraker* | grep -E "moonraker(-\d+)?\.service" | wc -l) -gt 1 ]; then
    enable_mainsail_remotemode
  fi
}

enable_mainsail_remotemode(){
  rm -f $MAINSAIL_DIR/config.json
  echo -e "{\n    \"remoteMode\":true\n}" >> $MAINSAIL_DIR/config.json
}

fluidd_setup(){
  ### get fluidd download url
  FLUIDD_DL_URL=$(curl -s $FLUIDD_REPO_API | grep browser_download_url | cut -d'"' -f4 | head -1)

  ### remove existing and create fresh fluidd folder, then download fluidd
  [ -d $FLUIDD_DIR ] && rm -rf $FLUIDD_DIR
  mkdir $FLUIDD_DIR && cd $FLUIDD_DIR
  status_msg "Downloading Fluidd $FLUIDD_VERSION ..."
  wget $FLUIDD_DL_URL && ok_msg "Download complete!"

  ### extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"

  ### delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!"
}

set_upstream_nginx_cfg(){
  get_date
  ### backup existing nginx configs
  [ ! -d "$BACKUP_DIR/nginx_cfg" ] && mkdir -p "$BACKUP_DIR/nginx_cfg"
  [ -f "$NGINX_CONFD/upstreams.conf" ] && sudo mv "$NGINX_CONFD/upstreams.conf" "$BACKUP_DIR/nginx_cfg/${current_date}_upstreams.conf"
  [ -f "$NGINX_CONFD/common_vars.conf" ] && sudo mv "$NGINX_CONFD/common_vars.conf" "$BACKUP_DIR/nginx_cfg/${current_date}_common_vars.conf"
  ### transfer ownership of backed up files from root to ${USER}
  for log in $(ls "$BACKUP_DIR/nginx_cfg"); do
    sudo chown ${USER} "$BACKUP_DIR/nginx_cfg/$log"
  done
  ### copy nginx configs to target destination
  if [ ! -f "$NGINX_CONFD/upstreams.conf" ]; then
    sudo cp "${SRCDIR}/kiauh/resources/upstreams.conf" "$NGINX_CONFD"
  fi
  if [ ! -f "$NGINX_CONFD/common_vars.conf" ]; then
    sudo cp "${SRCDIR}/kiauh/resources/common_vars.conf" "$NGINX_CONFD"
  fi
}

fetch_webui_ports(){
  ### read listen ports from possible installed interfaces
  ### and write them to ~/.kiauh.ini
  WEBIFS=(mainsail fluidd octoprint dwc2)
  for interface in "${WEBIFS[@]}"; do
    if [ -f "/etc/nginx/sites-available/${interface}" ]; then
      port=$(grep -E "listen" /etc/nginx/sites-available/$interface | head -1 | sed 's/^\s*//' | sed 's/;$//' | cut -d" " -f2)
      if [ ! -n "$(grep -E "${interface}_port" $INI_FILE)" ]; then
        sed -i '$a'"${interface}_port=${port}" $INI_FILE
      else
        sed -i "/^${interface}_port/d" $INI_FILE
        sed -i '$a'"${interface}_port=${port}" $INI_FILE
      fi
    else
        sed -i "/^${interface}_port/d" $INI_FILE
    fi
  done
}

match_nginx_configs(){
  ### reinstall nginx configs if the amount of upstreams don't match anymore
  source_kiauh_ini
  cfg_updated="false"
  mainsail_nginx_cfg="/etc/nginx/sites-available/mainsail"
  fluidd_nginx_cfg="/etc/nginx/sites-available/fluidd"
  upstreams_webcams=$(grep -E "mjpgstreamer" /etc/nginx/conf.d/upstreams.conf | wc -l)
  status_msg "Checking validity of NGINX configurations ..."
  if [ -e "$mainsail_nginx_cfg" ]; then
    mainsail_webcams=$(grep -E "mjpgstreamer" "$mainsail_nginx_cfg" | wc -l)
  fi
  if [ -e "$fluidd_nginx_cfg" ]; then
    fluidd_webcams=$(grep -E "mjpgstreamer" "$fluidd_nginx_cfg" | wc -l)
  fi
  ### check for outdated upstreams.conf
  if [[ "$upstreams_webcams" -lt "$mainsail_webcams" ]] || [[ "$upstreams_webcams" -lt "$fluidd_webcams" ]]; then
    status_msg "Outdated upstreams.conf found! Updating ..."
    set_upstream_nginx_cfg
    cfg_updated="true"
  fi
  ### check for outdated mainsail config
  if [ -e "$mainsail_nginx_cfg" ]; then
    if [[ "$upstreams_webcams" -gt "$mainsail_webcams" ]]; then
      status_msg "Outdated Mainsail config found! Updating ..."
      sudo rm -f "$mainsail_nginx_cfg"
      sudo cp "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" "$mainsail_nginx_cfg"
      sudo sed -i "s/<<UI>>/mainsail/g" "$mainsail_nginx_cfg"
      sudo sed -i "/root/s/pi/${USER}/" "$mainsail_nginx_cfg"
      sudo sed -i "s/listen\s[0-9]*;/listen $mainsail_port;/" "$mainsail_nginx_cfg"
      sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:$mainsail_port;/" "$mainsail_nginx_cfg"
      cfg_updated="true" && ok_msg "Done!"
    fi
  fi
  ### check for outdated fluidd config
  if [ -e "$fluidd_nginx_cfg" ]; then
    if [[ "$upstreams_webcams" -gt "$fluidd_webcams" ]]; then
      status_msg "Outdated Fluidd config found! Updating ..."
      sudo rm -f "$fluidd_nginx_cfg"
      sudo cp "${SRCDIR}/kiauh/resources/klipper_webui_nginx.cfg" "$fluidd_nginx_cfg"
      sudo sed -i "s/<<UI>>/fluidd/g" "$fluidd_nginx_cfg"
      sudo sed -i "/root/s/pi/${USER}/" "$fluidd_nginx_cfg"
      sudo sed -i "s/listen\s[0-9]*;/listen $fluidd_port;/" "$fluidd_nginx_cfg"
      sudo sed -i "s/listen\s\[\:*\]\:[0-9]*;/listen \[::\]\:$fluidd_port;/" "$fluidd_nginx_cfg"
      cfg_updated="true" && ok_msg "Done!"
    fi
  fi
  ### only restart nginx if configs were updated
  if [ "$cfg_updated" == "true" ]; then
    restart_nginx && unset cfg_updated
  fi
}

process_octoprint_dialog(){
  #ask user to disable octoprint when its service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "|       ${red}!!! WARNING - OctoPrint service found !!!${default}       |"
      hr
      echo -e "|  You might consider disabling the OctoPrint service,  |"
      echo -e "|  since an active OctoPrint service may lead to unex-  |"
      echo -e "|  pected behavior of the Klipper Webinterfaces.        |"
      bottom_border
      read -p "${cyan}###### Do you want to disable OctoPrint now? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Stopping OctoPrint ..."
          do_action_service "stop" "octoprint" && ok_msg "OctoPrint service stopped!"
          status_msg "Disabling OctoPrint ..."
          do_action_service "disable" "octoprint" && ok_msg "OctoPrint service disabled!"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

process_haproxy_lighttpd_services(){
  #handle haproxy service
  if [ "$DISABLE_HAPROXY" = "true" ] || [ "$REMOVE_HAPROXY" = "true" ]; then
    if systemctl is-active haproxy -q; then
      status_msg "Stopping haproxy service ..."
      sudo systemctl stop haproxy && ok_msg "Service stopped!"
    fi

    ### disable haproxy
    if [ "$DISABLE_HAPROXY" = "true" ]; then
      status_msg "Disabling haproxy ..."
      sudo systemctl disable haproxy && ok_msg "Haproxy service disabled!"

      ### remove haproxy
      if [ "$REMOVE_HAPROXY" = "true" ]; then
        status_msg "Removing haproxy ..."
        sudo apt-get remove haproxy -y && sudo update-rc.d -f haproxy remove && ok_msg "Haproxy removed!"
      fi
    fi
  fi

  ### handle lighttpd service
  if [ "$DISABLE_LIGHTTPD" = "true" ] || [ "$REMOVE_LIGHTTPD" = "true" ]; then
    if systemctl is-active lighttpd -q; then
      status_msg "Stopping lighttpd service ..."
      sudo systemctl stop lighttpd && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [ "$DISABLE_LIGHTTPD" = "true" ]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable lighttpd && ok_msg "Lighttpd service disabled!"

      ### remove lighttpd
      if [ "$REMOVE_LIGHTTPD" = "true" ]; then
        status_msg "Removing lighttpd ..."
        sudo apt-get remove lighttpd -y && sudo update-rc.d -f lighttpd remove && ok_msg "Lighttpd removed!"
      fi
    fi
  fi
}

process_haproxy_lighttpd_dialog(){
  #notify user about haproxy or lighttpd services found and possible issues
  if [ "$HAPROXY_FOUND" = "true" ] || [ "$LIGHTTPD_FOUND" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "| ${red}Possibly disruptive/incompatible services found!${default}      |"
      hr
      if [ "$HAPROXY_FOUND" = "true" ]; then
        echo -e "| ● haproxy                                             |"
      fi
      if [ "$LIGHTTPD_FOUND" = "true" ]; then
        echo -e "| ● lighttpd                                            |"
      fi
      hr
      echo -e "| Having those packages installed can lead to unwanted  |"
      echo -e "| behaviour. It is recommend to remove those packages.  |"
      echo -e "|                                                       |"
      echo -e "| 1) Remove packages (recommend)                        |"
      echo -e "| 2) Disable only (may cause issues)                    |"
      echo -e "| ${red}3) Skip this step (not recommended)${default}                   |"
      bottom_border
      read -p "${cyan}###### Please choose:${default} " action
      case "$action" in
        1)
          echo -e "###### > Remove packages"
          if [ "$HAPROXY_FOUND" = "true" ]; then
            DISABLE_HAPROXY="true"
            REMOVE_HAPROXY="true"
          fi
          if [ "$LIGHTTPD_FOUND" = "true" ]; then
            DISABLE_LIGHTTPD="true"
            REMOVE_LIGHTTPD="true"
          fi
          break;;
        2)
          echo -e "###### > Disable only"
          if [ "$HAPROXY_FOUND" = "true" ]; then
            DISABLE_HAPROXY="true"
            REMOVE_HAPROXY="false"
          fi
          if [ "$LIGHTTPD_FOUND" = "true" ]; then
            DISABLE_LIGHTTPD="true"
            REMOVE_LIGHTTPD="false"
          fi
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
