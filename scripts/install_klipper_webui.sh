check_moonraker(){
  status_msg "Checking for Moonraker service ..."
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "moonraker.service")" ]; then
    ok_msg "Moonraker service found!"; echo
    MOONRAKER_SERVICE_FOUND="true"
  else
    warn_msg "Moonraker service not found!"
    warn_msg "Please install Moonraker first!"; echo
    MOONRAKER_SERVICE_FOUND="false"
  fi
}

get_user_selection_webui(){
  #ask user for webui default macros
  while true; do
    unset ADD_WEBUI_MACROS
    echo
    top_border
    echo -e "| It is recommended to have some important macros to    |"
    echo -e "| have full functionality of the web interface.         |"
    blank_line
    echo -e "| If you do not have such macros, you can choose to     |"
    echo -e "| install the suggested default macros now.             |"
    bottom_border
    read -p "${cyan}###### Add the recommended macros? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        ADD_WEBUI_MACROS="true"
        break;;
      N|n|No|no)
        echo -e "###### > No"
        ADD_WEBUI_MACROS="false"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

install_mainsail(){
  get_user_selection_webui
  #check if moonraker is already installed
  check_moonraker
  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    #check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites
    #check if another site already listens to port 80
    mainsail_port_check
    #creating the mainsail nginx cfg
    set_nginx_cfg "mainsail"
    #test_nginx "$SET_LISTEN_PORT"
    locate_printer_cfg && read_printer_cfg "mainsail"
    install_webui_macros
    mainsail_setup
  fi
}

install_fluidd(){
  get_user_selection_webui
  #check if moonraker is already installed
  check_moonraker
  if [ "$MOONRAKER_SERVICE_FOUND" = "true" ]; then
    #check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites
    #check if another site already listens to port 80
    fluidd_port_check
    #creating the fluidd nginx cfg
    set_nginx_cfg "fluidd"
    #test_nginx "$SET_LISTEN_PORT"
    locate_printer_cfg && read_printer_cfg "fluidd"
    install_webui_macros
    fluidd_setup
  fi
}

install_webui_macros(){
  #copy webui_macros.cfg
  if [ "$ADD_WEBUI_MACROS" = "true" ]; then
    status_msg "Create webui_macros.cfg ..."
    if [ ! -f ${HOME}/klipper_config/webui_macros.cfg ]; then
      cp ${HOME}/kiauh/resources/webui_macros.cfg ${HOME}/klipper_config
      ok_msg "File created!"
    else
      warn_msg "File already exists! Skipping ..."
    fi
  fi
  write_printer_cfg
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
  MAINSAIL_VERSION=$(curl -s https://api.github.com/repositories/240875926/releases | grep tag_name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s https://api.github.com/repositories/295836951/releases | grep tag_name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

mainsail_setup(){
  #get mainsail download url
  MAINSAIL_DL_URL=$(curl -s https://api.github.com/repositories/240875926/releases | grep browser_download_url | cut -d'"' -f4 | head -1)
  #clean up an existing mainsail folder
  [ -d $MAINSAIL_DIR ] && rm -rf $MAINSAIL_DIR
  #create fresh mainsail folder and download mainsail
  mkdir $MAINSAIL_DIR && cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail $MAINSAIL_VERSION ..."
  wget $MAINSAIL_DL_URL && ok_msg "Download complete!"
  #extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"
  ### write mainsail version to file for update check reasons
  status_msg "Writing Mainsail version to file ..."
  get_mainsail_ver && echo "$MAINSAIL_VERSION" > $MAINSAIL_DIR/version && ok_msg "Done!"
  #delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Mainsail installation complete!"
  echo
}

fluidd_setup(){
  #get fluidd download url
  FLUIDD_DL_URL=$(curl -s https://api.github.com/repositories/295836951/releases/latest | grep browser_download_url | cut -d'"' -f4)
  #clean up an existing fluidd folder
  [ -d $FLUIDD_DIR ] && rm -rf $FLUIDD_DIR
  #create fresh fluidd folder and download fluidd
  mkdir $FLUIDD_DIR && cd $FLUIDD_DIR
  status_msg "Downloading Fluidd $FLUIDD_VERSION ..."
  wget $FLUIDD_DL_URL && ok_msg "Download complete!"
  #extract archive
  status_msg "Extracting archive ..."
  unzip -q -o *.zip && ok_msg "Done!"
  #write fluidd version to file for update check reasons
  status_msg "Writing Fluidd version to file ..."
  get_fluidd_ver && echo $FLUIDD_VERSION > $FLUIDD_DIR/version && ok_msg "Done!"
  #patch moonraker.conf to apply cors domains if needed
  backup_moonraker_conf
  patch_moonraker
  #delete downloaded zip
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Fluidd installation complete!"
  echo
}

patch_moonraker(){
  status_msg "Patching moonraker.conf ..."
  mr_conf=${HOME}/moonraker.conf
  # remove the now deprecated enable_cors option from moonraker.conf if it still exists
  if [ "$(grep "^enable_cors:" $mr_conf)" ]; then
    line="$(grep -n "^enable_cors:" ~/moonraker.conf | cut -d":" -f1)d"
    sed -i "$line" $mr_conf && mr_restart="true"
  fi
  # looking for a cors_domain entry in moonraker.conf
  if [ ! "$(grep "^cors_domains:$" $mr_conf)" ]; then
    #find trusted_clients line number and subtract one, to insert cors_domains later
    line="$(grep -n "^trusted_clients:$" $mr_conf | cut -d":" -f1)i"
    sed -i "$line cors_domains:" $mr_conf && mr_restart="true"
  fi
  if [ "$(grep "^cors_domains:$" $mr_conf)" ]; then
    hostname=$(hostname -I | cut -d" " -f1)
    url1="\ \ \ \ http://*.local"
    url2="\ \ \ \ http://app.fluidd.xyz"
    url3="\ \ \ \ https://app.fluidd.xyz"
    url4="\ \ \ \ http://$hostname:*"
    #find cors_domains line number and add one, to insert urls later
    line="$(expr $(grep -n "cors_domains:" $mr_conf | cut -d":" -f1) + 1)i"
    [ ! "$(grep -E '^\s+http:\/\/\*\.local$' $mr_conf)" ] && sed -i "$line $url1" $mr_conf && mr_restart="true"
    [ ! "$(grep -E '^\s+http:\/\/app\.fluidd\.xyz$' $mr_conf)" ] && sed -i "$line $url2" $mr_conf && mr_restart="true"
    [ ! "$(grep -E '^\s+https:\/\/app\.fluidd\.xyz$' $mr_conf)" ] && sed -i "$line $url3" $mr_conf && mr_restart="true"
    [ ! "$(grep -E '^\s+http:\/\/([0-9]{1,3}\.){3}[0-9]{1,3}' $mr_conf)" ] && sed -i "$line $url4" $mr_conf && mr_restart="true"
  fi
  #restart moonraker service if mr_restart was set to true
  if [[ $mr_restart == "true" ]]; then
    ok_msg "Patching done!" && restart_moonraker
  else
    ok_msg "No patching was needed!"
  fi
}