# setting up some frequently used functions
check_euid(){
  if [ "$EUID" -eq 0 ]
  then
    echo -e "${red}"
    top_border
    echo -e "|       !!! THIS SCRIPT MUST NOT RAN AS ROOT !!!        |"
    bottom_border
    echo -e "${default}"
    exit 1
  fi
}

locate_printer_cfg(){
  unset PRINTER_CFG
  if [ -e $KLIPPER_SERVICE2 ]; then
    status_msg "Locating printer.cfg via $KLIPPER_SERVICE2 ..."
    #reads /etc/default/klipper and gets the default printer.cfg location
    KLIPPY_ARGS_LINE="$(grep "KLIPPY_ARGS=" /etc/default/klipper)"
    KLIPPY_ARGS_COUNT="$(grep -o " " <<< "$KLIPPY_ARGS_LINE" | wc -l)"
    i=1
    PRINTER_CFG=$(while [ "$i" != "$KLIPPY_ARGS_COUNT" ]; do grep -E "(\/[A-Za-z0-9\_-]+)+\/printer\.cfg" /etc/default/klipper | cut -d" " -f"$i"; i=$(( $i + 1 )); done | grep "printer.cfg")
    ok_msg "printer.cfg location: '$PRINTER_CFG'"
  elif [ -e $KLIPPER_SERVICE3 ]; then
    status_msg "Locating printer.cfg via $KLIPPER_SERVICE3 ..."
    #reads /etc/systemd/system/klipper.service and gets the default printer.cfg location
    KLIPPY_ARGS_LINE="$(grep "ExecStart=" /etc/systemd/system/klipper.service)"
    KLIPPY_ARGS_COUNT="$(grep -o " " <<< "$KLIPPY_ARGS_LINE" | wc -l)"
    i=1
    PRINTER_CFG=$(while [ "$i" != "$KLIPPY_ARGS_COUNT" ]; do grep -E "(\/[A-Za-z0-9\_-]+)+\/printer\.cfg" /etc/systemd/system/klipper.service | cut -d" " -f"$i"; i=$(( $i + 1 )); done | grep "printer.cfg")
    ok_msg "printer.cfg location: '$PRINTER_CFG'"
  else
    PRINTER_CFG=""
    warn_msg "Can't read printer.cfg location!"
  fi
}

source_ini(){
  source ${SRCDIR}/kiauh/kiauh.ini
}

start_klipper(){
  status_msg "Starting Klipper Service ..."
  sudo systemctl start klipper && ok_msg "Klipper Service started!"
}

stop_klipper(){
  status_msg "Stopping Klipper Service ..."
  sudo systemctl stop klipper && ok_msg "Klipper Service stopped!"
}

restart_klipper(){
  status_msg "Restarting Klipper Service ..."
  sudo systemctl restart klipper && ok_msg "Klipper Service restarted!"
}

start_dwc(){
  status_msg "Starting DWC-for-Klipper-Socket Service ..."
  sudo systemctl start dwc && ok_msg "DWC-for-Klipper-Socket Service started!"
}

stop_dwc(){
  status_msg "Stopping DWC-for-Klipper-Socket Service ..."
  sudo systemctl stop dwc && ok_msg "DWC-for-Klipper-Socket Service stopped!"
}

start_moonraker(){
  status_msg "Starting Moonraker Service ..."
  sudo systemctl start moonraker && ok_msg "Moonraker Service started!"
}

stop_moonraker(){
  status_msg "Stopping Moonraker Service ..."
  sudo systemctl stop moonraker && ok_msg "Moonraker Service stopped!"
}

restart_moonraker(){
  status_msg "Restarting Moonraker Service ..."
  sudo systemctl restart moonraker && ok_msg "Moonraker Service restarted!"
}

start_octoprint(){
  status_msg "Starting OctoPrint Service ..."
  sudo systemctl start octoprint && ok_msg "OctoPrint Service started!"
}

stop_octoprint(){
  status_msg "Stopping OctoPrint Service ..."
  sudo systemctl stop octoprint && ok_msg "OctoPrint Service stopped!"
}

restart_octoprint(){
  status_msg "Restarting OctoPrint Service ..."
  sudo systemctl restart octoprint && ok_msg "OctoPrint Service restarted!"
}

enable_octoprint_service(){
  if [[ -f $OCTOPRINT_SERVICE1 && -f $OCTOPRINT_SERVICE2 ]]; then
    status_msg "OctoPrint Service is disabled! Enabling now ..."
    sudo systemctl enable octoprint -q && sudo systemctl start octoprint
  fi
}

disable_octoprint(){
  if [ "$DISABLE_OPRINT" = "true" ]; then
    disable_octoprint_service
  fi
}

disable_octoprint_service(){
  if [[ -f $OCTOPRINT_SERVICE1 && -f $OCTOPRINT_SERVICE2 ]]; then
    status_msg "OctoPrint Service is enabled! Disabling now ..."
    sudo systemctl stop octoprint && sudo systemctl disable octoprint -q
  fi
}

toggle_octoprint_service(){
  if [[ -f $OCTOPRINT_SERVICE1 && -f $OCTOPRINT_SERVICE2 ]]; then
    if systemctl is-enabled octoprint.service -q; then
      disable_octoprint_service
      sleep 2
      CONFIRM_MSG=" OctoPrint Service is now >>> DISABLED <<< !"
    else
      enable_octoprint_service
      sleep 2
      CONFIRM_MSG=" OctoPrint Service is now >>> ENABLED <<< !"
    fi
  else
    ERROR_MSG=" You cannot activate a service that does not exist!"
  fi
}

read_octoprint_service_status(){
  if ! systemctl is-enabled octoprint.service -q &>/dev/null; then
    OPRINT_SERVICE_STATUS="${green}[Enable]${default} OctoPrint Service                        "
  else
    OPRINT_SERVICE_STATUS="${red}[Disable]${default} OctoPrint Service                       "
  fi
}

restart_nginx(){
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "nginx.service")" ]; then
    status_msg "Restarting Nginx Service ..."
    sudo systemctl restart nginx && ok_msg "Nginx Service restarted!"
  fi
}

dependency_check(){
  status_msg "Checking for the following dependencies:"
  #check if package is installed, if not write name into array
  for pkg in "${dep[@]}"
  do
    echo -e "${cyan}● $pkg ${default}"
    if [[ ! $(dpkg-query -f'${Status}' --show $pkg 2>/dev/null) = *\ installed ]]; then
      inst+=($pkg)
    fi
  done
  #if array is not empty, install packages from array elements
  if [ "${#inst[@]}" != "0" ]; then
    status_msg "Installing the following dependencies:"
    for element in ${inst[@]}
    do
      echo -e "${cyan}● $element ${default}"
    done
    echo
    sudo apt-get install ${inst[@]} -y
    ok_msg "Dependencies installed!"
    #clearing the array
    unset inst
  else
    ok_msg "Dependencies already met! Continue..."
  fi
}

print_error(){
  for data in "${data_arr[@]}"
  do
    if [ ! -e $data ]; then
      data_count+=(0)
    else
      data_count+=(1)
    fi
  done
  sum=$(IFS=+; echo "$((${data_count[*]}))")
  if [ $sum -eq 0 ]; then
    ERROR_MSG="Looks like $1 was already removed!\n Skipping..."
  else
    ERROR_MSG=""
  fi
}

setup_gcode_shell_command(){
  echo
  top_border
  echo -e "| You are about to install the G-Code Shell Command     |"
  echo -e "| extension. Please make sure to read the instructions  |"
  echo -e "| before you continue and remember that potential risks |"
  echo -e "| can be involved after installing this extension!      |"
  blank_line
  echo -e "| ${red}You accept that you are doing this on your own risk!${default}  |"
  bottom_border
  while true; do
    read -p "${cyan}###### Do you want to continue? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        if [ -d $KLIPPER_DIR/klippy/extras ]; then
          status_msg "Installing gcode shell command extension ..."
          status_msg "Copy gcode_shell_command.py to '$KLIPPER_DIR/klippy/extras' ..."
          if [ -f $KLIPPER_DIR/klippy/extras/gcode_shell_command.py ]; then
            warn_msg "There is already a file named 'gcode_shell_command.py'"
            warn_msg "in the destination location!"
            while true; do
              read -p "${cyan}###### Do you want to overwrite it? (Y/n):${default} " yn
              case "$yn" in
                Y|y|Yes|yes|"")
                  rm -f $KLIPPER_DIR/klippy/extras/gcode_shell_command.py
                  install_gcode_shell_command
                  break;;
                N|n|No|no)
                  break;;
              esac
            done
          else
            install_gcode_shell_command
          fi
        else
          ERROR_MSG="Folder ~/klipper/klippy/extras not found!"
        fi
        break;;
      N|n|No|no)
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

install_gcode_shell_command(){
  stop_klipper
  status_msg "Copy 'gcode_shell_command.py' to $KLIPPER_DIR/klippy/extras"
  cp ${HOME}/kiauh/resources/gcode_shell_command.py $KLIPPER_DIR/klippy/extras
  echo
  while true; do
    read -p "${cyan}###### Do you want to create the example shell command? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        ADD_SHELL_CMD_MACRO="true"
        status_msg "Creating example macro ..."
        locate_printer_cfg
        read_printer_cfg "gcode_shell_command"
        write_printer_cfg
        ok_msg "Example macro created!"
        break;;
      N|n|No|no)
        break;;
    esac
  done
  ok_msg "Shell command extension installed!"
  restart_klipper
}

create_minimal_cfg(){
  #create a minimal default config for either moonraker or dwc2
  if [ "$SEL_DEF_CFG" = "true" ]; then
		cat <<- EOF >> $PRINTER_CFG
		[mcu]
		serial: </dev/serial/by-id/your-mcu>

		[printer]
		kinematics: cartesian
		max_velocity: 300
		max_accel: 3000
		max_z_velocity: 5
		max_z_accel: 100

		[virtual_sdcard]
		path: ~/sdcard

		[pause_resume]
		[display_status]
EOF
  fi
}

read_printer_cfg(){
  KIAUH_CFG=$(echo $PRINTER_CFG | sed 's/printer/kiauh/')
  [ ! -f $KIAUH_CFG ] && KIAUH_CFG_FOUND="false" || KIAUH_CFG_FOUND="true"
  if [ -f $PRINTER_CFG ]; then
    if [ "$1" = "moonraker" ]; then
      [ ! "$(grep '^\[virtual_sdcard\]$' $PRINTER_CFG)" ] && VSD="false" && EDIT_CFG="true"
      [ ! "$(grep '^\[pause_resume\]$' $PRINTER_CFG)" ] && PAUSE_RESUME="false" && EDIT_CFG="true"
      [ ! "$(grep '^\[display_status\]$' $PRINTER_CFG)" ] && DISPLAY_STATUS="false" && EDIT_CFG="true"
    elif [ "$1" = "mainsail" ] || [ "$1" = "fluidd" ]; then
      [ ! "$(grep '^\[include webui_macros\.cfg\]$' $PRINTER_CFG)" ] && WEBUI_MACROS="false" && EDIT_CFG="true"
    elif [ "$1" = "dwc2" ]; then
      [ ! "$(grep '^\[virtual_sdcard\]$' $PRINTER_CFG)" ] && VSD="false" && EDIT_CFG="true"
    fi
  fi
}

write_printer_cfg(){
  #backup printer.cfg if edits will be written
  [ "$EDIT_CFG" = "true" ] && backup_printer_cfg
  #create kiauh.cfg if its needed and doesn't exist
  if [ "$KIAUH_CFG_FOUND" = "false" ] && [ "$EDIT_CFG" = "true" ]; then
    status_msg "Creating kiauh.cfg ..."
    echo -e "##### AUTOCREATED BY KIAUH #####" > $KIAUH_CFG
  fi
  #write each entry to kiauh.cfg if it doesn't exist
  #Moonraker/DWC2 related config options
  if [ "$VSD" = "false" ] && [[ ! $(grep '^\[virtual_sdcard\]$' $KIAUH_CFG) ]]; then
    echo -e "\n[virtual_sdcard]\npath: ~/sdcard" >> $KIAUH_CFG
  fi
  if [ "$PAUSE_RESUME" = "false" ] && [[ ! $(grep '^\[pause_resume]$' $KIAUH_CFG) ]]; then
    echo -e "\n[pause_resume]" >> $KIAUH_CFG
  fi
  if [ "$DISPLAY_STATUS" = "false" ] && [[ ! $(grep '^\[display_status]$' $KIAUH_CFG) ]]; then
    echo -e "\n[display_status]" >> $KIAUH_CFG
  fi
  #Klipper webui related config options
  if [ "$WEBUI_MACROS" = "false" ] && [ "$ADD_WEBUI_MACROS" = "true" ] && [[ ! $(grep '^\[include webui_macros.cfg]$' $KIAUH_CFG) ]]; then
    echo -e "\n[include webui_macros.cfg]" >> $KIAUH_CFG
  fi
  #G-Code Shell Command extension related config options
  if [ "$ADD_SHELL_CMD_MACRO" = "true" ] && [[ ! $(grep '^\[gcode_shell_command hello_world]$' $KIAUH_CFG) ]]; then
		cat <<-EOF >> $KIAUH_CFG
		[gcode_shell_command hello_world]
		command: echo hello world
		timeout: 2.
		verbose: True
		[gcode_macro HELLO_WORLD]
		gcode:
		    RUN_SHELL_COMMAND CMD=hello_world
EOF
  fi
  #including the kiauh.cfg into printer.cfg if not already done
  if [ ! "$(grep '^\[include kiauh\.cfg\]$' $PRINTER_CFG)" ] && [ "$EDIT_CFG" = "true" ]; then
    status_msg "Writing [include kiauh.cfg] to printer.cfg ..."
    sed -i '1 i ##### AUTOCREATED BY KIAUH #####\n[include kiauh.cfg]' $PRINTER_CFG
  fi
  ok_msg "Done!"
}

init_ini(){
  if [ ! -f $INI_FILE ]; then
    echo -e "#don't edit this file if you don't know what you are doing...\c" > $INI_FILE
  fi
  if [ ! $(grep -E "^backup_before_update=." $INI_FILE) ]; then
    echo -e "\nbackup_before_update=false\c" >> $INI_FILE
  fi
  if [ ! $(grep -E "^previous_origin_state=[[:alnum:]]" $INI_FILE) ]; then
    echo -e "\nprevious_origin_state=0\c" >> $INI_FILE
  fi
  if [ ! $(grep -E "^previous_smoothing_state=[[:alnum:]]" $INI_FILE) ]; then
    echo -e "\nprevious_smoothing_state=0\c" >> $INI_FILE
  fi
  if [ ! $(grep -E "^previous_shaping_state=[[:alnum:]]" $INI_FILE) ]; then
    echo -e "\nprevious_shaping_state=0\c" >> $INI_FILE
  fi
  if [ ! $(grep -E "^logupload_accepted=." $INI_FILE) ]; then
    echo -e "\nlogupload_accepted=false\c" >> $INI_FILE
  fi
}