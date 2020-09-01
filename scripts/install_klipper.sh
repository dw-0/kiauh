install_klipper(){
  if [ -e /etc/init.d/klipper ] && [ -e /etc/default/klipper ]; then
    ERROR_MSG="Looks like Klipper is already installed!"
  else
    get_user_selections_klipper
    klipper_setup
    build_fw
    flash_mcu
    write_printer_usb
  fi
}

get_user_selections_klipper(){
  status_msg "Initializing Klipper installation ..."
  #ask user for building firmware
  while true; do
      echo
      read -p "${cyan}###### Do you want to build the Firmware? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          BUILD_FIRMWARE="true"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          BUILD_FIRMWARE="false"
          break;;
    esac
  done
  #ask user for flashing mcu
  while true; do
      echo
      read -p "${cyan}###### Do you want to flash your MCU? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          FLASH_FIRMWARE="true"
          flash_routine
          break;;
        N|n|No|no)
          echo -e "###### > No"
          FLASH_FIRMWARE="false"
          break;;
    esac
  done
}

klipper_setup(){
  #check for dependencies
  dep=(git)
  dependency_check
  #execute operation
  cd ${HOME}
  status_msg "Cloning Klipper repository ..."
  git clone $KLIPPER_REPO
  ok_msg "Klipper successfully cloned!"
  status_msg "Installing Klipper Service ..."
  $KLIPPER_DIR/scripts/install-octopi.sh
  ok_msg "Klipper installation complete!"
  #create a klippy.log symlink in home-dir just for convenience
  if [ ! -e ${HOME}/klippy.log ]; then
    status_msg "Creating klippy.log Symlink ..."
    ln -s /tmp/klippy.log ${HOME}/klippy.log
    ok_msg "Symlink created!"
  fi
}

flash_routine(){
  if [ "$FLASH_FIRMWARE" = "true" ]; then
    echo
    top_border
    echo -e "|        ${red}~~~~~~~~~~~ [ ATTENTION! ] ~~~~~~~~~~~~${default}        |"
    hr
    echo -e "| Flashing a Smoothie based board with this script will |"
    echo -e "| certainly fail. This applies to boards like the BTT   |"
    echo -e "| SKR V1.3 or SKR V1.4(Turbo). You have to copy the     |"
    echo -e "| firmware file to the microSD card manually and rename |"
    echo -e "| it to 'firmware.bin'.                                 |"
    hr
    echo -e "| You can find the file in: ~/klipper/out/klipper.bin   |"
    bottom_border
    while true; do
      read -p "${cyan}###### Do you want to continue? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          CONFIRM_FLASHING="true"
          CONFIRM_WRITE_PRINTER_USB="true"
          get_printer_usb
          break;;
        N|n|No|no)
          echo -e "###### > No"
          CONFIRM_FLASHING="false"
          CONFIRM_WRITE_PRINTER_USB="false"
          break;;
      esac
    done
  fi
}

flash_mcu(){
  if [ "$CONFIRM_FLASHING" = "true" ] && [ ! -z "$PRINTER_USB" ]; then
    stop_klipper
    if ! make flash FLASH_DEVICE="$PRINTER_USB" ; then
      warn_msg "Flashing failed!"
      warn_msg "Please read the console output above!"
    else
      ok_msg "Flashing successfull!"
    fi
    start_klipper
  fi
}

build_fw(){
  if [ "$BUILD_FIRMWARE" = "true" ]; then
    if [ -d $KLIPPER_DIR ]; then
      cd $KLIPPER_DIR
      status_msg "Initializing Firmware Setup ..."
      make menuconfig
      status_msg "Building Firmware ..."
      make clean && make && ok_msg "Firmware built!"
    else
      warn_msg "Can not build Firmware without a Klipper directory!"
    fi
  fi
}

### grab the printers id
get_printer_usb(){
  echo
  top_border
  echo -e "| Please make sure your printer is connected to the Pi! |"
  echo -e "| If the printer is not connected yet, connect it now.  |"
  hr
  echo -e "| Also make sure, that it is the only USB device        |"
  echo -e "| connected at for now! Otherwise this step may fail!   |"
  bottom_border
  while true; do
    echo -e "${cyan}"
    read -p "###### Press any key to continue ... " yn
    echo -e "${default}"
    case "$yn" in
      *)
        CONFIRM_PRINTER_USB="true"
        break;;
    esac
  done
  status_msg "Identifying the correct USB port ..."
  sleep 2
  unset PRINTER_USB
  if [ -e /dev/serial/by-id/* ]; then
    if [ -e /dev/serial/by-id/* ]; then
      PRINTER_USB=$(ls /dev/serial/by-id/*)
      status_msg "The ID of your printer is:"
      title_msg "$PRINTER_USB"
    else
      warn_msg "Could not retrieve ID!"
    fi
  elif [ -e /dev/serial/by-path/* ]; then
    if [ -e /dev/serial/by-path/* ]; then
      PRINTER_USB=$(ls /dev/serial/by-path/*)
      status_msg "The path of your printer is:"
      title_msg "$PRINTER_USB"
    else
      warn_msg "Could not retrieve path!"
    fi
  else
    warn_msg "Printer not plugged in or not detectable!"
fi
}

write_printer_usb(){
  locate_printer_cfg
  if [ ! -z "$PRINTER_CFG" ] && [ "$CONFIRM_WRITE_PRINTER_USB" = "true" ]; then
    SERIAL_OLD=$(grep "serial" $PRINTER_CFG | tail -1 | cut -d" " -f2)
    SERIAL_NEW=$PRINTER_USB
    if [ "$SERIAL_OLD" != "$SERIAL_NEW" ]; then
      unset write_entries
      backup_printer_cfg
      write_entries+=("[mcu]\nserial: $SERIAL_NEW")
      write_entries+=("\\\n############################\n##### CREATED BY KIAUH #####\n############################")
      write_entries=("############################\n" "${write_entries[@]}")
      #check for a SAVE_CONFIG entry
      SC="#*# <---------------------- SAVE_CONFIG ---------------------->"
      if [[ $(grep "$SC" $PRINTER_CFG) ]]; then
        SC_LINE=$(grep -n "$SC" $PRINTER_CFG | cut -d ":" -f1)
        PRE_SC_LINE=$(expr $SC_LINE - 1)
        SC_ENTRY="true"
      else
        SC_ENTRY="false"
      fi
      status_msg "Writing printer ID/path to printer.cfg ..."
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
    fi
  fi
}