check_moonraker(){
  status_msg "Checking for Moonraker service ..."
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "moonraker.service")" ] || [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "moonraker-[[:digit:]].service")" ]; then
    ok_msg "Moonraker service found!"; echo
    MOONRAKER_SERVICE_FOUND="true"
  else
    warn_msg "Moonraker service not found!"
    warn_msg "Please install Moonraker first!"; echo
    MOONRAKER_SERVICE_FOUND="false"
  fi
}

get_user_selection_kiauh_macros(){
  #ask user for webui default macros
  while true; do
    unset ADD_KIAUH_MACROS
    echo
    top_border
    echo -e "| It is recommended to have some important macros to    |"
    echo -e "| have full functionality of the web interface.         |"
    blank_line
    echo -e "| If you don't have those macros, you can choose to     |"
    echo -e "| install suggested default macros now.                 |"
    blank_line
    echo -e "| If unsure which macros are meant, just go ahead and   |"
    echo -e "| select 'Yes'. You can always delete them later.       |"
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

install_mainsail(){
  ### check if moonraker is already installed
  check_moonraker

  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    ### check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites

    ### check if another site already listens to port 80
    mainsail_port_check

    ### ask user to install the recommended webinterface macros
    get_user_selection_kiauh_macros

    ### creating the mainsail nginx cfg
    set_nginx_cfg "mainsail"

    ### copy the kiauh_macros.cfg to the config location
    install_kiauh_macros

    ### install mainsail
    mainsail_setup
  fi
}

install_fluidd(){
  ### check if moonraker is already installed
  check_moonraker

  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    ### check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites

    ### check if another site already listens to port 80
    fluidd_port_check

    ### ask user to install the recommended webinterface macros
    get_user_selection_kiauh_macros

    ### creating the fluidd nginx cfg
    set_nginx_cfg "fluidd"

    ### copy the kiauh_macros.cfg to the config location
    install_kiauh_macros

    ### install fluidd
    fluidd_setup
  fi
}

install_kiauh_macros(){
  source_kiauh_ini
  ### copy kiauh_macros.cfg
  if [ "$ADD_KIAUH_MACROS" = "true" ]; then
    ### create a backup of the config folder
    backup_klipper_config_dir

    ### handle single printer.cfg
    if [ -f $klipper_cfg_loc/printer.cfg ] && [ ! -f $klipper_cfg_loc/kiauh_macros.cfg ]; then
      ### copy kiauh_macros.cfg to config location
      cp ${SRCDIR}/kiauh/resources/kiauh_macros.cfg $klipper_cfg_loc
      ok_msg "$klipper_cfg_loc/kiauh_macros.cfg created!"

      ### write the include to the very first line of the printer.cfg
      sed -i "1 i [include kiauh_macros.cfg]" $klipper_cfg_loc/printer.cfg
    fi

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
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/mainsail_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
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
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/fluidd_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
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
    echo -e "| assigned to one of the other web interfaces!          |"
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
    echo -e "| assigned to one of the other web interfaces!          |"
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
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Mainsail installation complete!"
  echo
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