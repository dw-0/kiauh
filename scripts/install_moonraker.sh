### base variables
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_ENV="${HOME}/moonraker-env"
MOONRAKER_DIR="${HOME}/moonraker"
MOONRAKER_REPO="https://github.com/Arksine/moonraker.git"

system_check_moonraker(){
  ### python 3 check
  status_msg "Your Python 3 version is: $(python3 --version)"
  major=$(python3 --version | cut -d" " -f2 | cut -d"." -f1)
  minor=$(python3 --version | cut -d"." -f2)
  if [ $major -ge 3 ] && [ $minor -ge 7 ]; then
    ok_msg "Python version ok!"
    py_chk_ok="true"
  else
    warn_msg "Python version not ok!"
    py_chk_ok="false"
  fi
}

moonraker_setup_dialog(){
  status_msg "Initializing Moonraker installation ..."

  ### checking system for python3.7+
  system_check_moonraker

  ### exit moonraker setup if python version is not ok
  if [ $py_chk_ok = "false" ]; then
    ERROR_MSG="Python 3.7 or above required!\n Please upgrade your Python version first."
    print_msg && clear_msg && return 0
  fi

  shopt -s extglob # enable extended globbing
  ### check for existing moonraker service installations
  FILE="$SYSTEMDDIR/moonraker?(-*([0-9])).service"
  if ls $FILE 2>/dev/null 1>&2; then
    ERROR_MSG="At least one Moonraker service is already installed!" && return 0
  fi

  ### check for existing klipper service installations
  FILE="$SYSTEMDDIR/klipper?(-*([0-9])).service"
  if ! ls $FILE 2>/dev/null 1>&2; then
    ERROR_MSG="Klipper service not found, please install Klipper first!" && return 0
  fi
  shopt -u extglob # disable extended globbing

  ### count amount of klipper services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    INSTANCE_COUNT=1
  else
    INSTANCE_COUNT=$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]]+.service" | wc -l)
  fi

  ### initial moonraker.conf path check
  check_klipper_cfg_path

  ### instance confirmation dialog
  while true; do
      echo
      top_border
      if [ $INSTANCE_COUNT -gt 1 ]; then
        printf "|%-55s|\n" " $INSTANCE_COUNT Klipper instances were found!"
      else
        echo -e "| 1 Klipper instance was found!                         | "
      fi
      echo -e "| You need one Moonraker instance per Klipper instance. | "
      bottom_border
      echo
      read -p "${cyan}###### Create $INSTANCE_COUNT Moonraker instances? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Creating $INSTANCE_COUNT Moonraker instances ..."
          moonraker_setup
          break;;
        N|n|No|no)
          echo -e "###### > No"
          warn_msg "Exiting Moonraker setup ..."
          echo
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
  done
}

moonraker_setup(){
  ### checking dependencies
  dep=(wget curl unzip dfu-util virtualenv)
  ### additional deps for kiauh compatibility for armbian
  dep+=(libjpeg-dev zlib1g-dev)
  dependency_check

  ### step 1: clone moonraker
  status_msg "Downloading Moonraker ..."
  ### force remove existing moonraker dir and clone into fresh moonraker dir
  [ -d $MOONRAKER_DIR ] && rm -rf $MOONRAKER_DIR
  cd ${HOME} && git clone $MOONRAKER_REPO
  ok_msg "Download complete!"

  ### step 2: install moonraker dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_moonraker_packages
  create_moonraker_virtualenv

  ### step 3: create moonraker.conf folder and moonraker.confs
  create_moonraker_conf

  ### step 4: create final moonraker instances
  create_moonraker_service

  ### confirm message
  CONFIRM_MSG="$INSTANCE_COUNT Moonraker instances have been set up!"
  [ $INSTANCE_COUNT -eq 1 ] && CONFIRM_MSG="Moonraker has been set up!"
  print_msg && clear_msg

  ### display moonraker ips to the user
  print_mr_ip_list; echo
}

install_moonraker_packages(){
  ### read PKGLIST from official install script
  status_msg "Reading dependencies..."
  install_script="${HOME}/moonraker/scripts/install-moonraker.sh"
  PKGLIST=$(grep "PKGLIST=" $install_script | sed 's/PKGLIST//g; s/[$={}\n"]//g')
  ### rewrite packages into new array
  unset PKGARR
  for PKG in $PKGLIST; do PKGARR+=($PKG); done
  echo "${cyan}${PKGARR[@]}${default}"

  ### Update system package info
  status_msg "Running apt-get update..."
  sudo apt-get update --allow-releaseinfo-change

  ### Install desired packages
  status_msg "Installing packages..."
  sudo apt-get install --yes ${PKGARR[@]}
}

create_moonraker_virtualenv(){
  status_msg "Installing python virtual environment..."

  ### If venv exists and user prompts a rebuild, then do so
  if [ -d ${MOONRAKER_ENV} ] && [ $REBUILD_ENV = "y" ]; then
    status_msg "Removing old virtualenv"
    rm -rf ${MOONRAKER_ENV}
  fi

  if [ ! -d ${MOONRAKER_ENV} ]; then
    virtualenv -p /usr/bin/python3 ${MOONRAKER_ENV}
    ln -s /usr/lib/python3/dist-packages/gpiod* ${MOONRAKER_ENV}/lib/python*/site-packages
  fi

  ### Install/update dependencies
  ${MOONRAKER_ENV}/bin/pip install -r ${MOONRAKER_DIR}/scripts/moonraker-requirements.txt
}

create_moonraker_service(){
  ### get config directory
  source_kiauh_ini

  ### set up default values
  SINGLE_INST=1
  CFG_PATH="$klipper_cfg_loc"
  MR_ENV=$MOONRAKER_ENV
  MR_DIR=$MOONRAKER_DIR
  MR_LOG="${HOME}/klipper_logs/moonraker.log"
  MR_CONF="$CFG_PATH/moonraker.conf"
  MR_SERV_SRC="${SRCDIR}/kiauh/resources/moonraker.service"
  MR_SERV_TARGET="$SYSTEMDDIR/moonraker.service"

  write_mr_service(){
    if [ ! -f $MR_SERV_TARGET ]; then
      status_msg "Creating Moonraker Service $i ..."
        sudo cp $MR_SERV_SRC $MR_SERV_TARGET
        sudo sed -i "s|%INST%|$i|" $MR_SERV_TARGET
        sudo sed -i "s|%USER%|${USER}|" $MR_SERV_TARGET
        sudo sed -i "s|%MR_ENV%|$MR_ENV|" $MR_SERV_TARGET
        sudo sed -i "s|%MR_DIR%|$MR_DIR|" $MR_SERV_TARGET
        sudo sed -i "s|%MR_LOG%|$MR_LOG|" $MR_SERV_TARGET
        sudo sed -i "s|%MR_CONF%|$MR_CONF|" $MR_SERV_TARGET
    fi
  }

  if [ $SINGLE_INST -eq $INSTANCE_COUNT ]; then
    ### write single instance service
    write_mr_service
    ### enable instance
    sudo systemctl enable moonraker.service
    ok_msg "Single Moonraker instance created!"
    ### launching instance
    status_msg "Launching Moonraker instance ..."
    sudo systemctl start moonraker
  else
    i=1
    while [ $i -le $INSTANCE_COUNT ]; do
      ### rewrite default variables for multi instance cases
      CFG_PATH="$klipper_cfg_loc/printer_$i"
      MR_SERV_TARGET="$SYSTEMDDIR/moonraker-$i.service"
      MR_CONF="$CFG_PATH/moonraker.conf"
      MR_LOG="${HOME}/klipper_logs/moonraker-$i.log"
      ### write multi instance service
      write_mr_service
      ### enable instance
      sudo systemctl enable moonraker-$i.service
      ok_msg "Moonraker instance #$i created!"
      ### launching instance
      status_msg "Launching Moonraker instance #$i ..."
      sudo systemctl start moonraker-$i

      ### raise values by 1
      i=$((i+1))
    done
    unset i

    ### enable mainsails remoteMode if mainsail is found
    if [ -d $MAINSAIL_DIR ]; then
      status_msg "Mainsail installation found!"
      status_msg "Enabling Mainsail remoteMode ..."
      enable_mainsail_remotemode
      ok_msg "Mainsails remoteMode enabled!"
    fi
  fi
}

create_moonraker_conf(){
  ### get config directory
  source_kiauh_ini

  ### set up default values
  SINGLE_INST=1
  PORT=7125
  CFG_PATH="$klipper_cfg_loc"
  LOG_PATH="${HOME}/klipper_logs"
  MR_CONF="$CFG_PATH/moonraker.conf"
  MR_DB="~/.moonraker_database"
  KLIPPY_UDS="/tmp/klippy_uds"
  MR_CONF_SRC="${SRCDIR}/kiauh/resources/moonraker.conf"
  mr_ip_list=()
  IP=$(hostname -I | cut -d" " -f1)
  LAN="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  write_mr_conf(){
    [ ! -d $CFG_PATH ] && mkdir -p $CFG_PATH
    if [ ! -f $MR_CONF ]; then
      status_msg "Creating moonraker.conf in $CFG_PATH ..."
        cp $MR_CONF_SRC $MR_CONF
        sed -i "s|%PORT%|$PORT|" $MR_CONF
        sed -i "s|%CFG%|$CFG_PATH|" $MR_CONF
        sed -i "s|%LOG%|$LOG_PATH|" $MR_CONF
        sed -i "s|%MR_DB%|$MR_DB|" $MR_CONF
        sed -i "s|%UDS%|$KLIPPY_UDS|" $MR_CONF
        # if host ip is not in the default ip ranges, replace placeholder
        # otherwise remove placeholder from config
        if ! grep $LAN $MR_CONF; then
          sed -i "s|%LAN%|$LAN|" $MR_CONF
        else
          sed -i "/%LAN%/d" $MR_CONF
        fi
        sed -i "s|%USER%|${USER}|g" $MR_CONF
      ok_msg "moonraker.conf created!"
    else
      warn_msg "There is already a file called 'moonraker.conf'!"
      warn_msg "Skipping..."
    fi
  }

  if [ $SINGLE_INST -eq $INSTANCE_COUNT ]; then
    ### write single instance config
    write_mr_conf
    mr_ip_list+=("$IP:$PORT")
  else
    i=1
    while [ $i -le $INSTANCE_COUNT ]; do
      ### rewrite default variables for multi instance cases
      CFG_PATH="$klipper_cfg_loc/printer_$i"
      MR_CONF="$CFG_PATH/moonraker.conf"
      MR_DB="~/.moonraker_database_$i"
      KLIPPY_UDS="/tmp/klippy_uds-$i"

      ### write multi instance config
      write_mr_conf
      mr_ip_list+=("$IP:$PORT")

      ### raise values by 1
      PORT=$((PORT+1))
      i=$((i+1))
    done
    unset PORT && unset i
  fi
}

print_mr_ip_list(){
  i=1
  for ip in ${mr_ip_list[@]}; do
    echo -e "       ${cyan}● Instance $i:${default} $ip"
    i=$((i + 1))
  done
}
