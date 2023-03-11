#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/th33xitus/kiauh                                    #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e

#=================================================#
#============= INSTALL MJPG-STREAMER =============#
#=================================================#

function install_mjpg-streamer() {
  local webcamd="${KIAUH_SRCDIR}/resources/mjpg-streamer/webcamd"
  local webcam_txt="${KIAUH_SRCDIR}/resources/mjpg-streamer/webcam.txt"
  local service="${KIAUH_SRCDIR}/resources/mjpg-streamer/webcamd.service"
  local repo="https://github.com/jacksonliam/mjpg-streamer.git"

  ### return early if webcamd.service already exists
  if [[ -f "${SYSTEMD}/webcamd.service" ]]; then
    print_error "Looks like MJPG-streamer is already installed!\n Please remove it first before you try to re-install it!"
    return
  fi

  status_msg "Initializing MJPG-Streamer installation ..."

  ### check and install dependencies if missing
  local dep=(git cmake build-essential imagemagick libv4l-dev ffmpeg)
  if apt-cache search libjpeg62-turbo-dev | grep -Eq "^libjpeg62-turbo-dev "; then
    dep+=(libjpeg62-turbo-dev)
  elif apt-cache search libjpeg8-dev | grep -Eq "^libjpeg8-dev "; then
    dep+=(libjpeg8-dev)
  fi

  dependency_check "${dep[@]}"

  ### step 1: clone mjpg-streamer
  status_msg "Cloning MJPG-Streamer from ${repo} ..."
  [[ -d "${HOME}/mjpg-streamer" ]] && rm -rf "${HOME}/mjpg-streamer"

  cd "${HOME}" || exit 1
  if ! git clone "${repo}" "${HOME}/mjpg-streamer"; then
    print_error "Cloning MJPG-Streamer from\n ${repo}\n failed!"
    exit 1
  fi
  ok_msg "Cloning complete!"

  ### step 2: compiling mjpg-streamer
  status_msg "Compiling MJPG-Streamer ..."
  cd "${HOME}/mjpg-streamer/mjpg-streamer-experimental"
  if ! make; then
    print_error "Compiling MJPG-Streamer failed!"
    exit 1
  fi
  ok_msg "Compiling complete!"

  #step 3: install mjpg-streamer
  status_msg "Installing MJPG-Streamer ..."
  cd "${HOME}/mjpg-streamer" && mv mjpg-streamer-experimental/* .
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

  sudo cp "${webcamd}" "/usr/local/bin/webcamd"
  sudo sed -i "/^config_dir=/ s|=.*|=${KLIPPER_CONFIG}|" /usr/local/bin/webcamd
  sudo sed -i "/MJPGSTREAMER_HOME/ s/pi/${USER}/" /usr/local/bin/webcamd
  sudo chmod +x /usr/local/bin/webcamd

  ### step 4: create webcam.txt config file
  [[ ! -d ${KLIPPER_CONFIG} ]] && mkdir -p "${KLIPPER_CONFIG}"
  if [[ ! -f "${KLIPPER_CONFIG}/webcam.txt" ]]; then
    status_msg "Creating webcam.txt config file ..."
    cp "${webcam_txt}" "${KLIPPER_CONFIG}/webcam.txt"
    ok_msg "Done!"
  fi

  ### step 5: create systemd service
  status_msg "Creating MJPG-Streamer service ..."
  sudo cp "${service}" "${SYSTEMD}/webcamd.service"
  sudo sed -i "s|%USER%|${USER}|" "${SYSTEMD}/webcamd.service"
  ok_msg "MJPG-Streamer service created!"

  ### step 6: enabling and starting mjpg-streamer service
  status_msg "Starting MJPG-Streamer service, please wait ..."
  sudo systemctl enable webcamd.service
  if sudo systemctl start webcamd.service; then
    ok_msg "MJPG-Streamer service started!"
  else
    status_msg "MJPG-Streamer service couldn't be started! No webcam connected?\n###### You need to manually restart the service once your webcam is set up correctly."
  fi

  ### step 6.1: create webcamd.log symlink
  [[ ! -d ${KLIPPER_LOGS} ]] && mkdir -p "${KLIPPER_LOGS}"
  if [[ -f "/var/log/webcamd.log" && ! -L "${KLIPPER_LOGS}/webcamd.log" ]]; then
    ln -s "/var/log/webcamd.log" "${KLIPPER_LOGS}/webcamd.log"
  fi

  ### step 6.2: add webcamd.log logrotate
  if [[ ! -f "/etc/logrotate.d/webcamd"  ]]; then
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
  local usergroup_changed="false"
  if ! groups "${USER}" | grep -q "video"; then
    status_msg "Adding user '${USER}' to group 'video' ..."
    sudo usermod -a -G video "${USER}" && ok_msg "Done!"
    usergroup_changed="true"
  fi

  ### confirm message
  local confirm_msg="MJPG-Streamer has been set up!"
  if [[ ${usergroup_changed} == "true" ]]; then
    confirm_msg="${confirm_msg}\n ${yellow}INFO: Your User was added to a new group!${green}"
    confirm_msg="${confirm_msg}\n ${yellow}You need to relog/restart for the group to be applied!${green}"
  fi

  print_confirm "${confirm_msg}"

  ### print webcam ip adress/url
  local ip
  ip=$(hostname -I | cut -d" " -f1)
  local cam_url="http://${ip}:8080/?action=stream"
  local cam_url_alt="http://${ip}/webcam/?action=stream"
  echo -e " ${cyan}● Webcam URL:${white} ${cam_url}"
  echo -e " ${cyan}● Webcam URL:${white} ${cam_url_alt}"
  echo
}

#=================================================#
#============== REMOVE MJPG-STREAMER =============#
#=================================================#

function remove_mjpg-streamer() {
  ### remove MJPG-Streamer service
  if [[ -e "${SYSTEMD}/webcamd.service" ]]; then
    status_msg "Removing MJPG-Streamer service ..."
    sudo systemctl stop webcamd && sudo systemctl disable webcamd
    sudo rm -f "${SYSTEMD}/webcamd.service"
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "MJPG-Streamer Service removed!"
  fi

  ### remove webcamd from /usr/local/bin
  if [[ -e "/usr/local/bin/webcamd" ]]; then
    sudo rm -f "/usr/local/bin/webcamd"
  fi

  ### remove MJPG-Streamer directory
  if [[ -d "${HOME}/mjpg-streamer" ]]; then
    status_msg "Removing MJPG-Streamer directory ..."
    rm -rf "${HOME}/mjpg-streamer"
    ok_msg "MJPG-Streamer directory removed!"
  fi

  ### remove webcamd log and symlink
  [[ -f "/var/log/webcamd.log" ]] && sudo rm -f "/var/log/webcamd.log"
  [[ -L "${KLIPPER_LOGS}/webcamd.log" ]] && rm -f "${KLIPPER_LOGS}/webcamd.log"

  print_confirm "MJPG-Streamer successfully removed!"
}