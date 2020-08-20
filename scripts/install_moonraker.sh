install_moonraker(){
  system_check_moonraker
  #ask user for customization
  get_user_selections_moonraker
  #moonraker main installation
  moonraker_setup
  check_for_folder
  #setup configs
  setup_printer_config
  setup_moonraker_conf
  #execute customizations
  write_custom_trusted_clients
  symlink_moonraker_log
  install_mainsail
  set_hostname
  #after install actions
  restart_moonraker
  restart_klipper
  test_api
}

system_check_moonraker(){
  status_msg "Initializing Moonraker installation ..."
  #check for existing printer.cfg and for the location
  if [ ! -e ${HOME}/printer.cfg ] && [ ! -e ${HOME}/klipper_config/printer.cfg ]; then
    PRINTER_CFG_FOUND="false"
  else
    if [ -f ${HOME}/printer.cfg ]; then
      PRINTER_CFG_FOUND="true"
      PRINTER_CFG_LOC="${HOME}/printer.cfg"
    fi
    if [ -f ${HOME}/klipper_config/printer.cfg ]; then
      PRINTER_CFG_FOUND="true"
      PRINTER_CFG_LOC="${HOME}/klipper_config/printer.cfg"
    fi
  fi
  #check for existing moonraker.log symlink in /klipper_config
  if [ ! -e ${HOME}/klipper_config/moonraker.log ]; then
    MOONRAKER_SL_FOUND="false"
  else
    MOONRAKER_SL_FOUND="true"
  fi
  #check for existing moonraker.conf
  if [ ! -f ${HOME}/moonraker.conf ]; then
    MOONRAKER_CONF_FOUND="false"
  else
    MOONRAKER_CONF_FOUND="true"
  fi
}

get_user_selections_moonraker(){
  #ask if moonraker only or moonraker + mainsail
  while true; do
    echo
    top_border
      echo -e "| Do you want to install Moonraker and Mainsail?        |"
      echo -e "| You can choose to install Moonraker only by answering |"
      echo -e "| with 'No'.                                            |"
      hr
      echo -e "| If you select 'Yes' please be aware that an existing  |"
      echo -e "| Mainsail installation will then be overwritten!       |"
    bottom_border
    read -p "${cyan}###### Install Moonraker + Mainsail? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        INST_MAINSAIL="true";;
      N|n|No|no)
        echo -e "###### > No"
        INST_MAINSAIL="false";;
    esac
    break
  done
  #ask to change hostname if mainsail should be installed as well
  if [ "$INST_MAINSAIL" = "true" ]; then
    create_custom_hostname
  fi
  #user selection for printer.cfg
  if [ "$PRINTER_CFG_FOUND" = "false" ]; then
    while true; do
      echo
      warn_msg "No printer.cfg found!"
      read -p "${cyan}###### Create a default printer.cfg? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          SEL_DEF_CFG="true";;
        N|n|No|no)
          echo -e "###### > No"
          SEL_DEF_CFG="false";;
      esac
      break
    done
  fi
  #user selection for moonraker.log symlink
  if [ "$MOONRAKER_SL_FOUND" = "false" ]; then
    while true; do
      echo
      read -p "${cyan}###### Create moonraker.log symlink? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          SEL_MRLOG_SL="true";;
        N|n|No|no)
          echo -e "###### > No"
          SEL_MRLOG_SL="false";;
      esac
      break
    done
  fi
  #ask user for more trusted clients
    while true; do
      echo
      top_border
      echo -e "| Apart from devices of your local network, you can add |"
      echo -e "| additional trusted clients to the moonraker.conf file |"
      bottom_border
      read -p "${cyan}###### Add additional trusted clients? (y/N):${default} " yn
      case "$yn" in
        Y|y|Yes|yes)
          echo -e "###### > Yes"
          ADD_TRUSTED_CLIENT="true"
          custom_trusted_clients
          ;;
        N|n|No|no|"")
          echo -e "###### > No"
          ADD_TRUSTED_CLIENT="false";;
      esac
      break
    done
  #ask user for mainsail default macros
    while true; do
      echo
      read -p "${cyan}###### Add the recommended Mainsail macros? (Y/n):${default} "
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          ADD_MAINSAIL_MACROS="true";;
        N|n|No|no)
          echo -e "###### > No"
          ADD_MAINSAIL_MACROS="false";;
      esac
      break
    done
}

#############################################################
#############################################################

moonraker_setup(){
  dep=(wget curl unzip)
  dependency_check
  status_msg "Downloading Moonraker ..."
  if [ -d $MOONRAKER_DIR ]; then
    mv -f $MOONRAKER_DIR ${HOME}/moonraker_bak
  fi
  cd ${HOME} && git clone $MOONRAKER_REPO
  ok_msg "Download complete!"
  status_msg "Installing Moonraker ..."
  $MOONRAKER_DIR/scripts/install-moonraker.sh
  ok_msg "Moonraker successfully installed!"
}

check_for_folder(){
  #check for / create sdcard folder
  if [ ! -d ${HOME}/sdcard ]; then
    status_msg "Creating sdcard directory ..."
    mkdir ${HOME}/sdcard
    ok_msg "sdcard directory created!"
  fi
  ##check for / create klipper_config folder
  if [ ! -d ${HOME}/klipper_config ]; then
    status_msg "Creating klipper_config directory ..."
    mkdir ${HOME}/klipper_config
    ok_msg "klipper_config directory created!"
  fi
}

#############################################################
#############################################################

setup_printer_config(){
  if [ "$PRINTER_CFG_FOUND" = "true" ]; then
    backup_printer_cfg
    if [ "$PRINTER_CFG_LOC" != "${HOME}/klipper_config/printer.cfg" ]; then
      status_msg "Moving printer.cfg to ~/klipper_config ..."
      mv $PRINTER_CFG_LOC ${HOME}/klipper_config
      ok_msg "Done!"
    fi
    status_msg "Create symlink in home directory ..."
    if [ -f ${HOME}/printer.cfg ]; then
      mv ${HOME}/printer.cfg ${HOME}/printer_old.cfg
    fi
    ln -s ${HOME}/klipper_config/printer.cfg ${HOME}
    ok_msg "Done!"
    #check printer.cfg for necessary entries
    read_printer_cfg
    write_printer_cfg
  fi
  if [ "$SEL_DEF_CFG" = "true" ]; then
    create_default_printer_cfg
    status_msg "Create symlink in home directory ..."
    ln -s ${HOME}/klipper_config/printer.cfg ${HOME}
    ok_msg "Done!"
  fi
  #copy mainsail_macro.cfg
  if [ "$ADD_MAINSAIL_MACROS" = "true" ]; then
    status_msg "Create mainsail_macros.cfg ..."
    if [ ! -f ${HOME}/klipper_config/mainsail_macros.cfg ]; then
      cp ${HOME}/kiauh/resources/mainsail_macros.cfg ${HOME}/klipper_config
      ok_msg "File created!"
    else
      warn_msg "File does already exist! Skipping ..."
    fi
  fi
}

read_printer_cfg(){
  SC="#*# <---------------------- SAVE_CONFIG ---------------------->"
  if [ ! $(grep '^\[virtual_sdcard\]$' ${HOME}/klipper_config/printer.cfg) ]; then
    VSD="false"
  fi
  if [ ! $(grep '^\[pause_resume\]$' ${HOME}/klipper_config/printer.cfg) ]; then
    PAUSE_RESUME="false"
  fi
  if [ ! $(grep '^\[display_status\]$' ${HOME}/klipper_config/printer.cfg) ]; then
    DISPLAY_STATUS="false"
  fi
  #check for a SAVE_CONFIG entry
  if [[ $(grep "$SC" ${HOME}/klipper_config/printer.cfg) ]]; then
    SC_LINE=$(grep -n "$SC" ${HOME}/klipper_config/printer.cfg | cut -d ":" -f1)
    PRE_SC_LINE=$(expr $SC_LINE - 1)
    SC_ENTRY="true"
  fi
}

write_printer_cfg(){
  unset write_entries
  if [ "$ADD_MAINSAIL_MACROS" = "true" ]; then
    write_entries+=("[include klipper_config/mainsail_macros.cfg]")
  fi
  if [ "$PAUSE_RESUME" = "false" ]; then
    write_entries+=("[pause_resume]")
  fi
  if [ "$DISPLAY_STATUS" = "false" ]; then
    write_entries+=("[display_status]")
  fi
  if [ "$VSD" = "false" ]; then
    write_entries+=("[virtual_sdcard]\npath: ~/sdcard")
  fi
  if [ "${#write_entries[@]}" != "0" ]; then
    write_entries+=("\\\n############################\n##### CREATED BY KIAUH #####\n############################")
    write_entries=("############################\n" "${write_entries[@]}")
  fi
  #execute writing
  if [ "$SC_ENTRY" = "true" ]; then
    PRE_SC_LINE="$(expr $SC_LINE - 1)a"
    for entry in "${write_entries[@]}"
    do
      sed -i "$PRE_SC_LINE $entry" ${HOME}/klipper_config/printer.cfg
    done
  fi
  if [ "$SC_ENTRY" = "false" ]; then
    LINE_COUNT="$(wc -l < ${HOME}/klipper_config/printer.cfg)a"
    for entry in "${write_entries[@]}"
    do
      sed -i "$LINE_COUNT $entry" ${HOME}/klipper_config/printer.cfg
    done
  fi
}

setup_moonraker_conf(){
  if [ "$MOONRAKER_CONF_FOUND" = "false" ]; then
    status_msg "Creating moonraker.conf ..."
    cp ${HOME}/kiauh/resources/moonraker.conf ${HOME}
    ok_msg "moonraker.conf created!"
    status_msg "Writing trusted clients to config ..."
    write_default_trusted_clients
    ok_msg "Trusted clients written!"
  fi
  #check for at least one trusted client in an already existing moonraker.conf
  #in no entry is found, write default trusted client
  if [ "$MOONRAKER_CONF_FOUND" = "true" ]; then
    if grep "trusted_clients:" ${HOME}/moonraker.conf -q; then
      TC_LINE=$(grep -n "trusted_clients:" ${HOME}/moonraker.conf | cut -d ":" -f1)
      FIRST_IP_LINE=$(expr $TC_LINE + 1)
      FIRST_IP=$(sed -n 2p ${HOME}/moonraker.conf | cut -d" " -f5)
      if [[ ! $FIRST_IP =~ ([0-9].[0-9].[0-9].[0-9]) ]]; then
        status_msg "Writing trusted clients to config ..."
        write_default_trusted_clients
        ok_msg "Trusted clients written!"
      fi
    fi
  fi
}

#############################################################
#############################################################

create_default_printer_cfg(){
#create default config
touch ${HOME}/klipper_config/printer.cfg
cat <<DEFAULT_CFG >> ${HOME}/klipper_config/printer.cfg

##########################
### CREATED WITH KIAUH ###
##########################
[virtual_sdcard]
path: ~/sdcard

[pause_resume]
[display_status]
[include klipper_config/mainsail_macros.cfg]

##########################
##########################
DEFAULT_CFG
}

write_default_trusted_clients(){
  DEFAULT_IP=$(hostname -I)
  status_msg "Your devices current IP adress is:\n${cyan}● $DEFAULT_IP ${default}"
  #make IP of the device KIAUH is exectuted on as
  #default trusted client and expand the IP range from 0 - 255
  DEFAULT_IP_RANGE="$(echo "$DEFAULT_IP" | cut -d"." -f1-3).0/24"
  status_msg "Writing the following IP range to moonraker.conf:\n${cyan}● $DEFAULT_IP_RANGE ${default}"
  #write the ip range in the first line below "trusted clients"
  #example: 192.168.1.0/24
  sed -i "/trusted_clients\:/a \ \ \ \ $DEFAULT_IP_RANGE" ${HOME}/moonraker.conf
  ok_msg "IP range of ${cyan}$DEFAULT_IP_RANGE${default} written to moonraker.conf!"
}

#############################################################
#############################################################

custom_trusted_clients(){
  if [ "$ADD_TRUSTED_CLIENT" = "true" ]; then
    unset trusted_arr
    echo
    top_border
    echo -e "|  You can now add additional trusted clients to your   |"
    echo -e "|  moonraker.conf file. Be warned, that there is no     |"
    echo -e "|  spellcheck to check for valid input.                 |"
    echo -e "|  Make sure to type the IP correct!                    |"
    echo -e "|-------------------------------------------------------|"
    echo -e "|  You can add as many IPs as you want.                 |"
    echo -e "|  When you are done type '${cyan}done${default}' to exit this dialoge.  |"
    bottom_border
    while true; do
      read -p "${cyan}###### Enter IP and press ENTER:${default} " TRUSTED_IP
      case "$TRUSTED_IP" in
        done)
          echo
          echo -e "List of IPs to add:"
          for ip in ${trusted_arr[@]}
          do
            echo -e "${cyan}● $ip ${default}"
          done
          while true; do
            echo
            echo -e "Select 'Yes' to confirm, 'No' to start again"
            echo -e "or 'Q' to abort and skip."
            read -p "${cyan}###### Confirm writing (Y/n/q):${default} " yn
            case "$yn" in
              Y|y|Yes|yes|"")
                echo -e "###### > Yes"
                TUSTED_CLIENT_CONFIRM="true"
                break;;
              N|n|No|no)
                echo -e "###### > No"
                custom_trusted_clients
                break;;
              Q|q)
                unset trusted_arr
                echo -e "###### > Abort"
                echo -e "${red}Aborting ...${default}"
                break;;
            esac
          done
          break;;
        *) trusted_arr+=($TRUSTED_IP);;
      esac
    done
  fi
}

write_custom_trusted_clients(){
  if [ "$TUSTED_CLIENT_CONFIRM" = "true" ]; then
    if [ "${#trusted_arr[@]}" != "0" ]; then
      for ip in ${trusted_arr[@]}
      do
        sed -i "/trusted_clients\:/a \ \ \ \ $ip" ${HOME}/moonraker.conf
      done
      ok_msg "Custom IPs written to moonraker.conf!"
    fi
  fi
}

symlink_moonraker_log(){
  #create a moonraker.log symlink in klipper_config-dir just for convenience
  if [ "$SEL_MRLOG_SL" = "true" ]; then
    status_msg "Creating moonraker.log symlink ..."
    ln -s /tmp/moonraker.log ${HOME}/klipper_config/moonraker.log
    ok_msg "Symlink created!"
  fi
}

#############################################################
#############################################################

test_api(){
  status_msg "Testing API ..."
  sleep 5
  status_msg "API response from http://localhost:7125/printer/info :"
  API_RESPONSE=$(curl -sG4m5 http://localhost:7125/printer/info)
  echo -e "${cyan}$API_RESPONSE${default}"
  if [ $(curl -sG4 "http://localhost:7125/printer/info" | grep '^{"result"' -c) -eq 1 ]; then
    echo; ok_msg "Klipper API is working correctly!"; echo
  else
    echo; warn_msg "Klipper API not working correctly!"; echo
  fi
}