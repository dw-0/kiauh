install_mainsail(){
  if [ "$INST_MAINSAIL" = "true" ]; then
    unset SET_LISTEN_PORT
    #check for other enabled web interfaces
    detect_enabled_sites
    #check if another site already listens to port 80
    mainsail_port_check
    #creating the mainsail nginx cfg
    set_nginx_cfg "mainsail"
    mainsail_setup && ok_msg "Mainsail installation complete!"; echo
  fi
}

mainsail_port_check(){
  if [ "$MAINSAIL_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      echo "Detected other enabled Interfaces:"
      [ "$FLUIDD_ENABLED" = "true" ] && echo "${cyan}● Fluidd - Port:$FLUIDD_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo "${cyan}● DWC2 - Port:$DWC2_PORT${default}"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo "${cyan}● OctoPrint - Port:$OCTOPRINT_PORT${default}"
      if [ "$FLUIDD_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
      fi
      if [ "$PORT_80_BLOCKED" = "true" ]; then
        [ "$FLUIDD_PORT" = "80" ] && echo "${cyan}Fluidd${default} already listens on Port 80!"
        [ "$DWC2_PORT" = "80" ] && echo "${cyan}DWC2${default} already listens on Port 80!"
        [ "$OCTOPRINT_PORT" = "80" ] && echo "${cyan}OctoPrint${default} already listens on Port 80!"
        echo "You need to choose a different Port for Mainsail than the above!"
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

select_mainsail_port(){
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
}

get_mainsail_ver(){
  MAINSAIL_VERSION=$(curl -s https://api.github.com/repositories/240875926/tags | grep name | cut -d'"' -f4 | cut -d"v" -f2 | head -1)
}

mainsail_dl_url(){
  get_mainsail_ver
  MAINSAIL_URL=https://github.com/meteyou/mainsail/releases/download/v$MAINSAIL_VERSION/mainsail-beta-$MAINSAIL_VERSION.zip
}

mainsail_setup(){
  mainsail_dl_url
  #clean up an existing mainsail folder
  [ -d $MAINSAIL_DIR ] && rm -rf $MAINSAIL_DIR
  #create fresh mainsail folder and download mainsail
  mkdir $MAINSAIL_DIR && cd $MAINSAIL_DIR
  status_msg "Downloading Mainsail v$MAINSAIL_VERSION ..."
  wget -O mainsail.zip $MAINSAIL_URL && status_msg "Extracting archive ..." && unzip -o mainsail.zip && rm mainsail.zip
  ### write mainsail version to file for update check reasons
  echo "$MAINSAIL_VERSION" > $MAINSAIL_DIR/version
  echo
}