install_dwc2(){
  if [ -d $KLIPPER_DIR ]; then
    system_check_dwc2
    #ask user for customization
    get_user_selections_dwc2
    #dwc2 main installation
    tornado_setup
    dwc2_setup
    #setup config
    write_printer_cfg_dwc2
    write_custom_printer_cfg_dwc2
    #execute customizations
    disable_octoprint
    create_reverse_proxy "dwc2"
    set_hostname
    #after install actions
    restart_klipper
  else
    ERROR_MSG=" Please install Klipper first!\n Skipping..."
  fi
}

system_check_dwc2(){
  status_msg "Initializing DWC2 installation ..."
  stop_klipper
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
    unset OCTOPRINT_ENABLED
    OCTOPRINT_ENABLED="true"
  fi
}

get_user_selections_dwc2(){
  #user selection for printer.cfg
  if [ "$PRINTER_CFG_FOUND" = "false" ]; then
    unset SEL_DEF_CFG
    unset SEL_CUS_CFG
    while true; do
      echo
      top_border
      echo -e "|         ${red}WARNING! - No printer.cfg was found!${default}          |"
      hr
      echo -e "|  You can now either select to create a printer.cfg    |"
      echo -e "|  with the default entries (1), customize the settings |"
      echo -e "|  before writing them (2) or you can skip the creation |"
      echo -e "|  of a printer.cfg at all.                             |"
      echo -e "|                                                       |"
      echo -e "|  Please keep in mind that DWC2 will ONLY load if you  |"
      echo -e "|  have a correctly defined printer.cfg. Any missing    |"
      echo -e "|  option or error will prevent DWC2 from loading and   |"
      echo -e "|  you need to check klippy.log to resolve the error.   |"
      echo -e "|                                                       |"
      echo -e "|  ${red}Neither option 1 or 2 of this script will create a   |"
      echo -e "|  fully working printer.cfg for you!${default}                   |"
      hr
      echo -e "|  1) [Create default configuration]                    |"
      echo -e "|  2) [Create custom configuration]                     |"
      echo -e "|  3) ${red}[Skip]${default}                                            |"
      bottom_border
      read -p "${cyan}###### Please select:${default} " choice
      case "$choice" in
        1)
          echo -e "###### > Create default configuration"
          SEL_DEF_CFG="true"
          SEL_CUS_CFG="false"
          break;;
        2)
          echo -e "###### > Create custom configuration"
          SEL_DEF_CFG="false"
          SEL_CUS_CFG="true"
          break;;
        3)
          echo -e "###### > Skip"
          SEL_DEF_CFG="false"
          SEL_CUS_CFG="false"
          echo "${red}Skipping ...${default}"; break;;
      esac
      break
    done
  fi
  #
  setup_printer_config_dwc2
  #ask user to install reverse proxy
  dwc2_reverse_proxy_dialog
  #ask to change hostname
  if [ "$SET_REVERSE_PROXY" = "true" ]; then
    create_custom_hostname
  fi
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
          DISABLE_OPRINT="true";;
        N|n|No|no)
          echo -e "###### > No"
          DISABLE_OPRINT="false";;
      esac
      break
    done
  fi
  status_msg "Installation will start now! Please wait ..."
}

#############################################################
#############################################################

check_for_folder_dwc2(){
  #check for needed folder
  if [ ! -d $DWC2_DIR/web ]; then
    mkdir -p $DWC2_DIR/web
  fi
}

tornado_setup(){
  if [ "$(cd $KLIPPY_ENV_DIR/bin/ && $_/pip list 2>/dev/null | grep "tornado" | cut -d" " -f9)" = "5.1.1" ]; then
    ok_msg "Tornado 5.1.1 is already installed! Continue..."
  else
    status_msg "Installing Tornado 5.1.1 ..."
    cd ${HOME}
    PYTHONDIR="${HOME}/klippy-env"
    virtualenv ${PYTHONDIR}
    ${PYTHONDIR}/bin/pip install tornado==5.1.1
    ok_msg "Tornado 5.1.1 successfully installed!"
  fi
}

dwc2_setup(){
  #check dependencies
  dep=(git wget gzip tar curl)
  dependency_check
  #get dwc2-for-klipper
  cd ${HOME}
  status_msg "Cloning DWC2-for-Klipper repository ..."
  git clone $DWC2FK_REPO
  ok_msg "DWC2-for-Klipper successfully cloned!"
  #create a web_dwc2.py symlink if not already existing
  if [ -d $KLIPPER_DIR/klippy/extras ] && [ ! -e $KLIPPER_DIR/klippy/extras/web_dwc2.py ]; then
    status_msg "Creating web_dwc2.py Symlink ..."
    ln -s $DWC2FK_DIR/web_dwc2.py $KLIPPER_DIR/klippy/extras/web_dwc2.py
    ok_msg "Symlink created!"
  fi
  #get Duet Web Control
  GET_DWC2_URL=`curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4`
  cd $DWC2_DIR/web
  status_msg "Downloading DWC2 Web UI ..."
  wget -q $GET_DWC2_URL
  ok_msg "Download complete!"
  status_msg "Unzipping archive ..."
  unzip -q -o *.zip
  for f_ in $(find . | grep '.gz')
  do
    gunzip -f ${f_}
  done
  ok_msg "Done!"
  status_msg "Writing DWC version to file ..."
  echo $GET_DWC2_URL | cut -d/ -f8 > $DWC2_DIR/web/version
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
  if [ "$SEL_CUS_CFG" = "true" ]; then
    #get user input for custom config
    create_custom_dwc2_printer_cfg
    locate_printer_cfg
  fi
}

read_printer_cfg_dwc2(){
  unset SC_ENTRY
  SC="#*# <---------------------- SAVE_CONFIG ---------------------->"
  if [ ! $(grep '^\[virtual_sdcard\]$' $PRINTER_CFG) ]; then
    VSD="false"
  fi
  if [ ! $(grep '^\[web_dwc2\]$' $PRINTER_CFG) ]; then
    WEB_DWC2="false"
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
  if [ "$WEB_DWC2" = "false" ]; then
    write_entries+=("[web_dwc2]\nprinter_name: my_printer\nlisten_adress: 0.0.0.0\nlisten_port: 4750\nweb_path: dwc2/web")
  fi
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

write_custom_printer_cfg_dwc2(){
  #create custom config
  if [ "$PRINTER_CFG_FOUND" = "false" ] && [ "$CONFIRM_CUSTOM_CFG" = "true" ]; then
    touch $PRINTER_CFG
    echo -e "$DWC2_CFG" >> $PRINTER_CFG
  fi
}

create_default_dwc2_printer_cfg(){
  #create default config
  if [ "$PRINTER_CFG_FOUND" = "false" ] && [ "$SEL_CUS_CFG" = "true" ]; then
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

[web_dwc2]
printer_name: my_printer
listen_adress: 0.0.0.0
listen_port: 4750
web_path: dwc2/web
##########################
DEFAULT_DWC2_CFG
  fi
}

#############################################################
#############################################################

create_custom_dwc2_printer_cfg(){
  echo
  top_border
  echo -e "|  Please fill in custom values for the following       |"
  echo -e "|  configuration options. If you are unsure what to put |"
  echo -e "|  in, keep the pre-entered values.                     |"
  bottom_border
  echo -e "${cyan}"
  read -e -p "Printer name: " -i "my_printer" PRINTER_NAME
  read -e -p "Listen adress: " -i "0.0.0.0" LISTEN_ADRESS
  read -e -p "Listen port: " -i "4750" LISTEN_PORT
  read -e -p "Web path: " -i "dwc2/web" WEB_PATH
  echo -e "${default}"
  DWC2_CFG=$(cat <<DWC2
##########################
### CREATED WITH KIAUH ###
##########################
[virtual_sdcard]
path: ~/sdcard

[web_dwc2]
printer_name: $PRINTER_NAME
listen_adress: $LISTEN_ADRESS
listen_port: $LISTEN_PORT
web_path: $WEB_PATH
##########################
DWC2
)
  echo "The following lines will be written:"
  echo -e "$DWC2_CFG"
  while true; do
    echo
    read -p "${cyan}###### Confirm (Y) or start over (n)? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        CONFIRM_CUSTOM_CFG="true"
        break;;
      N|n|No|no)
        CONFIRM_CUSTOM_CFG="false"
        create_custom_dwc2_printer_cfg
        break;;
    esac
  done
}

#############################################################
#############################################################

dwc2_reverse_proxy_dialog(){
  unset SET_REVERSE_PROXY
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
        SET_REVERSE_PROXY="true"
        break;;
      N|n|No|no|"")
        SET_REVERSE_PROXY="false"
        break;;
    esac
  done
}