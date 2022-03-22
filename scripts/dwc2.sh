#!/bin/bash

#=======================================================================#
# Copyright (C) 2020 - 2022 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

### global variables
SYSTEMD="/etc/systemd/system"
DWC_ENV_DIR=${HOME}/dwc-env
DWC2FK_DIR=${HOME}/dwc2-for-klipper-socket
DWC2_DIR=${HOME}/duetwebcontrol
DWC2FK_REPO=https://github.com/Stephan3/dwc2-for-klipper-socket.git
KLIPPER_CONFIG="${HOME}/klipper_config"

#=================================================#
#================= INSTALL DWC2 ==================#
#=================================================#

system_check_dwc(){
  ### check system for an installed octoprint service
  if systemctl is-enabled octoprint.service -q 2>/dev/null; then
    OCTOPRINT_ENABLED="true"
  fi
}

dwc_setup_dialog(){
  status_msg "Initializing Duet Web Control installation ..."

  ### check system for several requirements before initializing the dwc2 installation
  system_check_dwc

  ### check for existing klipper service installations
  if [ ! "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ] && [ ! "$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service")" ]; then
    ERROR_MSG="Klipper service not found, please install Klipper first!" && return 0
  fi

  ### count amount of klipper services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    INSTANCE_COUNT=1
  else
    INSTANCE_COUNT=$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service" | wc -l)
  fi

  ### initial config path check
  check_klipper_cfg_path

  ### ask user how to handle OctoPrint, Haproxy and Lighttpd
  process_octoprint_dialog_dwc2
  process_services_dialog

  ### instance confirmation dialog
  while true; do
      echo
      top_border
      if [ "$INSTANCE_COUNT" -gt 1 ]; then
        printf "|%-55s|\n" " $INSTANCE_COUNT Klipper instances were found!"
      else
        echo -e "| 1 Klipper instance was found!                         | "
      fi
      echo -e "| You need one DWC instance per Klipper instance.       | "
      bottom_border
      echo
      read -p "${cyan}###### Create $INSTANCE_COUNT DWC instances? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Creating $INSTANCE_COUNT DWC instances ..."
          dwc_setup
          break;;
        N|n|No|no)
          echo -e "###### > No"
          warn_msg "Exiting DWC setup ..."
          echo
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
  done
}

###TODO for future: should be some kind of shared function between moonraker and this installer, since it does the same
process_octoprint_dialog_dwc2(){
  ### ask user to disable octoprint when its service was found
  if [ "$OCTOPRINT_ENABLED" = "true" ]; then
    while true; do
      echo
      top_border
      echo -e "|       ${red}!!! WARNING - OctoPrint service found !!!${default}       |"
      hr
      echo -e "|  You might consider disabling the OctoPrint service,  |"
      echo -e "|  since an active OctoPrint service may lead to unex-  |"
      echo -e "|  pected behavior of Duet Web Control for Klipper.     |"
      bottom_border
      read -p "${cyan}###### Do you want to disable OctoPrint now? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          echo -e "###### > Yes"
          status_msg "Stopping OctoPrint ..."
          sudo systemctl stop octoprint && ok_msg "OctoPrint service stopped!"
          status_msg "Disabling OctoPrint ..."
          sudo systemctl disable octoprint && ok_msg "OctoPrint service disabled!"
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
  status_msg "Installation will start now! Please wait ..."
}

#############################################################
#############################################################

get_dwc_ver(){
  DWC2_VERSION=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep tag_name | cut -d'"' -f4)
}

dwc_setup(){
  ### get printer config directory
  source_kiauh_ini
  DWC_CONF_LOC="$klipper_cfg_loc"

  ### check dependencies
  dep=(git wget gzip tar curl)
  dependency_check

  ### step 1: get dwc2-for-klipper
  status_msg "Downloading DWC2-for-Klipper-Socket ..."
  cd "${HOME}" && git clone "$DWC2FK_REPO"
  ok_msg "Download complete!"

  ### step 2: install dwc2 dependencies and create python virtualenv
  status_msg "Installing dependencies ..."
  install_dwc_packages
  create_dwc_virtualenv

  ### step 3: create dwc2.cfg folder and dwc2.cfg
  [ ! -d "$DWC_CONF_LOC" ] && mkdir -p "$DWC_CONF_LOC"
  dwc_cfg_creation

  ### step 4: download Duet Web Control
  download_dwc_webui

  ### step 5: create dwc instances
  INSTANCE=1
  if [ "$INSTANCE_COUNT" -eq $INSTANCE ]; then
    create_single_dwc_instance
  else
    #create_multi_dwc_instance
    create_multi_dwc_instance
  fi
}

download_dwc_webui(){
  #get Duet Web Control
  GET_DWC2_URL=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4)
  status_msg "Downloading DWC2 Web UI ..."
  [ ! -d "$DWC2_DIR" ] && mkdir -p "$DWC2_DIR"
  cd "$DWC2_DIR" && wget "$GET_DWC2_URL"
  ok_msg "Download complete!"
  status_msg "Extracting archive ..."
  unzip -q -o *.zip
  for f_ in $(find . | grep '.gz')
  do
    gunzip -f "${f_}"
  done
  ok_msg "Done!"
  status_msg "Writing DWC version to file ..."
  echo "$GET_DWC2_URL" | cut -d/ -f8 > "$DWC2_DIR/.version"
  ok_msg "Done!"
  status_msg "Remove downloaded archive ..."
  rm -rf *.zip && ok_msg "Done!" && ok_msg "Duet Web Control installed!"
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

install_dwc_packages()
{
    PKGLIST="python3-virtualenv python3-dev python3-tornado"

    # Update system package info
    status_msg "Running apt-get update..."
    sudo apt-get update --allow-releaseinfo-change

    # Install desired packages
    status_msg "Installing packages..."
    sudo apt-get install --yes "${PKGLIST}"
}

create_dwc_virtualenv()
{
    status_msg "Installing python virtual environment..."

    # Create virtualenv if it doesn't already exist
    [ ! -d "${DWC_ENV}" ] && virtualenv -p /usr/bin/python3 "${DWC_ENV}"

    # Install/update dependencies
    "${DWC_ENV}"/bin/pip install tornado==6.0.4
}

create_single_dwc_startscript(){
  ### create systemd service file
  sudo /bin/sh -c "cat > ${SYSTEMDDIR}/dwc.service" << DWC
[Unit]
Description=DuetWebControl
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${USER}
RemainAfterExit=yes
ExecStart=${DWC_ENV}/bin/python3 ${DWC2FK_DIR}/web_dwc2.py -l ${DWC_LOG} -c ${DWC_CFG}
Restart=always
RestartSec=10
DWC
}

create_multi_dwc_startscript(){
  ### create systemd service file
  sudo /bin/sh -c "cat > ${SYSTEMDDIR}/dwc-$INSTANCE.service" << DWC
[Unit]
Description=DuetWebControl
After=network.target
[Install]
WantedBy=multi-user.target
[Service]
Type=simple
User=${USER}
RemainAfterExit=yes
ExecStart=${DWC_ENV}/bin/python3 ${DWC2FK_DIR}/web_dwc2.py -l ${DWC_LOG} -c ${DWC_CFG}
Restart=always
RestartSec=10
DWC
}

create_single_dwcfk_cfg(){
### create single instance config file
/bin/sh -c "cat > $DWC_CONF_LOC/dwc2.cfg" << DWCCFG
[webserver]
listen_adress: 0.0.0.0
web_root: ${HOME}/duetwebcontrol
port: ${PORT}

[reply_filters]
regex:
    max_accel: \d+.\d+
    max_accel_to_decel: \d+.\d+
    square_corner_velocity: \d+.\d+
    max_velocity: \d+.\d+
DWCCFG
}

create_multi_dwcfk_cfg(){
### create single instance config file
/bin/sh -c "cat > $DWC_CONF_LOC/printer_$INSTANCE/dwc2.cfg" << DWCCFG
[webserver]
listen_adress: 0.0.0.0
web_root: ${HOME}/duetwebcontrol
port: ${PORT}

[reply_filters]
regex:
    max_accel: \d+.\d+
    max_accel_to_decel: \d+.\d+
    square_corner_velocity: \d+.\d+
    max_velocity: \d+.\d+
DWCCFG
}

##############################################################################################
#********************************************************************************************#
##############################################################################################

print_dwc_ip_list(){
  i=1
  for ip in ${dwc_ip_list[@]}; do
    echo -e "       ${cyan}● Instance $i:${default} $ip"
    i=$((i + 1))
  done
}

create_single_dwc_instance(){
  status_msg "Setting up 1 Duet Web Control instance ..."

  ### single instance variables
  DWC_LOG=/tmp/dwc.log
  DWC_CFG="$DWC_CONF_LOC/dwc2.cfg"

  ### create instance
  status_msg "Creating single DWC instance ..."
  create_single_dwc_startscript

  ### enable instance
  sudo systemctl enable dwc.service
  ok_msg "Single DWC instance created!"

  ### launching instance
  status_msg "Launching DWC instance ..."
  sudo systemctl start dwc

  ### confirm message
  CONFIRM_MSG="Single DWC instance has been set up!"
  print_msg && clear_msg

  ### display moonraker ip to the user
  print_dwc_ip_list; echo
}

create_multi_dwc_instance(){
  status_msg "Setting up $INSTANCE_COUNT instances of Duet Web Control ..."
  while [ $INSTANCE -le "$INSTANCE_COUNT" ]; do
    ### multi instance variables
    DWC_LOG=/tmp/dwc-$INSTANCE.log
    DWC_CFG="$DWC_CONF_LOC/printer_$INSTANCE/dwc2.cfg"

    ### create instance
    status_msg "Creating instance #$INSTANCE ..."
    create_multi_dwc_startscript

    ### enable instance
    sudo systemctl enable dwc-$INSTANCE.service
    ok_msg "DWC instance $INSTANCE created!"

    ### launching instance
    status_msg "Launching DWC instance $INSTANCE ..."
    sudo systemctl start dwc-$INSTANCE

    ### instance counter +1
    INSTANCE=$(expr $INSTANCE + 1)
  done

  ### confirm message
  CONFIRM_MSG="$INSTANCE_COUNT DWC instances has been set up!"
  print_msg && clear_msg

  ### display moonraker ip to the user
  print_dwc_ip_list; echo
}

dwc_cfg_creation(){
  ### default dwc port
  DEFAULT_PORT=4750

  ### get printer config directory
  source_kiauh_ini
  DWC_CONF_LOC="$klipper_cfg_loc"

  ### reset instances back to 1 again
  INSTANCE=1

  ### declare empty array for ips which get displayed to the user at the end of the setup
  HOSTNAME=$(hostname -I | cut -d" " -f1)
  dwc_ip_list=()

  ### create single instance dwc2.cfg file
  if [ "$INSTANCE_COUNT" -eq $INSTANCE ]; then
    ### set port
    PORT=$DEFAULT_PORT

    ### write the ip and port to the ip list for displaying it later to the user
    dwc_ip_list+=("$HOSTNAME:$PORT")

    status_msg "Creating dwc2.cfg in $DWC_CONF_LOC"
    [ ! -d "$DWC_CONF_LOC" ] && mkdir -p "$DWC_CONF_LOC"
    if [ ! -f "$DWC_CONF_LOC/dwc2.cfg" ]; then
      create_single_dwcfk_cfg && ok_msg "dwc2.cfg created!"
    else
      warn_msg "There is already a file called 'dwc2.cfg'!"
      warn_msg "Skipping..."
    fi

  ### create multi instance moonraker.conf files
  else
    while [ $INSTANCE -le "$INSTANCE_COUNT" ]; do
      ### set each instance to its own port
      PORT=$(expr $DEFAULT_PORT + $INSTANCE - 1)

      ### write the ip and port to the ip list for displaying it later to the user
      dwc_ip_list+=("$HOSTNAME:$PORT")

      ### start the creation of each instance
      status_msg "Creating dwc2.cfg for instance #$INSTANCE"
      [ ! -d "$DWC_CONF_LOC/printer_$INSTANCE" ] && mkdir -p "$DWC_CONF_LOC/printer_$INSTANCE"
      if [ ! -f "$DWC_CONF_LOC/printer_$INSTANCE/dwc2.cfg" ]; then
        create_multi_dwcfk_cfg && ok_msg "dwc2.cfg created!"
      else
        warn_msg "There is already a file called 'dwc2.cfg'!"
        warn_msg "Skipping..."
      fi

      ### raise instance counter by 1
      INSTANCE=$(expr $INSTANCE + 1)
    done
  fi
}

#=================================================#
#================= REMOVE DWC2 ===================#
#=================================================#

remove_dwc2(){
  ### remove "legacy" init.d service
  if [ -e /etc/init.d/dwc ]; then
    status_msg "Removing DWC2-for-Klipper-Socket Service ..."
    sudo systemctl stop dwc
    sudo update-rc.d -f dwc remove
    sudo rm -f /etc/init.d/dwc
    sudo rm -f /etc/default/dwc
    ok_msg "DWC2-for-Klipper-Socket Service removed!"
  fi

  ### remove all dwc services
  if ls /etc/systemd/system/dwc*.service 2>/dev/null 1>&2; then
    status_msg "Removing DWC2-for-Klipper-Socket Services ..."
    for service in $(ls /etc/systemd/system/dwc*.service | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "Done!"
    done
    ### reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "DWC2-for-Klipper-Socket Service removed!"
  fi

  ### remove all logfiles
  if ls /tmp/dwc*.log 2>/dev/null 1>&2; then
    for logfile in $(ls /tmp/dwc*.log)
    do
      status_msg "Removing $logfile ..."
      rm -f $logfile
      ok_msg "File '$logfile' removed!"
    done
  fi

  ### removing the rest of the folders
  if [ -d $DWC2FK_DIR ]; then
    status_msg "Removing DWC2-for-Klipper-Socket directory ..."
    rm -rf $DWC2FK_DIR && ok_msg "Directory removed!"
  fi
  if [ -d $DWC_ENV_DIR ]; then
    status_msg "Removing DWC2-for-Klipper-Socket virtualenv ..."
    rm -rf $DWC_ENV_DIR && ok_msg "Directory removed!"
  fi
  if [ -d $DWC2_DIR ]; then
    status_msg "Removing DWC2 directory ..."
    rm -rf $DWC2_DIR && ok_msg "Directory removed!"
  fi

  ### remove dwc2_port from ~/.kiauh.ini
  sed -i "/^dwc2_port=/d" $INI_FILE

  CONFIRM_MSG=" DWC2-for-Klipper-Socket was successfully removed!"
}

#=================================================#
#================= UPDATE DWC2 ===================#
#=================================================#

update_dwc2fk(){
  do_action_service "stop" "dwc"
  bb4u "dwc2"
  if [ ! -d $DWC2FK_DIR ]; then
    cd ${HOME} && git clone $DWC2FK_REPO
  else
    cd $DWC2FK_DIR && git pull
  fi
  do_action_service "start" "dwc"
}

update_dwc2(){
  bb4u "dwc2"
  download_dwc_webui
}

#=================================================#
#================= DWC2 STATUS ===================#
#=================================================#

dwc2_status(){
  dcount=0
  dwc_data=(
    SERVICE
    $DWC2_DIR
    $DWC2FK_DIR
    $DWC_ENV_DIR
  )

  ### count amount of dwc service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "^dwc(\-[[:digit:]]+)?\.service$" | wc -l)

  ### remove the "SERVICE" entry from the dwc_data array if a dwc service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset dwc_data[0]

  #count+1 for each found data-item from array
  for dd in "${dwc_data[@]}"
  do
    if [ -e $dd ]; then
      dcount=$(expr $dcount + 1)
    fi
  done

  if [ "$dcount" == "${#dwc_data[*]}" ]; then
    DWC2_STATUS="$(printf "${green}Installed: %-5s${default}" $SERVICE_FILE_COUNT)"
  elif [ "$dcount" == 0 ]; then
    DWC2_STATUS="${red}Not installed!${default}  "
  else
    DWC2_STATUS="${yellow}Incomplete!${default}     "
  fi
}

read_dwc2fk_versions(){
  if [ -d $DWC2FK_DIR ] && [ -d $DWC2FK_DIR/.git ]; then
    cd $DWC2FK_DIR
    git fetch origin master -q
    LOCAL_DWC2FK_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_DWC2FK_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_DWC2FK_COMMIT=$NONE
    REMOTE_DWC2FK_COMMIT=$NONE
  fi
}

compare_dwc2fk_versions(){
  unset DWC2FK_UPDATE_AVAIL
  read_dwc2fk_versions
  if [ "$LOCAL_DWC2FK_COMMIT" != "$REMOTE_DWC2FK_COMMIT" ]; then
    LOCAL_DWC2FK_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_DWC2FK_COMMIT")${default}"
    REMOTE_DWC2FK_COMMIT="${green}$(printf "%-12s" "$REMOTE_DWC2FK_COMMIT")${default}"
    # add dwc2fk to the update all array for the update all function in the updater
    DWC2FK_UPDATE_AVAIL="true" && update_arr+=(update_dwc2fk)
  else
    LOCAL_DWC2FK_COMMIT="${green}$(printf "%-12s" "$LOCAL_DWC2FK_COMMIT")${default}"
    REMOTE_DWC2FK_COMMIT="${green}$(printf "%-12s" "$REMOTE_DWC2FK_COMMIT")${default}"
    DWC2FK_UPDATE_AVAIL="false"
  fi
}

read_local_dwc2_version(){
  unset DWC2_VER_FOUND
  if [ -e $DWC2_DIR/.version ]; then
    DWC2_VER_FOUND="true"
    DWC2_LOCAL_VER=$(head -n 1 $DWC2_DIR/.version)
  else
    DWC2_VER_FOUND="false" && unset DWC2_LOCAL_VER
  fi
}

read_remote_dwc2_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    DWC2_REMOTE_VER=$NONE
  else
    get_dwc_ver
    DWC2_REMOTE_VER=$DWC2_VERSION
  fi
}

compare_dwc2_versions(){
  unset DWC2_UPDATE_AVAIL
  read_local_dwc2_version && read_remote_dwc2_version
  if [[ $DWC2_VER_FOUND = "true" ]] && [[ $DWC2_LOCAL_VER == $DWC2_REMOTE_VER ]]; then
    #printf fits the string for displaying it in the ui to a total char length of 12
    DWC2_LOCAL_VER="${green}$(printf "%-12s" "$DWC2_LOCAL_VER")${default}"
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
  elif [[ $DWC2_VER_FOUND = "true" ]] && [[ $DWC2_LOCAL_VER != $DWC2_REMOTE_VER ]]; then
    DWC2_LOCAL_VER="${yellow}$(printf "%-12s" "$DWC2_LOCAL_VER")${default}"
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
    # add dwc to the update all array for the update all function in the updater
    DWC2_UPDATE_AVAIL="true" && update_arr+=(update_dwc2)
  else
    DWC2_LOCAL_VER=$NONE
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
    DWC2_UPDATE_AVAIL="false"
  fi
}