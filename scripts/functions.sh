# setting up some frequently used functions
check_euid(){
  if [ "$EUID" -eq 0 ]
  then
    echo -e "${red}"
    echo -e "/=================================================\ "
    echo -e "|    !!! THIS SCRIPT MUST NOT RAN AS ROOT !!!     |"
    echo -e "\=================================================/ "
    echo -e "${default}"
    exit 1
  fi
}

source_ini(){
  source ${HOME}/kiauh/kiauh.ini
}

start_klipper(){
  if [ -e /etc/init.d/klipper ]; then
    status_msg "Starting Klipper Service ..."
    sudo /etc/init.d/klipper start && sleep 2 && ok_msg "Klipper Service started!"
  fi
}

stop_klipper(){
  if [ -e /etc/init.d/klipper ]; then
    status_msg "Stopping Klipper Service ..."
    sudo /etc/init.d/klipper stop && sleep 2 && ok_msg "Klipper Service stopped!"
  fi
}

restart_klipper(){
  if [ -e /etc/init.d/klipper ]; then
    status_msg "Restarting Klipper Service ..."
    sudo /etc/init.d/klipper restart && sleep 2 && ok_msg "Klipper Service restarted!"
  fi
}

start_moonraker(){
  if [ -e /etc/init.d/moonraker ]; then
    status_msg "Starting Moonraker Service ..."
    sudo /etc/init.d/moonraker start && sleep 2 && ok_msg "Moonraker Service started!"
  fi
}

stop_moonraker(){
  if [ -e /etc/init.d/moonraker ]; then
    status_msg "Stopping Moonraker Service ..."
    sudo /etc/init.d/moonraker stop && sleep 2 && ok_msg "Moonraker Service stopped!"
  fi
}

restart_moonraker(){
  if [ -e /etc/init.d/moonraker ]; then
    status_msg "Restarting Moonraker Service ..."
    sudo /etc/init.d/moonraker restart && sleep 2 && ok_msg "Moonraker Service restarted!"
  fi
}

start_octoprint(){
  if [ -e /etc/init.d/octoprint ]; then
    status_msg "Starting OctoPrint Service ..."
    sudo /etc/init.d/octoprint start && sleep 2 && ok_msg "OctoPrint Service started!"
  fi
}

stop_octoprint(){
  if [ -e /etc/init.d/octoprint ]; then
    status_msg "Stopping OctoPrint Service ..."
    sudo /etc/init.d/octoprint stop && sleep 2 && ok_msg "OctoPrint Service stopped!"
  fi
}

restart_octoprint(){
  if [ -e /etc/init.d/octoprint ]; then
    status_msg "Restarting OctoPrint Service ..."
    sudo /etc/init.d/octoprint restart && sleep 2 && ok_msg "OctoPrint Service restarted!"
  fi
}

dep_check(){
  for package in "${dep[@]}"
  do
    ! command -v $package >&/dev/null 2>&1 && install+=($package)
  done
  if ! [ ${#install[@]} -eq 0 ]; then
  warn_msg "The following packages are missing but necessary:"
  echo ${install[@]}
  while true; do
    read -p "Do you want to install them now? (Y/n): " yn
    case "$yn" in
      Y|y|Yes|yes|"")
      status_msg "Installing dependencies ..."
      sudo apt-get install ${install[@]} -y && ok_msg "Dependencies installed!"
      break;;
      N|n|No|no) break;;
    esac
  done
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
    ERROR_MSG=" Looks like $1 was already removed!\n Skipping..."
  else
    ERROR_MSG=""
  fi
}

#pkg_check(){
#  #WIP
#  if [[ $(dpkg-query -f'${Status}' --show $PKG 2>/dev/null) = *\ installed ]]; then
#    echo "WIP"
#  else
#    sudo apt-get -y install $PKG 2>/dev/null
#  fi
#}

build_fw(){
    if [ -d $KLIPPER_DIR ]; then
      cd $KLIPPER_DIR && make menuconfig
      status_msg "Building Firmware ..."
      make clean && make && ok_msg "Firmware built!"
    else
      warn_msg "Can not build Firmware without a Klipper directory!"
    fi
}

### grab the printers id
get_usb_id(){
  warn_msg "Make sure your printer is the only USB device connected!"
  while true; do
    echo -e "${cyan}"
    read -p "###### Press any key to continue ... " yn
    echo -e "${default}"
    case "$yn" in
      *) break;;
    esac
  done
  status_msg "Identifying the correct USB port ..."
  USB_ID=$(ls /dev/serial/by-id/*)
  if [ -e /dev/serial/by-id/* ]; then
    status_msg "The ID of your printer is:"
    title_msg "$USB_ID"
  else
    warn_msg "Could not retrieve ID!"
    return 1
  fi
}

write_printer_id(){
  while true; do
    echo -e "${cyan}"
    read -p "###### Do you want to write the ID to your printer.cfg? (Y/n): " yn
    echo -e "${default}"
    case "$yn" in
      Y|y|Yes|yes|"")
        backup_printer_cfg
cat <<PRINTERID >> $PRINTER_CFG

##########################
### CREATED WITH KIAUH ###
##########################
[mcu]
serial: $USB_ID
##########################
##########################
PRINTERID
        ok_msg "Config written!"
        break;;
      N|n|No|no) break;;
    esac
  done
}

flash_routine(){
  echo -e "/=================================================\ "
  echo -e "|     ${red}~~~~~~~~~~~ [ ATTENTION! ] ~~~~~~~~~~~~${default}     |"
  echo -e "| Flashing a Smoothie based board for the first   |"
  echo -e "| time with this script will certainly fail.      |"
  echo -e "| This applies to boards like the BTT SKR V1.3 or |"
  echo -e "| the newer SKR V1.4 (Turbo). You have to copy    |"
  echo -e "| the firmware file to the microSD card manually  |"
  echo -e "| and rename it to 'firmware.bin'.                |"
  echo -e "|                                                 |"
  echo -e "| You find the file in: ~/klipper/out/klipper.bin |"
  echo -e "\=================================================/ "
  echo
  while true; do
    echo -e "${cyan}"
    read -p "###### Do you want to continue? (Y/n): " yn
    echo -e "${default}"
    case "$yn" in
      Y|y|Yes|yes|"")
      get_usb_id && flash_mcu && write_printer_id; break;;
      N|n|No|no) break;;
    esac
  done
}

flash_mcu(){
  stop_klipper
  if ! make flash FLASH_DEVICE="$USB_ID" ; then
    warn_msg "Flashing failed!"
    warn_msg "Please read the log above!"
  else
    ok_msg "Flashing successfull!"
  fi
  start_klipper
}

enable_octoprint_service(){
  if [[ -f $OCTOPRINT_SERVICE1 && -f $OCTOPRINT_SERVICE2 ]]; then
    status_msg "OctoPrint Service is disabled! Enabling now ..."
    sudo systemctl enable octoprint -q && sudo systemctl start octoprint
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