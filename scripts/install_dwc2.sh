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
    write_printer_cfg_dwc2
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
  check_for_folder_dwc2
  #check for existing printer.cfg
  locate_printer_cfg
  if [ ! -z $PRINTER_CFG ]; then
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
  unset INST_SYSTEMD
  unset INST_INITD
  while true; do
    echo
    top_border
    echo -e "| Do you want to install dwc2-for-klipper-socket as     |"
    echo -e "| 1) Init.d Service                                     |"
    echo -e "| 2) Systemd Service                                    |"
    hr
    echo -e "| Please use the appropriate option for your chosen     |"
    echo -e "| Linux distribution. If you are unsure what to select, |"
    echo -e "| please do a research before.                          |"
    hr
    echo -e "| If you are using Raspberry Pi OS, either option 1 or  |"
    echo -e "| 2 will work.                                          |"
    bottom_border
    read -p "${cyan}###### Please choose:${default} " action
    case "$action" in
      1)
        INST_INITD="true"
        INST_SYSTEMD="false"
        break;;
      2)
        INST_INITD="false"
        INST_SYSTEMD="true"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
  #user selection for printer.cfg
  if [ "$PRINTER_CFG_FOUND" = "false" ]; then
    unset SEL_DEF_CFG
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
  #
  setup_printer_config_dwc2
  #ask user to install reverse proxy
  dwc2_reverse_proxy_dialog
  #ask to change hostname
  [ "$SET_NGINX_CFG" = "true" ] && create_custom_hostname
  #ask user to disable octoprint when such installed service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    unset DISABLE_OPRINT
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

check_for_folder_dwc2(){
  #check for needed folder
  if [ ! -d $DWC2_DIR ]; then
    mkdir -p $DWC2_DIR
  fi
}

dwc2_setup(){
  #check dependencies
  dep=(git wget gzip tar curl)
  dependency_check
  #get dwc2-for-klipper
  cd ${HOME}
  status_msg "Cloning DWC2-for-Klipper-Socket repository ..."
  git clone $DWC2FK_REPO
  ok_msg "DWC2-for-Klipper successfully cloned!"
  #copy installers from kiauh srcdir to dwc-for-klipper-socket
  status_msg "Copy installers to $DWC2FK_DIR"
  cp -r ${SRCDIR}/kiauh/scripts/dwc2-for-klipper-socket-installer $DWC2FK_DIR/scripts
  ok_msg "Done!"
  status_msg "Starting service-installer ..."
  if [ "$INST_INITD" = "true" ] && [ "$INST_SYSTEMD" = "false" ]; then
    $DWC2FK_DIR/scripts/install-octopi.sh
  elif [ "$INST_INITD" = "false" ] && [ "$INST_SYSTEMD" = "true" ]; then
    $DWC2FK_DIR/scripts/install-debian.sh
  fi
  ok_msg "Service installed!"
  #patch /etc/default/klipper to append the uds argument
  patch_klipper_sysfile_dwc2
  #download Duet Web Control
  download_dwc2_webui
}

patch_klipper_sysfile_dwc2(){
  status_msg "Checking /etc/default/klipper for necessary entries ..."
  #patching new UDS argument to /etc/default/klipper
  if ! grep -q -- "-a /tmp/klippy_uds" $KLIPPER_SERVICE2; then
    status_msg "Patching unix domain socket to /etc/default/klipper ..."
    #append the new argument to /tmp/klippy.log argument
    sudo sed -i "/KLIPPY_ARGS/s/\.log/\.log -a \/tmp\/klippy_uds/" $KLIPPER_SERVICE2
    ok_msg "Patching done!"
  else
    ok_msg "No patching needed!"
  fi
  ok_msg "Check complete!"
  echo
}

download_dwc2_webui(){
  #get Duet Web Control
  GET_DWC2_URL=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4)
  cd $DWC2_DIR
  status_msg "Downloading DWC2 Web UI ..."
  wget $GET_DWC2_URL
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
    backup_printer_cfg
    #check printer.cfg for necessary dwc2 entries
    read_printer_cfg_dwc2
  fi
  if [ "$SEL_DEF_CFG" = "true" ]; then
    create_default_dwc2_printer_cfg
    locate_printer_cfg
  fi
}

read_printer_cfg_dwc2(){
  unset SC_ENTRY
  SC="#*# <---------------------- SAVE_CONFIG ---------------------->"
  if [ ! $(grep '^\[virtual_sdcard\]$' $PRINTER_CFG) ]; then
    VSD="false"
  fi
  #check for a SAVE_CONFIG entry
  if [[ $(grep "$SC" $PRINTER_CFG) ]]; then
    SC_LINE=$(grep -n "$SC" $PRINTER_CFG | cut -d ":" -f1)
    PRE_SC_LINE=$(expr $SC_LINE - 1)
    SC_ENTRY="true"
  else
    SC_ENTRY="false"
  fi
}

write_printer_cfg_dwc2(){
  unset write_entries
  if [ "$VSD" = "false" ]; then
    write_entries+=("[virtual_sdcard]\npath: ~/sdcard")
  fi
  if [ "${#write_entries[@]}" != "0" ]; then
    write_entries+=("\\\n############################\n##### CREATED BY KIAUH #####\n############################")
    write_entries=("############################\n" "${write_entries[@]}")
  fi
  #execute writing
  status_msg "Writing to printer.cfg ..."
  if [ "$SC_ENTRY" = "true" ]; then
    PRE_SC_LINE="$(expr $SC_LINE - 1)a"
    for entry in "${write_entries[@]}"
    do
      sed -i "$PRE_SC_LINE $entry" $PRINTER_CFG
    done
  fi
  if [ "$SC_ENTRY" = "false" ]; then
    LINE_COUNT="$(wc -l < $PRINTER_CFG)a"
    for entry in "${write_entries[@]}"
    do
      sed -i "$LINE_COUNT $entry" $PRINTER_CFG
    done
  fi
  ok_msg "Done!"
}

create_default_dwc2_printer_cfg(){
  #create default config
  if [ "$PRINTER_CFG_FOUND" = "false" ] && [ "$SEL_DEF_CFG" = "true" ]; then
    touch $PRINTER_CFG
    cat <<DEFAULT_DWC2_CFG >> $PRINTER_CFG
##########################
### CREATED WITH KIAUH ###
##########################
[printer]
kinematics: cartesian
max_velocity: 300
max_accel: 3000
max_z_velocity: 5
max_z_accel: 100

[virtual_sdcard]
path: ~/sdcard

##########################
DEFAULT_DWC2_CFG
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