install_octoprint(){
  #check for other enabled web interfaces
  unset SET_LISTEN_PORT
  detect_enabled_sites
  #ask user for customization
  get_user_selections_octoprint
  #octoprint main installation
  octoprint_dependencies
  octoprint_setup
  add_groups
  configure_autostart
  add_reboot_permission
  create_config_yaml
  #execute customizations
  set_nginx_cfg "octoprint"
  set_hostname
  #after install actions
  load_octoprint_server
}

get_user_selections_octoprint(){
  status_msg "Initializing OctoPrint installation ..."
  #ask user to set a reverse proxy
  octoprint_reverse_proxy_dialog
  #ask to change hostname
  [ "$SET_NGINX_CFG" = "true" ] && create_custom_hostname
  status_msg "Installation will start now! Please wait ..."
}

octoprint_dependencies(){
  dep=(
    git
    wget
    python-pip
    python-dev
    libyaml-dev
    build-essential
    python-setuptools
    python-virtualenv
    )
  dependency_check
}

octoprint_setup(){
  if [ ! -d $OCTOPRINT_DIR ];then
    status_msg "Create OctoPrint directory ..."
    mkdir -p $OCTOPRINT_DIR && ok_msg "Directory created!"
  fi
  cd $OCTOPRINT_DIR
  #create the virtualenv
  status_msg "Set up virtualenv ..."
  virtualenv venv
  source venv/bin/activate
  #install octoprint with pip
  status_msg "Download and install OctoPrint ..."
  pip install pip --upgrade
  pip install --no-cache-dir octoprint
  ok_msg "Download complete!"
  #leave virtualenv
  deactivate
}

add_groups(){
  if [ ! "$(groups | grep tty)" ]; then
    status_msg "Adding user '${USER}' to group 'tty' ..."
    sudo usermod -a -G tty ${USER} && ok_msg "Done!"
  fi
  if [ ! "$(groups | grep dialout)" ]; then
    status_msg "Adding user '${USER}' to group 'dialout' ..."
    sudo usermod -a -G dialout ${USER} && ok_msg "Done!"
  fi
}

configure_autostart(){
  USER=$(whoami)
  cd $OCTOPRINT_DIR
  status_msg "Downloading files ..."
  wget https://github.com/foosel/OctoPrint/raw/master/scripts/octoprint.init
  wget https://github.com/foosel/OctoPrint/raw/master/scripts/octoprint.default
  ok_msg "Files downloaded successfully!"
  #make necessary changes in default file
  status_msg "Configure OctoPrint Service ..."
  DEFAULT_FILE=$OCTOPRINT_DIR/octoprint.default
  sed -i "s/pi/$USER/g" $DEFAULT_FILE
  sed -i "s/#BASEDIR=/BASEDIR=/" $DEFAULT_FILE
  sed -i "s/#CONFIGFILE=/CONFIGFILE=/" $DEFAULT_FILE
  sed -i "s/#DAEMON=/DAEMON=/" $DEFAULT_FILE
  #move files to correct location
  sudo mv octoprint.init $OCTOPRINT_SERVICE1
  sudo mv octoprint.default $OCTOPRINT_SERVICE2
  #make file in init.d executable
  sudo chmod +x $OCTOPRINT_SERVICE1
  status_msg "Reload systemd configuration files"
  sudo update-rc.d octoprint defaults
  sudo systemctl daemon-reload
  ok_msg "Configuration complete!"
  ok_msg "OctoPrint installed!"
}

add_reboot_permission(){
  USER=$(whoami)
  #create a backup when file already exists
  if [ -f /etc/sudoers.d/octoprint-shutdown ]; then
    sudo mv /etc/sudoers.d/octoprint-shutdown /etc/sudoers.d/octoprint-shutdown.old
  fi
  #create new permission file
  status_msg "Add reboot permission to user '$USER' ..."
  cd $OCTOPRINT_DIR
  echo "$USER ALL=NOPASSWD: /sbin/shutdown" > octoprint-shutdown
  sudo chown 0 octoprint-shutdown
  sudo mv octoprint-shutdown /etc/sudoers.d/octoprint-shutdown
  ok_msg "Permission set!"
  sleep 2
}

octoprint_reverse_proxy_dialog(){
  echo
  top_border
  echo -e "|  If you want to have nicer URLs or simply need        | "
  echo -e "|  OctoPrint to run on port 80 (http's default port)    | "
  echo -e "|  due to some network restrictions, you can set up a   | "
  echo -e "|  reverse proxy instead of configuring OctoPrint to    | "
  echo -e "|  run on port 80.                                      | "
  bottom_border
  while true; do
    echo -e "${cyan}"
    read -p "###### Do you want to set up a reverse proxy now? (y/N): " yn
    echo -e "${default}"
    case "$yn" in
      Y|y|Yes|yes)
        octoprint_port_check
        break;;
      N|n|No|no|"")
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

octoprint_port_check(){
  if [ "$OCTOPRINT_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      echo "Detected other enabled Interfaces:"
      [ "$MAINSAIL_ENABLED" = "true" ] && echo "${cyan}● Mainsail - Port:$MAINSAIL_PORT${default}"
      [ "$FLUIDD_ENABLED" = "true" ] && echo "${cyan}● Fluidd - Port:$FLUIDD_PORT${default}"
      [ "$DWC2_ENABLED" = "true" ] && echo "${cyan}● DWC2 - Port:$DWC2_PORT${default}"
      if [ "$MAINSAIL_PORT" = "80" ] || [ "$DWC2_PORT" = "80" ] || [ "$FLUIDD_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
      fi
      if [ "$PORT_80_BLOCKED" = "true" ]; then
        [ "$MAINSAIL_PORT" = "80" ] && echo "${cyan}Mainsail${default} already listens on Port 80!"
        [ "$FLUIDD_PORT" = "80" ] && echo "${cyan}Fluidd${default} already listens on Port 80!"
        [ "$DWC2_PORT" = "80" ] && echo "${cyan}DWC2${default} already listens on Port 80!"
        echo "You need to choose a different Port for OctoPrint than the above!"
        select_octoprint_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/octoprint_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

select_octoprint_port(){
  while true; do
    read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
    if [ "$NEW_PORT" != "$MAINSAIL_PORT" ] && [ "$NEW_PORT" != "$DWC2_PORT" ] && [ "$NEW_PORT" != "$FLUIDD_PORT" ]; then
      echo "Setting port $NEW_PORT for OctoPrint!"
      SET_LISTEN_PORT=$NEW_PORT
      break
    else
      echo "That port is already taken! Select a different one!"
    fi
  done
}

create_config_yaml(){
  if [ ! -d $OCTOPRINT_CFG_DIR ]; then
    status_msg "Creating config.yaml ..."
    mkdir $OCTOPRINT_CFG_DIR
    cp ${HOME}/kiauh/resources/octoprint_config.cfg $OCTOPRINT_CFG_DIR/config.yaml
    ok_msg "Config created!"
  fi
}

load_octoprint_server(){
  start_octoprint
  #create an octoprint.log symlink in home-dir just for convenience
  if [ ! -e ${HOME}/octoprint.log ]; then
      status_msg "Creating octoprint.log Symlink ..."
      ln -s ${HOME}/.octoprint/logs/octoprint.log ${HOME}/octoprint.log && ok_msg "Symlink created!"
  fi
  ok_msg "OctoPrint is now running on:"
  ok_msg "$(hostname -I | cut -d " " -f1):5000 or"
  ok_msg "http://localhost:5000"; echo
}