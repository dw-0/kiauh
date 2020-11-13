install_dwc2(){
  if [ -d $KLIPPER_DIR ]; then
    system_check_dwc2
    #check for other enabled web interfaces
    unset SET_LISTEN_PORT
    detect_enabled_sites
    #ask user for customization
    get_user_selections_dwc2
    #dwc2 main installation
    stop_klipper
    dwc2_setup
    #setup config
    setup_printer_config_dwc2
    #execute customizations
    disable_octoprint
    set_nginx_cfg "dwc2"
    set_hostname
    #after install actions
    restart_klipper
  else
    ERROR_MSG=" Please install Klipper first!\n Skipping..."
  fi
}

system_check_dwc2(){
  status_msg "Initializing DWC2 installation ..."
  #check for existing printer.cfg
  locate_printer_cfg
  if [ -f $PRINTER_CFG ]; then
    PRINTER_CFG_FOUND="true"
  else
    PRINTER_CFG_FOUND="false"
  fi
  #check if octoprint is installed
  if systemctl is-enabled octoprint.service -q 2>/dev/null; then
    OCTOPRINT_ENABLED="true"
  fi
}

get_user_selections_dwc2(){
  #let user choose to install systemd or init.d service
  while true; do
    echo
    top_border
    echo -e "| Do you want to install dwc2-for-klipper-socket as     |"
    echo -e "| 1) Init.d Service (default)                           |"
    echo -e "| 2) Systemd Service                                    |"
    hr
    echo -e "| Please use the appropriate option for your chosen     |"
    echo -e "| Linux distribution. If you are unsure what to select, |"
    echo -e "| please do a research before.                          |"
    hr
    echo -e "| If you run Raspberry Pi OS, both options will work.   |"
    bottom_border
    read -p "${cyan}###### Please choose:${default} " action
    case "$action" in
      1|"")
        echo -e "###### > 1) Init.d"
        INST_DWC2_INITD="true"
        INST_DWC2_SYSTEMD="false"
        break;;
      2)
        echo -e "###### > 1) Systemd"
        INST_DWC2_INITD="false"
        INST_DWC2_SYSTEMD="true"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
  #user selection for printer.cfg
  if [ "$PRINTER_CFG_FOUND" = "false" ]; then
    while true; do
      echo
      top_border
      echo -e "|         ${red}WARNING! - No printer.cfg was found!${default}          |"
      hr
      echo -e "|  KIAUH can create a minimal printer.cfg with only the |"
      echo -e "|  necessary config entries if you wish.                |"
      echo -e "|                                                       |"
      echo -e "|  Please be aware, that this option will ${red}NOT${default} create a  |"
      echo -e "|  fully working printer.cfg for you!                   |"
      bottom_border
      read -p "${cyan}###### Create a default printer.cfg? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          SEL_DEF_CFG="true"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          SEL_DEF_CFG="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
  #ask user to install reverse proxy
  dwc2_reverse_proxy_dialog
  #ask to change hostname
  [ "$SET_NGINX_CFG" = "true" ] && create_custom_hostname
  #ask user to disable octoprint when such installed service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    while true; do
      echo
      warn_msg "OctoPrint service found!"
      echo -e "You might consider disabling the OctoPrint service,"
      echo -e "since an active OctoPrint service may lead to unexpected"
      echo -e "behavior of the DWC2 Webinterface."
      read -p "${cyan}###### Do you want to disable OctoPrint now? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          DISABLE_OPRINT="true"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          DISABLE_OPRINT="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
  status_msg "Installation will start now! Please wait ..."
}

#############################################################
#############################################################

dwc2_setup(){
  #check dependencies
  dep=(git wget gzip tar curl)
  dependency_check
  #get dwc2-for-klipper
  status_msg "Cloning DWC2-for-Klipper-Socket repository ..."
  cd ${HOME} && git clone $DWC2FK_REPO
  ok_msg "DWC2-for-Klipper successfully cloned!"
  #copy installers from kiauh srcdir to dwc-for-klipper-socket
  status_msg "Copy installers to $DWC2FK_DIR"
  cp -r ${SRCDIR}/kiauh/scripts/dwc2-for-klipper-socket-installer $DWC2FK_DIR/scripts
  ok_msg "Done!"
  status_msg "Starting service-installer ..."
  if [ "$INST_DWC2_INITD" = "true" ]; then
    $DWC2FK_DIR/scripts/install-octopi.sh
  elif [ "$INST_DWC2_SYSTEMD" = "true" ]; then
    $DWC2FK_DIR/scripts/install-debian.sh
  fi
  ok_msg "Service installed!"
  #patch /etc/default/klipper to append the uds argument
  patch_klipper_sysfile "dwc2"
  #download Duet Web Control
  download_dwc2_webui
}

download_dwc2_webui(){
  #get Duet Web Control
  GET_DWC2_URL=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4)
  status_msg "Downloading DWC2 Web UI ..."
  [ ! -d $DWC2_DIR ] && mkdir -p $DWC2_DIR
  cd $DWC2_DIR && wget $GET_DWC2_URL
  ok_msg "Download complete!"
  status_msg "Unzipping archive ..."
  unzip -q -o *.zip
  for f_ in $(find . | grep '.gz')
  do
    gunzip -f ${f_}
  done
  ok_msg "Done!"
  status_msg "Writing DWC version to file ..."
  echo $GET_DWC2_URL | cut -d/ -f8 > $DWC2_DIR/version
  ok_msg "Done!"
  status_msg "Do a little cleanup ..."
  rm -rf DuetWebControl-SD.zip
  ok_msg "Done!"
  ok_msg "DWC2 Web UI installed!"
}

#############################################################
#############################################################

setup_printer_config_dwc2(){
  if [ "$PRINTER_CFG_FOUND" = "true" ]; then
    #check printer.cfg for necessary dwc2 entries
    read_printer_cfg "dwc2" && write_printer_cfg
  fi
  if [ "$SEL_DEF_CFG" = "true" ]; then
    status_msg "Creating minimal default printer.cfg ..."
    create_minimal_cfg
    ok_msg "printer.cfg location: '$PRINTER_CFG'"
    ok_msg "Done!"
  fi
}

#############################################################
#############################################################

dwc2_reverse_proxy_dialog(){
  echo
  top_border
  echo -e "|  If you want to have a nicer URL or simply need/want  | "
  echo -e "|  DWC2 to run on port 80 (http's default port) you     | "
  echo -e "|  can set up a reverse proxy to run DWC2 on port 80.   | "
  bottom_border
  while true; do
    read -p "${cyan}###### Do you want to set up a reverse proxy now? (y/N):${default} " yn
    case "$yn" in
      Y|y|Yes|yes)
        dwc2_port_check
        break;;
      N|n|No|no|"")
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

dwc2_port_check(){
  if [ "$DWC2_ENABLED" = "false" ]; then
    if [ "$SITE_ENABLED" = "true" ]; then
      status_msg "Detected other enabled interfaces:"
      [ "$OCTOPRINT_ENABLED" = "true" ] && echo "   ${cyan}● OctoPrint - Port:$OCTOPRINT_PORT${default}"
      [ "$MAINSAIL_ENABLED" = "true" ] && echo "   ${cyan}● Mainsail - Port:$MAINSAIL_PORT${default}"
      [ "$FLUIDD_ENABLED" = "true" ] && echo "   ${cyan}● Fluidd - Port:$FLUIDD_PORT${default}"
      if [ "$MAINSAIL_PORT" = "80" ] || [ "$OCTOPRINT_PORT" = "80" ] || [ "$FLUIDD_PORT" = "80" ]; then
        PORT_80_BLOCKED="true"
        select_dwc2_port
      fi
    else
      DEFAULT_PORT=$(grep listen ${SRCDIR}/kiauh/resources/dwc2_nginx.cfg | head -1 | sed 's/^\s*//' | cut -d" " -f2 | cut -d";" -f1)
      SET_LISTEN_PORT=$DEFAULT_PORT
    fi
    SET_NGINX_CFG="true"
  else
    SET_NGINX_CFG="false"
  fi
}

select_dwc2_port(){
  if [ "$PORT_80_BLOCKED" = "true" ]; then
    echo
    top_border
    echo -e "|                    ${red}!!!WARNING!!!${default}                      |"
    echo -e "| ${red}You need to choose a different port for DWC2!${default}         |"
    echo -e "| ${red}The following web interface is listening at port 80:${default}  |"
    blank_line
    [ "$OCTOPRINT_PORT" = "80" ] && echo "|  ● OctoPrint                                          |"
    [ "$MAINSAIL_PORT" = "80" ] && echo "|  ● Mainsail                                           |"
    [ "$FLUIDD_PORT" = "80" ] && echo "|  ● Fluidd                                             |"
    blank_line
    echo -e "| Make sure you don't choose a port which was already   |"
    echo -e "| assigned to one of the other web interfaces!          |"
    blank_line
    echo -e "| Be aware: there is ${red}NO${default} sanity check for the following  |"
    echo -e "| input. So make sure to choose a valid port!           |"
    bottom_border
    while true; do
      read -p "${cyan}Please enter a new Port:${default} " NEW_PORT
      if [ "$NEW_PORT" != "$MAINSAIL_PORT" ] && [ "$NEW_PORT" != "$FLUIDD_PORT" ] && [ "$NEW_PORT" != "$OCTOPRINT_PORT" ]; then
        echo "Setting port $NEW_PORT for DWC2!"
        SET_LISTEN_PORT=$NEW_PORT
        break
      else
        echo "That port is already taken! Select a different one!"
      fi
    done
  fi
}