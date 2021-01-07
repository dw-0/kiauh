#install_klipper(){
#  get_user_selections_klipper
#  klipper_setup
#  build_fw
#  flash_mcu
#  write_printer_usb
#}

### base variables
SYSTEMDDIR="/etc/systemd/system"
KLIPPY_ENV="${HOME}/klippy-env"
KLIPPER_DIR="${HOME}/klipper"

klipper_setup_dialog(){
  status_msg "Initializing Klipper installation ..."

  ### check for existing klipper service installations
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ] || [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service")" ]; then
    ERROR_MSG="At least one Klipper service is already installed!" && return 0
  fi

  ### initial printer.cfg path check
  check_klipper_cfg_path

  ### ask for amount of instances to create
  while true; do
      echo
      read -p "${cyan}###### How many Klipper instances do you want to set up?:${default} " INSTANCE_COUNT
      echo
      if [ $INSTANCE_COUNT == 1 ]; then
        read -p "${cyan}###### Create $INSTANCE_COUNT single instance? (Y/n):${default} " yn
      else
        read -p "${cyan}###### Create $INSTANCE_COUNT instances? (Y/n):${default} " yn
      fi
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Creating $INSTANCE_COUNT Klipper instances ..."
          klipper_setup
          break;;
        N|n|No|no)
          echo -e "###### > No"
          warn_msg "Exiting Klipper setup ..."
          echo
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
  done
}

install_klipper_packages(){
  ### Packages for python cffi
  PKGLIST="python-virtualenv virtualenv python-dev libffi-dev build-essential"
  ### kconfig requirements
  PKGLIST="${PKGLIST} libncurses-dev"
  ### hub-ctrl
  PKGLIST="${PKGLIST} libusb-dev"
  ### AVR chip installation and building
  PKGLIST="${PKGLIST} avrdude gcc-avr binutils-avr avr-libc"
  ### ARM chip installation and building
  PKGLIST="${PKGLIST} stm32flash libnewlib-arm-none-eabi"
  PKGLIST="${PKGLIST} gcc-arm-none-eabi binutils-arm-none-eabi libusb-1.0"
  ### dbus requirement for DietPi
  PKGLIST="${PKGLIST} dbus"

  ### Update system package info
  status_msg "Running apt-get update..."
  sudo apt-get update

  ### Install desired packages
  status_msg "Installing packages..."
  sudo apt-get install --yes ${PKGLIST}
}

create_klipper_virtualenv(){
  status_msg "Installing python virtual environment..."
  # Create virtualenv if it doesn't already exist
  [ ! -d ${KLIPPY_ENV} ] && virtualenv -p python2 ${KLIPPY_ENV}
  # Install/update dependencies
  ${KLIPPY_ENV}/bin/pip install -r ${KLIPPER_DIR}/scripts/klippy-requirements.txt
}

create_single_klipper_startscript(){
### create systemd service file
sudo /bin/sh -c "cat > $SYSTEMDDIR/klipper.service" << EOF
#Systemd service file for klipper
[Unit]
Description=Starts klipper on startup
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=$USER
RemainAfterExit=yes
ExecStart=${KLIPPY_ENV}/bin/python ${KLIPPER_DIR}/klippy/klippy.py ${PRINTER_CFG} -l ${KLIPPER_LOG} -a ${KLIPPY_UDS}
Restart=always
RestartSec=10
EOF
}

create_multi_klipper_startscript(){
### create multi instance systemd service file
sudo /bin/sh -c "cat > $SYSTEMDDIR/klipper-$INSTANCE.service" << EOF
#Systemd service file for klipper
[Unit]
Description=Starts klipper instance $INSTANCE on startup
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=$USER
RemainAfterExit=yes
ExecStart=${KLIPPY_ENV}/bin/python ${KLIPPER_DIR}/klippy/klippy.py ${PRINTER_CFG} -I ${TMP_PRINTER} -l ${KLIPPER_LOG} -a ${KLIPPY_UDS}
Restart=always
RestartSec=10
EOF
}

klipper_setup(){
  ### get printer config directory
  source_kiauh_ini
  PRINTER_CFG_LOC="$klipper_cfg_loc"

  ### clone klipper
  cd ${HOME}
  status_msg "Downloading Klipper ..."
  [ -d $KLIPPER_DIR ] && rm -rf $KLIPPER_DIR
  git clone $KLIPPER_REPO
  status_msg "Download complete!"

  ### install klipper dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_klipper_packages
  create_klipper_virtualenv

  ### create sdcard folder
  [ ! -d ${HOME}/sdcard ] && mkdir -p ${HOME}/sdcard
  ### create config folder
  [ ! -d $PRINTER_CFG_LOC ] && mkdir -p $PRINTER_CFG_LOC

  ### create klipper instances
  INSTANCE=1
  if [ $INSTANCE_COUNT -eq $INSTANCE ]; then
    create_single_klipper_instance
  else
    create_multi_klipper_instance
  fi
}

create_single_klipper_instance(){
  status_msg "Setting up 1 Klipper instance ..."

  ### single instance variables
  KLIPPER_LOG=/tmp/klippy.log
  KLIPPY_UDS=/tmp/klippy_uds
  PRINTER_CFG="$PRINTER_CFG_LOC/printer.cfg"

  ### create instance
  status_msg "Creating single Klipper instance ..."
  status_msg "Installing system start script ..."
  create_single_klipper_startscript

  ### enable instance
  sudo systemctl enable klipper.service
  ok_msg "Single Klipper instance created!"

  ### launching instance
  status_msg "Launching Klipper instance ..."
  sudo systemctl start klipper

  ### confirm message
  ok_msg "Single Klipper instance has been set up!\n"
}

create_multi_klipper_instance(){
  status_msg "Setting up $INSTANCE_COUNT instances of Klipper ..."
  while [ $INSTANCE -le $INSTANCE_COUNT ]; do
    ### multi instance variables
    KLIPPER_LOG=/tmp/klippy-$INSTANCE.log
    KLIPPY_UDS=/tmp/klippy_uds-$INSTANCE
    TMP_PRINTER=/tmp/printer-$INSTANCE
    PRINTER_CFG="$PRINTER_CFG_LOC/printer-$INSTANCE.cfg"

    ### create instance
    status_msg "Creating instance #$INSTANCE ..."
    create_multi_klipper_startscript

    ### enable instance
    sudo systemctl enable klipper-$INSTANCE.service
    ok_msg "Klipper instance $INSTANCE created!"

    ### launching instance
    status_msg "Launching Klipper instance $INSTANCE ..."
    sudo systemctl start klipper-$INSTANCE

    ### instance counter +1
    INSTANCE=$(expr $INSTANCE + 1)
  done
  ### confirm message
  ok_msg "$INSTANCE_COUNT Klipper instances have been set up!\n"
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
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

flash_mcu(){
  if [ "$CONFIRM_FLASHING" = "true" ] && [ ! -z "$PRINTER_USB" ]; then
    klipper_service "stop"
    if ! make flash FLASH_DEVICE="$PRINTER_USB" ; then
      warn_msg "Flashing failed!"
      warn_msg "Please read the console output above!"
    else
      ok_msg "Flashing successfull!"
    fi
    klipper_service "start"
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