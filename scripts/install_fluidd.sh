install_fluidd(){
  if [ "$INST_FLUIDD" = "true" ]; then
    unset SET_LISTEN_PORT
    #check for other enabled web interfaces
    detect_enabled_sites
    #check if another site already listens to port 80
    fluidd_port_check
    #creating the fluidd nginx cfg
    set_nginx_cfg "fluidd"
    fluidd_setup
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

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s https://api.github.com/repositories/295836951/releases/latest | grep tag_name | cut -d'"' -f4 | cut -d"v" -f2)
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
  status_msg "Unzipping archive ..."
  unzip -q -o *.zip && ok_msg "Done!"
  #write fluidd version to file for update check reasons
  status_msg "Writing Fluidd version to file ..."
  get_fluidd_ver && echo $FLUIDD_VERSION > $FLUIDD_DIR/version && ok_msg "Done!"
  #delete downloaded zip
  status_msg "Do a little cleanup ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Fluidd installation complete!"
  echo
}