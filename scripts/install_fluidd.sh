install_fluidd(){
  if [ "$INST_FLUIDD" = "true" ]; then
    unset SET_LISTEN_PORT
    #check for other enabled web interfaces
    detect_enabled_sites
    #check if another site already listens to port 80
    fluidd_port_check
    #creating the fluidd nginx cfg
    set_nginx_cfg "fluidd"
    fluidd_setup && ok_msg "Fluidd installation complete!"; echo
  fi
}

fluidd_port_check(){
  if [ "$FLUIDD_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      echo "Detected other enabled Interfaces:"
      [ "$MAINSAIL_ENABLED" = "true" ] && echo "${cyan}● Mainsail - Port:$MAINSAIL_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo "${cyan}● DWC2 - Port:$DWC2_PORT${default}"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo "${cyan}● OctoPrint - Port:$OCTOPRINT_PORT${default}"
      if [ "$MAINSAIL_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
      fi
      if [ "$PORT_80_BLOCKED" = "true" ]; then
        [ "$MAINSAIL_PORT" = "80" ] && echo "${cyan}Mainsail${default} already listens on Port 80!"
        [ "$DWC2_PORT" = "80" ] && echo "${cyan}DWC2${default} already listens on Port 80!"
        [ "$OCTOPRINT_PORT" = "80" ] && echo "${cyan}OctoPrint${default} already listens on Port 80!"
        echo "You need to choose a different Port for Fluidd than the above!"
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
  while true; do
    read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
    if [ "$NEW_PORT" != "$MAINSAIL_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
      echo "Setting port $NEW_PORT for Mainsail!"
      SET_LISTEN_PORT=$NEW_PORT
      break
    else
      echo "That port is already taken! Select a different one!"
    fi
  done
}

get_fluidd_ver(){
  FLUIDD_VERSION=$(curl -s https://api.github.com/repositories/295836951/tags | grep name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

fluidd_dl_url(){
  get_fluidd_ver
  FLUIDD_URL=https://github.com/cadriel/fluidd/releases/download/v$FLUIDD_VERSION/fluidd_v$FLUIDD_VERSION.zip
}

fluidd_setup(){
  fluidd_dl_url
  #clean up an existing fluidd folder
  [ -d $FLUIDD_DIR ] && rm -rf $FLUIDD_DIR
  #create fresh fluidd folder and download fluidd
  mkdir $FLUIDD_DIR
  cd $FLUIDD_DIR
  status_msg "Downloading Fluidd $FLUIDD_VERSION ..."
  wget -O fluidd.zip $FLUIDD_URL && status_msg "Extracting archive ..." && unzip -o fluidd.zip && rm fluidd.zip
  ### write fluidd version to file for update check reasons
  echo "$FLUIDD_VERSION" > $FLUIDD_DIR/version
  echo
}