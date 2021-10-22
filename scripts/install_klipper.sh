### base variables
SYSTEMDDIR="/etc/systemd/system"
KLIPPY_ENV="${HOME}/klippy-env"
KLIPPER_DIR="${HOME}/klipper"

klipper_setup_dialog(){
  status_msg "Initializing Klipper installation ..."

  ### check for existing klipper service files
  INITD=$(ls /etc/init.d | grep -E "^klipper(\-[[:digit:]]+)?$")
  SYSTEMD=$(ls /etc/systemd/system | grep -E "^klipper(\-[[:digit:]]+)?\.service$")

  if [ ! -z "$INITD" ] || [ ! -z "$SYSTEMD" ]; then
    echo "${red}$INITD${default}" && echo "${red}$SYSTEMD${default}"
    ERROR_MSG="At least one Klipper service is already installed!\n Please remove Klipper first, before installing it again." && return 0
  fi

  ### initial printer.cfg path check
  check_klipper_cfg_path

  ### ask for amount of instances to create
  INSTANCE_COUNT=""
  while [[ ! ($INSTANCE_COUNT =~ ^[1-9]+((0)+)?$) ]]; do
    echo
    read -p "${cyan}###### Number of Klipper instances to set up:${default} " INSTANCE_COUNT
    if [[ ! ($INSTANCE_COUNT =~ ^[1-9]+((0)+)?$) ]]; then
      warn_msg "Invalid Input!" && echo
    else
      echo
      read -p "${cyan}###### Install $INSTANCE_COUNT instance(s)? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Installing $INSTANCE_COUNT Klipper instance(s) ..."
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
    fi
  done
}

install_klipper_packages(){
  ### read PKGLIST from official install script
  status_msg "Reading dependencies..."
  install_script="${HOME}/klipper/scripts/install-octopi.sh"
  PKGLIST=$(grep "PKGLIST=" $install_script | sed 's/PKGLIST//g; s/[$={}\n"]//g')
  ### rewrite packages into new array
  unset PKGARR
  for PKG in $PKGLIST; do PKGARR+=($PKG); done
  ### add dbus requirement for DietPi distro
  if [ -e "/boot/dietpi" ]; then
    PKGARR+=("dbus")
  fi

  ### display dependencies to user
  echo "${cyan}${PKGARR[@]}${default}"

  ### Update system package info
  status_msg "Running apt-get update..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install desired packages
  status_msg "Installing packages..."
  sudo apt-get install --yes ${PKGARR[@]}
}

create_klipper_virtualenv(){
  status_msg "Installing python virtual environment..."
  # Create virtualenv if it doesn't already exist
  [ ! -d ${KLIPPY_ENV} ] && virtualenv -p python2 ${KLIPPY_ENV}
  # Install/update dependencies
  ${KLIPPY_ENV}/bin/pip install -r ${KLIPPER_DIR}/scripts/klippy-requirements.txt
}

klipper_setup(){
  ### step 1: clone klipper
  status_msg "Downloading Klipper ..."
  ### force remove existing klipper dir and clone into fresh klipper dir
  [ -d $KLIPPER_DIR ] && rm -rf $KLIPPER_DIR
  cd ${HOME} && git clone $KLIPPER_REPO
  status_msg "Download complete!"

  ### step 2: install klipper dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_klipper_packages
  create_klipper_virtualenv

  ### step 3: create shared gcode_files and logs folder
  [ ! -d ${HOME}/gcode_files ] && mkdir -p ${HOME}/gcode_files
  [ ! -d ${HOME}/klipper_logs ] && mkdir -p ${HOME}/klipper_logs

  ### step 4: create klipper instances
  create_klipper_service

  ### confirm message
  CONFIRM_MSG="$INSTANCE_COUNT Klipper instances have been set up!"
  [ $INSTANCE_COUNT -eq 1 ] && CONFIRM_MSG="Klipper has been set up!"
  print_msg && clear_msg
}

create_klipper_service(){
  ### get config directory
  source_kiauh_ini

  ### set up default values
  SINGLE_INST=1
  CFG_PATH="$klipper_cfg_loc"
  KL_ENV=$KLIPPY_ENV
  KL_DIR=$KLIPPER_DIR
  KL_LOG="${HOME}/klipper_logs/klippy.log"
  KL_UDS="/tmp/klippy_uds"
  P_TMP="/tmp/printer"
  P_CFG="$CFG_PATH/printer.cfg"
  P_CFG_SRC="${SRCDIR}/kiauh/resources/printer.cfg"
  KL_SERV_SRC="${SRCDIR}/kiauh/resources/klipper.service"
  KL_SERV_TARGET="$SYSTEMDDIR/klipper.service"

  write_kl_service(){
    [ ! -d $CFG_PATH ] && mkdir -p $CFG_PATH
    ### create a minimal config if there is no printer.cfg
    [ ! -f $P_CFG ] && cp $P_CFG_SRC $P_CFG
    ### replace placeholder
    if [ ! -f $KL_SERV_TARGET ]; then
      status_msg "Creating Klipper Service $i ..."
        sudo cp $KL_SERV_SRC $KL_SERV_TARGET
        sudo sed -i "s|%INST%|$i|" $KL_SERV_TARGET
        sudo sed -i "s|%USER%|${USER}|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_ENV%|$KL_ENV|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_DIR%|$KL_DIR|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_LOG%|$KL_LOG|" $KL_SERV_TARGET
        sudo sed -i "s|%P_CFG%|$P_CFG|" $KL_SERV_TARGET
        sudo sed -i "s|%P_TMP%|$P_TMP|" $KL_SERV_TARGET
        sudo sed -i "s|%KL_UDS%|$KL_UDS|" $KL_SERV_TARGET
    fi
  }

  if [ $SINGLE_INST -eq $INSTANCE_COUNT ]; then
    ### write single instance service
    write_kl_service
    ### enable instance
    sudo systemctl enable klipper.service
    ok_msg "Single Klipper instance created!"
    ### launching instance
    status_msg "Launching Klipper instance ..."
    sudo systemctl start klipper
  else
    i=1
    while [ $i -le $INSTANCE_COUNT ]; do
      ### rewrite default variables for multi instance cases
      CFG_PATH="$klipper_cfg_loc/printer_$i"
      KL_SERV_TARGET="$SYSTEMDDIR/klipper-$i.service"
      P_TMP="/tmp/printer-$i"
      P_CFG="$CFG_PATH/printer.cfg"
      KL_LOG="${HOME}/klipper_logs/klippy-$i.log"
      KL_UDS="/tmp/klippy_uds-$i"
      ### write multi instance service
      write_kl_service
      ### enable instance
      sudo systemctl enable klipper-$i.service
      ok_msg "Klipper instance #$i created!"
      ### launching instance
      status_msg "Launching Klipper instance #$i ..."
      sudo systemctl start klipper-$i

      ### raise values by 1
      i=$((i+1))
    done
    unset i
  fi
}
