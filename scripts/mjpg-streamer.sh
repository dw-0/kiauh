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

### base variables
SYSTEMD="/etc/systemd/system"
WEBCAMD_SRC="https://raw.githubusercontent.com/mainsail-crew/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/usr/local/bin/webcamd"
WEBCAM_TXT_SRC="https://raw.githubusercontent.com/mainsail-crew/MainsailOS/master/src/modules/mjpgstreamer/filesystem/home/pi/klipper_config/webcam.txt"

#=================================================#
#============= INSTALL MJPG-STREAMER =============#
#=================================================#

function install_mjpg-streamer(){
  check_klipper_cfg_path
  source_kiauh_ini

  ### set default values
  MJPG_SERV_SRC="${SRCDIR}/kiauh/resources/webcamd.service"
  MJPG_SERV_TARGET="${SYSTEMD}/webcamd.service"
  WEBCAM_TXT="${KLIPPER_CONFIG}/webcam.txt"

  ### if there is a webcamd.service -> exit
  if [ -f "${MJPG_SERV_TARGET}" ]; then
    ERROR_MSG="Looks like MJPG-streamer is already installed!\n Please remove it first before you try to re-install it!"
    print_msg && clear_msg && return
  fi

  ### check and install dependencies if missing
  dep=(git cmake build-essential imagemagick libv4l-dev ffmpeg)
  if apt-cache search libjpeg62-turbo-dev | grep -Eq "^libjpeg62-turbo-dev "; then
    dep+=(libjpeg62-turbo-dev)
  elif apt-cache search libjpeg8-dev | grep -Eq "^libjpeg8-dev "; then
    dep+=(libjpeg8-dev)
  fi
  dependency_check

  ### step 1: clone moonraker
  status_msg "Downloading MJPG-Streamer ..."
  cd "${HOME}" && git clone https://github.com/jacksonliam/mjpg-streamer.git
  ok_msg "Download complete!"

  ### step 2: compiling mjpg-streamer
  status_msg "Compiling MJPG-Streamer ..."
  cd "${HOME}"/mjpg-streamer/mjpg-streamer-experimental && make
  ok_msg "Compiling complete!"

  #step 3: install mjpg-streamer
  status_msg "Installing MJPG-Streamer ..."
  cd "${HOME}"/mjpg-streamer && mv mjpg-streamer-experimental/* .
  mkdir www-mjpgstreamer
  cat <<EOT >> ./www-mjpgstreamer/index.html
<html>
<head><title>mjpg_streamer test page</title></head>
<body>
<h1>Snapshot</h1>
<p>Refresh the page to refresh the snapshot</p>
<img src="./?action=snapshot" alt="Snapshot">
<h1>Stream</h1>
<img src="./?action=stream" alt="Stream">
</body>
</html>
EOT
  sudo wget "${WEBCAMD_SRC}" -O "/usr/local/bin/webcamd"
  sudo sed -i "/^config_dir=/ s|=.*|=${KLIPPER_CONFIG}|" /usr/local/bin/webcamd
  sudo sed -i "/MJPGSTREAMER_HOME/ s/pi/${USER}/" /usr/local/bin/webcamd
  sudo chmod +x /usr/local/bin/webcamd

  ### step 4: create webcam.txt config file
  [ ! -d "${KLIPPER_CONFIG}" ] && mkdir -p "${KLIPPER_CONFIG}"
  if [ ! -f "${WEBCAM_TXT}" ]; then
    status_msg "Creating webcam.txt config file ..."
    wget "${WEBCAM_TXT_SRC}" -O "${WEBCAM_TXT}"
    ok_msg "Done!"
  fi

  ### step 5: create systemd service
  status_msg "Creating MJPG-Streamer service ..."
  sudo cp "${MJPG_SERV_SRC}" "${MJPG_SERV_TARGET}"
  sudo sed -i "s|%USER%|${USER}|" "${MJPG_SERV_TARGET}"
  ok_msg "MJPG-Streamer service created!"

  ### step 6: enabling and starting mjpg-streamer service
  status_msg "Starting MJPG-Streamer service ..."
  sudo systemctl enable webcamd.service
  sudo systemctl start webcamd.service
  ok_msg "MJPG-Streamer service started!"

  ### step 6.1: create webcamd.log symlink
  [ ! -d "${HOME}/klipper_logs" ] && mkdir -p "${HOME}/klipper_logs"
  if [ -f "/var/log/webcamd.log" ] && [ ! -L "${HOME}/klipper_logs/webcamd.log" ]; then
    ln -s "/var/log/webcamd.log" "${HOME}/klipper_logs/webcamd.log"
  fi

  ### step 6.2: add webcamd.log logrotate
  if [ ! -f "/etc/logrotate.d/webcamd"  ]; then
    status_msg "Create logrotate rule ..."
    sudo /bin/sh -c "cat > /etc/logrotate.d/webcamd" << EOF
/var/log/webcamd.log
{
    rotate 2
    weekly
    maxsize 32M
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
}
EOF
     ok_msg "Done!"
  fi

  ### step 7: check if user is in group "video"
  usergroup_changed=false
  USER_IN_VIDEO_GROUP=$(groups "${USER}" | grep "video")
  if [ -z "${USER_IN_VIDEO_GROUP}" ]; then
    status_msg "Adding user ${USER} to group 'video' ..."
    sudo usermod -a -G video "${USER}" && ok_msg "Done!"
    usergroup_changed=true
  else
    ok_msg "User ${USER} already in group 'video'!"
  fi

  ### confirm message
  CONFIRM_MSG="MJPG-Streamer has been set up!"
  if [ "${usergroup_changed}" == true ]; then
    CONFIRM_MSG="${CONFIRM_MSG}\n ${yellow}INFO: Your User was added to a new group!${green}"
    CONFIRM_MSG="${CONFIRM_MSG}\n ${yellow}You need to relog/restart for the group to be applied!${green}"
  fi
  print_msg && clear_msg

  ### print webcam ip adress/url
  IP=$(hostname -I | cut -d" " -f1)
  WEBCAM_IP="http://${IP}:8080/?action=stream"
  WEBCAM_URL="http://${IP}/webcam/?action=stream"
  echo -e " ${cyan}● Webcam URL:${white} ${WEBCAM_IP}"
  echo -e " ${cyan}● Webcam URL:${white} ${WEBCAM_URL}"
  echo
}

function get_user_selection_mjpg-streamer(){
  while true; do
    unset INSTALL_MJPG
    echo
    top_border
    echo -e "|  Install MJGP-Streamer for webcam support?            |"
    bottom_border
    read -p "${cyan}###### Install MJPG-Streamer? (Y/n):${white} " yn
    case "${yn}" in
      Y|y|Yes|yes|"")
        echo -e "###### > Yes"
        INSTALL_MJPG="true"
        break;;
      N|n|No|no)
        echo -e "###### > No"
        INSTALL_MJPG="false"
        break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
}

#=================================================#
#============== REMOVE MJPG-STREAMER =============#
#=================================================#

function remove_mjpg-streamer(){
  ### remove MJPG-Streamer service
  if [ -e "${SYSTEMD}/webcamd.service" ]; then
    status_msg "Removing MJPG-Streamer service ..."
    sudo systemctl stop webcamd && sudo systemctl disable webcamd
    sudo rm -f "${SYSTEMD}/webcamd.service"
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "MJPG-Streamer Service removed!"
  fi

  ### remove webcamd from /usr/local/bin
  if [ -e "/usr/local/bin/webcamd" ]; then
    sudo rm -f "/usr/local/bin/webcamd"
  fi

  ### remove MJPG-Streamer directory
  if [ -d "${HOME}/mjpg-streamer" ]; then
    status_msg "Removing MJPG-Streamer directory ..."
    rm -rf "${HOME}/mjpg-streamer"
    ok_msg "MJPG-Streamer directory removed!"
  fi

  ### remove webcamd log and symlink
  [ -f "/var/log/webcamd.log" ] && sudo rm -f "/var/log/webcamd.log"
  [ -L "${HOME}/klipper_logs/webcamd.log" ] && rm -f "${HOME}/klipper_logs/webcamd.log"

  CONFIRM_MSG="MJPG-Streamer successfully removed!"
}