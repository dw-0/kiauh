### base variables
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_ENV="${HOME}/moonraker-env"
MOONRAKER_DIR="${HOME}/moonraker"

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

  ### check for existing moonraker service installations
  if ls /etc/systemd/system/moonraker*.service 2>/dev/null 1>&2; then
    ERROR_MSG="At least one Moonraker service is already installed!" && return 0
  fi

  ### check for existing klipper service installations
  if ! ls /etc/systemd/system/klipper*.service 2>/dev/null 1>&2; then
    ERROR_MSG="Klipper service not found, please install Klipper first!" && return 0
  fi

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
  ### get printer config directory
  source_kiauh_ini
  MOONRAKER_CONF_LOC="$klipper_cfg_loc"

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
  [ ! -d $MOONRAKER_CONF_LOC ] && mkdir -p $MOONRAKER_CONF_LOC
  moonraker_conf_creation

  ### step 4: set up moonrakers nginx configs
  setup_moonraker_nginx_cfg

  ### step 5: process possible disruptive services
  process_haproxy_lighttpd_services

  ### step 6: create final moonraker instances
  INSTANCE=1
  if [ $INSTANCE_COUNT -eq $INSTANCE ]; then
    create_single_moonraker_instance
  else
    create_multi_moonraker_instance
    ### step 6.5: enable mainsails remoteMode if its already installed
    if [ -d $MAINSAIL_DIR ]; then
      enable_mainsail_remotemode
    fi
  fi
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

install_moonraker_packages(){
  PKGLIST="python3-virtualenv python3-dev nginx libopenjp2-7 python3-libgpiod"

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

  [ ! -d ${MOONRAKER_ENV} ] && virtualenv -p /usr/bin/python3 --system-site-packages ${MOONRAKER_ENV}

  ### Install/update dependencies
  ${MOONRAKER_ENV}/bin/pip install -r ${MOONRAKER_DIR}/scripts/moonraker-requirements.txt
}

create_single_moonraker_startscript(){
### create systemd service file
sudo /bin/sh -c "cat > ${SYSTEMDDIR}/moonraker.service" << EOF
#Systemd service file for moonraker
[Unit]
Description=Starts Moonraker on startup
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${USER}
RemainAfterExit=yes
ExecStart=${MOONRAKER_ENV}/bin/python ${MOONRAKER_DIR}/moonraker/moonraker.py -l ${MOONRAKER_LOG} -c ${MOONRAKER_CONF}
Restart=always
RestartSec=10
EOF
}

create_multi_moonraker_startscript(){
### create multi instance systemd service file
sudo /bin/sh -c "cat > ${SYSTEMDDIR}/moonraker-$INSTANCE.service" << EOF
#Systemd service file for moonraker
[Unit]
Description=Starts Moonraker instance $INSTANCE on startup
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${USER}
RemainAfterExit=yes
ExecStart=${MOONRAKER_ENV}/bin/python ${MOONRAKER_DIR}/moonraker/moonraker.py -l ${MOONRAKER_LOG} -c ${MOONRAKER_CONF}
Restart=always
RestartSec=10
EOF
}

create_single_moonraker_conf(){
  HOSTNAME=$(hostname -I | cut -d" " -f1)
  LOCAL_NETWORK="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  /bin/sh -c "cat > $MOONRAKER_CONF_LOC/moonraker.conf" << MOONRAKERCONF
[server]
host: 0.0.0.0
port: $PORT
enable_debug_logging: False
config_path: $PRINTER_CFG_LOC
klippy_uds_address: /tmp/klippy_uds

[authorization]
enabled: True
api_key_file: ~/.moonraker_api_key
trusted_clients:
    127.0.0.1
    $LOCAL_NETWORK
    ::1/128
    FE80::/10
cors_domains:
    *.local
    *://my.mainsail.xyz
    *://app.fluidd.xyz

[octoprint_compat]

[update_manager]

[update_manager client mainsail]
type: web
repo: meteyou/mainsail
path: ~/mainsail

[update_manager client fluidd]
type: web
repo: cadriel/fluidd
path: ~/fluidd

#[update_manager client KlipperScreen]
#type: git_repo
#path: /home/${HOME}/KlipperScreen
#origin: https://github.com/jordanruthe/KlipperScreen.git
#env: /home/${HOME}/.KlipperScreen-env/bin/python
#requirements: scripts/KlipperScreen-requirements.txt
#install_script: scripts/KlipperScreen-install.sh
MOONRAKERCONF
}

create_multi_moonraker_conf(){
  HOSTNAME=$(hostname -I | cut -d" " -f1)
  LOCAL_NETWORK="$(hostname -I | cut -d" " -f1 | cut -d"." -f1-2).0.0/16"

  /bin/sh -c "cat > $MOONRAKER_CONF_LOC/printer_$INSTANCE/moonraker.conf" << MOONRAKERCONF
[server]
host: 0.0.0.0
port: $PORT
enable_debug_logging: False
config_path: $PRINTER_CFG_LOC/printer_$INSTANCE
klippy_uds_address: /tmp/klippy_uds-$INSTANCE

[authorization]
enabled: True
api_key_file: ~/.moonraker_api_key
trusted_clients:
    127.0.0.1
    $LOCAL_NETWORK
    ::1/128
    FE80::/10
cors_domains:
    *.local
    *://my.mainsail.xyz
    *://app.fluidd.xyz

[octoprint_compat]

[update_manager]

[update_manager client mainsail]
type: web
repo: meteyou/mainsail
path: ~/mainsail

[update_manager client fluidd]
type: web
repo: cadriel/fluidd
path: ~/fluidd

#[update_manager client KlipperScreen]
#type: git_repo
#path: /home/${USER}/KlipperScreen
#origin: https://github.com/jordanruthe/KlipperScreen.git
#env: /home/${USER}/.KlipperScreen-env/bin/python
#requirements: scripts/KlipperScreen-requirements.txt
#install_script: scripts/KlipperScreen-install.sh
MOONRAKERCONF
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

print_mr_ip_list(){
  i=1
  for ip in ${mr_ip_list[@]}; do
    echo -e "       ${cyan}● Instance $i:${default} $ip"
    i=$((i + 1))
  done
}

create_single_moonraker_instance(){
  status_msg "Setting up 1 Moonraker instance ..."

  ### single instance variables
  MOONRAKER_LOG=/tmp/moonraker.log
  MOONRAKER_CONF="$MOONRAKER_CONF_LOC/moonraker.conf"

  ### create instance
  status_msg "Creating single Moonraker instance ..."
  create_single_moonraker_startscript

  ### enable instance
  sudo systemctl enable moonraker.service
  ok_msg "Single Moonraker instance created!"

  ### launching instance
  status_msg "Launching Moonraker instance ..."
  sudo systemctl start moonraker

  ### confirm message
  CONFIRM_MSG="Single Moonraker instance has been set up!"
  print_msg && clear_msg

  ### display moonraker ip to the user
  print_mr_ip_list; echo
}

create_multi_moonraker_instance(){
  status_msg "Setting up $INSTANCE_COUNT instances of Moonraker ..."
  while [ $INSTANCE -le $INSTANCE_COUNT ]; do
    ### multi instance variables
    MOONRAKER_LOG=/tmp/moonraker-$INSTANCE.log
    MOONRAKER_CONF="$MOONRAKER_CONF_LOC/printer_$INSTANCE/moonraker.conf"

    ### create instance
    status_msg "Creating instance #$INSTANCE ..."
    create_multi_moonraker_startscript

    ### enable instance
    sudo systemctl enable moonraker-$INSTANCE.service
    ok_msg "Moonraker instance $INSTANCE created!"

    ### launching instance
    status_msg "Launching Moonraker instance $INSTANCE ..."
    sudo systemctl start moonraker-$INSTANCE

    ### instance counter +1
    INSTANCE=$(expr $INSTANCE + 1)
  done

  ### confirm message
  CONFIRM_MSG="$INSTANCE_COUNT Moonraker instances have been set up!"
  print_msg && clear_msg

  ### display all moonraker ips to the user
  print_mr_ip_list; echo
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

moonraker_conf_creation(){
  ### default moonraker port
  DEFAULT_PORT=7125

  ### get printer and moonraker config directory
  source_kiauh_ini
  PRINTER_CFG_LOC="$klipper_cfg_loc"
  MOONRAKER_CONF_LOC="$klipper_cfg_loc"

  ### reset instances back to 1 again
  INSTANCE=1

  ### declare empty array for ips which get displayed to the user at the end of the setup
  HOSTNAME=$(hostname -I | cut -d" " -f1)
  mr_ip_list=()

  ### create single instance moonraker.conf file
  if [ $INSTANCE_COUNT -eq $INSTANCE ]; then
    ### set port
    PORT=$DEFAULT_PORT

    ### write the ip and port to the ip list for displaying it later to the user
    mr_ip_list+=("$HOSTNAME:$PORT")

    status_msg "Creating moonraker.conf in $MOONRAKER_CONF_LOC"
    [ ! -d $MOONRAKER_CONF_LOC ] && mkdir -p $MOONRAKER_CONF_LOC
    if [ ! -f $MOONRAKER_CONF_LOC/moonraker.conf ]; then
      create_single_moonraker_conf && ok_msg "moonraker.conf created!"
    else
      warn_msg "There is already a file called 'moonraker.conf'!"
      warn_msg "Skipping..."
    fi

  ### create multi instance moonraker.conf files
  else
    while [ $INSTANCE -le $INSTANCE_COUNT ]; do
      ### set each instance to its own port
      PORT=$(expr $DEFAULT_PORT + $INSTANCE - 1)

      ### write the ip and port to the ip list for displaying it later to the user
      mr_ip_list+=("$HOSTNAME:$PORT")

      ### start the creation of each instance
      status_msg "Creating moonraker.conf for instance #$INSTANCE"
      [ ! -d $MOONRAKER_CONF_LOC/printer_$INSTANCE ] && mkdir -p $MOONRAKER_CONF_LOC/printer_$INSTANCE
      if [ ! -f $MOONRAKER_CONF_LOC/printer_$INSTANCE/moonraker.conf ]; then
        create_multi_moonraker_conf && ok_msg "moonraker.conf created!"
      else
        warn_msg "There is already a file called 'moonraker-$INSTANCE.conf'!"
        warn_msg "Skipping..."
      fi

      ### raise instance counter by 1
      INSTANCE=$(expr $INSTANCE + 1)
    done
  fi
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

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
