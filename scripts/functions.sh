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
  status_msg "Locating printer.cfg via /etc/default/klipper ..."
  if [ -f $KLIPPER_SERVICE2 ]; then
    #reads /etc/default/klipper and gets the default printer.cfg location
    KLIPPY_ARGS_LINE="$(grep "KLIPPY_ARGS=" /etc/default/klipper)"
    KLIPPY_ARGS_COUNT="$(grep -o " " <<< "$KLIPPY_ARGS_LINE" | wc -l)"
    i=1
    PRINTER_CFG=$(while [ "$i" != "$KLIPPY_ARGS_COUNT" ]; do grep -E "(\/[A-Za-z0-9\_-]+)+\/printer\.cfg" /etc/default/klipper | cut -d" " -f"$i"; i=$(( $i + 1 )); done | grep "printer.cfg")
    ok_msg "printer.cfg location: '$PRINTER_CFG'"
  else
    PRINTER_CFG=""
    warn_msg "Can't read /etc/default/klipper - File not found!"
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
  sudo systemctl start moonraker
  ok_msg "Moonraker Service started!"
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
  if [ -e /etc/init.d/nginx ]; then
    status_msg "Restarting Nginx Service ..."
    sudo /etc/init.d/nginx restart && sleep 2 && ok_msg "Nginx Service restarted!"
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

install_extension_shell_command(){
  echo
  top_border
  echo -e "| You are about to install the shell command extension. |"
  echo -e "| Please make sure to read the instructions before you  |"
  echo -e "| continue and remember that there are potential risks! |"
  bottom_border
  while true; do
    read -p "${cyan}###### Do you want to continue? (Y/n):${default} " yn
    case "$yn" in
      Y|y|Yes|yes|"")
        if [ -d $KLIPPER_DIR/klippy/extras ] && [ ! -f $KLIPPER_DIR/klippy/extras/shell_command.py ] ; then
          status_msg "Installing shell command extension ..."
          stop_klipper
          cp ${HOME}/kiauh/resources/shell_command.py $KLIPPER_DIR/klippy/extras
          status_msg "Creating example macro ..."
          create_shell_command_example
          ok_msg "Example macro created!"
          ok_msg "Shell command extension installed!"
          restart_klipper
        else
          if [ ! -d $KLIPPER_DIR/klippy/extras ]; then
            ERROR_MSG="Folder ~/klipper/klippy/extras not found!"
          fi
          if [ -f $KLIPPER_DIR/klippy/extras/shell_command.py ]; then
            ERROR_MSG="Extension already installed!"
          fi
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

create_shell_command_example(){
  unset SC_ENTRY
  unset write_entries
  #check for a SAVE_CONFIG entry
  SC="#*# <---------------------- SAVE_CONFIG ---------------------->"
  if [[ $(grep "$SC" ${HOME}/printer.cfg) ]]; then
    SC_LINE=$(grep -n "$SC" $PRINTER_CFG | cut -d ":" -f1)
    PRE_SC_LINE=$(expr $SC_LINE - 1)
    SC_ENTRY="true"
  else
    SC_ENTRY="false"
  fi
  #example shell command
  write_entries+=("[shell_command hello_world]\ncommand: echo hello world\ntimeout: 2.\nverbose: True")
  #example macro
  write_entries+=("[gcode_macro HELLO_WORLD]\ngcode:\n    RUN_SHELL_COMMAND CMD=hello_world")
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