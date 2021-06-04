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

  ### check system for an installed and enabled octoprint service
  if systemctl list-unit-files | grep -E "octoprint.*" | grep "enabled" &>/dev/null; then
    OCTOPRINT_ENABLED="true"
  fi

  ### check system for an installed haproxy service
  if [[ $(dpkg-query -f'${Status}' --show haproxy 2>/dev/null) = *\ installed ]]; then
    HAPROXY_FOUND="true"
  fi

  ### check system for an installed lighttpd service
  if [[ $(dpkg-query -f'${Status}' --show lighttpd 2>/dev/null) = *\ installed ]]; then
    LIGHTTPD_FOUND="true"
  fi

}

moonraker_setup_dialog(){
  status_msg "Initializing Moonraker installation ..."

  ### check system for several requirements before initializing the moonraker installation
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
    INSTANCE_COUNT=$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service" | wc -l)
  fi

  ### initial moonraker.conf path check
  check_klipper_cfg_path

  ### ask user how to handle OctoPrint, Haproxy and Lighttpd
  process_octoprint_dialog
  process_haproxy_lighttpd_dialog

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
  dep=(wget curl unzip dfu-util)
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

  ### step 4: set up moonrakers nginx configs
  setup_moonraker_nginx_cfg

  ### step 5: process possible disruptive services
  process_haproxy_lighttpd_services

  # ### step 6: create final moonraker instances
  create_moonraker_service

  ### confirm message
  CONFIRM_MSG="$INSTANCE_COUNT Moonraker instances have been set up!"
  [ $INSTANCE_COUNT -eq 1 ] && CONFIRM_MSG="Moonraker has been set up!"
  print_msg && clear_msg

  ### display moonraker ips to the user
  print_mr_ip_list; echo
}

install_moonraker_packages(){
  PKGLIST="python3-virtualenv python3-dev nginx libopenjp2-7 python3-libgpiod"
  PKGLIST="${PKGLIST} liblmdb0 libsodium-dev zlib1g-dev"

  ### Update system package info
  status_msg "Running apt-get update..."
  sudo apt-get update

  ### Install desired packages
  status_msg "Installing packages..."
  sudo apt-get install --yes ${PKGLIST}
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
  MR_LOG="/tmp/moonraker.log"
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
      MR_LOG="/tmp/moonraker-$i.log"
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
        sed -i "s|%MR_DB%|$MR_DB|" $MR_CONF
        sed -i "s|%UDS%|$KLIPPY_UDS|" $MR_CONF
        sed -i "s|%LAN%|$LAN|" $MR_CONF
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

setup_moonraker_nginx_cfg(){
  get_date

  ### backup existing nginx configs
  [ -f $NGINX_CONFD/upstreams.conf ] && sudo mv $NGINX_CONFD/upstreams.conf $NGINX_CONFD/$current_date_upstreams.conf
  [ -f $NGINX_CONFD/common_vars.conf ] && sudo mv $NGINX_CONFD/common_vars.conf $NGINX_CONFD/$current_date_common_vars.conf

  ### copy nginx configs to target destination
  if [ ! -f $NGINX_CONFD/upstreams.conf ]; then
    sudo cp ${SRCDIR}/kiauh/resources/upstreams.conf $NGINX_CONFD
  fi
  if [ ! -f $NGINX_CONFD/common_vars.conf ]; then
    sudo cp ${SRCDIR}/kiauh/resources/common_vars.conf $NGINX_CONFD
  fi
}

process_octoprint_dialog(){
  #ask user to disable octoprint when its service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "|       ${red}!!! WARNING - OctoPrint service found !!!${default}       |"
      hr
      echo -e "|  You might consider disabling the OctoPrint service,  |"
      echo -e "|  since an active OctoPrint service may lead to unex-  |"
      echo -e "|  pected behavior of the Klipper Webinterfaces.        |"
      bottom_border
      read -p "${cyan}###### Do you want to disable OctoPrint now? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Stopping OctoPrint ..."
          octoprint_service "stop" && ok_msg "OctoPrint service stopped!"
          status_msg "Disabling OctoPrint ..."
          octoprint_service "disable" && ok_msg "OctoPrint service disabled!"
          break;;
        N|n|No|no)
          echo -e "###### > No"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}

process_haproxy_lighttpd_services(){
  #handle haproxy service
  if [ "$DISABLE_HAPROXY" = "true" ] || [ "$REMOVE_HAPROXY" = "true" ]; then
    if systemctl is-active haproxy -q; then
      status_msg "Stopping haproxy service ..."
      sudo systemctl stop haproxy && ok_msg "Service stopped!"
    fi

    ### disable haproxy
    if [ "$DISABLE_HAPROXY" = "true" ]; then
      status_msg "Disabling haproxy ..."
      sudo systemctl disable haproxy && ok_msg "Haproxy service disabled!"

      ### remove haproxy
      if [ "$REMOVE_HAPROXY" = "true" ]; then
        status_msg "Removing haproxy ..."
        sudo apt-get remove haproxy -y && sudo update-rc.d -f haproxy remove && ok_msg "Haproxy removed!"
      fi
    fi
  fi

  ### handle lighttpd service
  if [ "$DISABLE_LIGHTTPD" = "true" ] || [ "$REMOVE_LIGHTTPD" = "true" ]; then
    if systemctl is-active lighttpd -q; then
      status_msg "Stopping lighttpd service ..."
      sudo systemctl stop lighttpd && ok_msg "Service stopped!"
    fi

    ### disable lighttpd
    if [ "$DISABLE_LIGHTTPD" = "true" ]; then
      status_msg "Disabling lighttpd ..."
      sudo systemctl disable lighttpd && ok_msg "Lighttpd service disabled!"

      ### remove lighttpd
      if [ "$REMOVE_LIGHTTPD" = "true" ]; then
        status_msg "Removing lighttpd ..."
        sudo apt-get remove lighttpd -y && sudo update-rc.d -f lighttpd remove && ok_msg "Lighttpd removed!"
      fi
    fi
  fi
}

process_haproxy_lighttpd_dialog(){
  #notify user about haproxy or lighttpd services found and possible issues
  if [ "$HAPROXY_FOUND" = "true" ] || [ "$LIGHTTPD_FOUND" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "| ${red}Possibly disruptive/incompatible services found!${default}      |"
      hr
      if [ "$HAPROXY_FOUND" = "true" ]; then
        echo -e "| ● haproxy                                             |"
      fi
      if [ "$LIGHTTPD_FOUND" = "true" ]; then
        echo -e "| ● lighttpd                                            |"
      fi
      hr
      echo -e "| Having those packages installed can lead to unwanted  |"
      echo -e "| behaviour. It is recommend to remove those packages.  |"
      echo -e "|                                                       |"
      echo -e "| 1) Remove packages (recommend)                        |"
      echo -e "| 2) Disable only (may cause issues)                    |"
      echo -e "| ${red}3) Skip this step (not recommended)${default}                   |"
      bottom_border
      read -p "${cyan}###### Please choose:${default} " action
      case "$action" in
        1)
          echo -e "###### > Remove packages"
          if [ "$HAPROXY_FOUND" = "true" ]; then
            DISABLE_HAPROXY="true"
            REMOVE_HAPROXY="true"
          fi
          if [ "$LIGHTTPD_FOUND" = "true" ]; then
            DISABLE_LIGHTTPD="true"
            REMOVE_LIGHTTPD="true"
          fi
          break;;
        2)
          echo -e "###### > Disable only"
          if [ "$HAPROXY_FOUND" = "true" ]; then
            DISABLE_HAPROXY="true"
            REMOVE_HAPROXY="false"
          fi
          if [ "$LIGHTTPD_FOUND" = "true" ]; then
            DISABLE_LIGHTTPD="true"
            REMOVE_LIGHTTPD="false"
          fi
          break;;
        3)
          echo -e "###### > Skip"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    done
  fi
}
