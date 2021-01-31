check_moonraker(){
  status_msg "Checking for Moonraker service ..."
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "moonraker.service")" ] || [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "moonraker-[[:digit:]].service")" ]; then
    moonraker_chk_ok="true"
  else
    moonraker_chk_ok="false"
  fi
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
  ### check if moonraker is already installed
  check_moonraker

  [ $1 == "mainsail" ] && IF_NAME1="Mainsail" && IF_NAME2="Mainsail     "
  [ $1 == "fluidd" ] && IF_NAME1="Fluidd" && IF_NAME2="Fluidd       "

  ### exit mainsail/fluidd setup if moonraker not found
  if [ $moonraker_chk_ok = "false" ]; then
    ERROR_MSG="Moonraker service not found!\n Please install Moonraker first!"
    print_msg && clear_msg && return 0
  else
    ok_msg "Moonraker service found!"
    status_msg "Initializing $IF_NAME1 installation ..."
  fi

  ### check for other enabled web interfaces
  unset SET_LISTEN_PORT
  detect_enabled_sites

  ### check if another site already listens to port 80
  $1_port_check

  ### ask user to install the recommended webinterface macros
  get_user_selection_kiauh_macros "$IF_NAME2"

  ### creating the mainsail/fluidd nginx cfg
  set_nginx_cfg "$1"

  ### copy the kiauh_macros.cfg to the config location
  install_kiauh_macros

  ### install mainsail/fluidd
  $1_setup
}

install_kiauh_macros(){
  source_kiauh_ini
  ### copy kiauh_macros.cfg
  if [ "$ADD_KIAUH_MACROS" = "true" ]; then
    ### create a backup of the config folder
    backup_klipper_config_dir
    ### handle multi printer.cfg
    if ls $klipper_cfg_loc/printer_*  2>/dev/null 1>&2; then
      for config in $(find $klipper_cfg_loc/printer_*/printer.cfg); do
        path=$(echo $config | rev | cut -d"/" -f2- | rev)
        if [ ! -f $path/kiauh_macros.cfg ]; then
          ### copy kiauh_macros.cfg to config location
          cp ${SRCDIR}/kiauh/resources/kiauh_macros.cfg $path
          ok_msg "$path/kiauh_macros.cfg created!"
          ### write the include to the very first line of the printer.cfg
          sed -i "1 i [include kiauh_macros.cfg]" $path/printer.cfg
        fi
      done
    ### handle single printer.cfg
    elif [ -f $klipper_cfg_loc/printer.cfg ] && [ ! -f $klipper_cfg_loc/kiauh_macros.cfg ]; then
      ### copy kiauh_macros.cfg to config location
      cp ${SRCDIR}/kiauh/resources/kiauh_macros.cfg $klipper_cfg_loc
      ok_msg "$klipper_cfg_loc/kiauh_macros.cfg created!"
      ### write the include to the very first line of the printer.cfg
      sed -i "1 i [include kiauh_macros.cfg]" $klipper_cfg_loc/printer.cfg
    fi
    ### restart klipper service to parse the modified printer.cfg
    klipper_service "restart"
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
  MAINSAIL_VERSION=$(curl -s https://api.github.com/repositories/240875926/releases | grep tag_name | cut -d'"' -f4 | head -1)
}

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s https://api.github.com/repositories/295836951/releases | grep tag_name | cut -d'"' -f4 | head -1)
}

mainsail_setup(){
  ### get mainsail download url
  MAINSAIL_DL_URL=$(curl -s https://api.github.com/repositories/240875926/releases | grep browser_download_url | cut -d'"' -f4 | head -1)

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
  if [ $(ls /etc/systemd/system/moonraker* | wc -l) -gt 1 ]; then
    enable_mainsail_remotemode
  fi

  ok_msg "Mainsail installation complete!\n"
}

enable_mainsail_remotemode(){
  rm -f $MAINSAIL_DIR/config.json
  echo -e "{\n    \"remoteMode\":true\n}" >> $MAINSAIL_DIR/config.json
}

fluidd_setup(){
  ### get fluidd download url
  FLUIDD_DL_URL=$(curl -s https://api.github.com/repositories/295836951/releases/latest | grep browser_download_url | cut -d'"' -f4)

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
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Fluidd installation complete!"
  echo
}