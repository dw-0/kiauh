### base variables
SYSTEMDDIR="/etc/systemd/system"

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

#############################################################
#############################################################

remove_mainsail(){
  ### remove mainsail dir
  if [ -d $MAINSAIL_DIR ]; then
    status_msg "Removing Mainsail directory ..."
    rm -rf $MAINSAIL_DIR && ok_msg "Directory removed!"
  fi

  ### remove mainsail config for nginx
  if [ -e /etc/nginx/sites-available/mainsail ]; then
    status_msg "Removing Mainsail configuration for Nginx ..."
    sudo rm /etc/nginx/sites-available/mainsail && ok_msg "File removed!"
  fi

  ### remove mainsail symlink for nginx
  if [ -L /etc/nginx/sites-enabled/mainsail ]; then
    status_msg "Removing Mainsail Symlink for Nginx ..."
    sudo rm /etc/nginx/sites-enabled/mainsail && ok_msg "File removed!"
  fi

  ### remove mainsail nginx logs and log symlinks
  for log in $(find /var/log/nginx -name "mainsail*"); do
    sudo rm -f $log
  done
  for log in $(find ${HOME}/klipper_logs -name "mainsail*"); do
    rm -f $log
  done

  ### remove mainsail_port from ~/.kiauh.ini
  sed -i "/^mainsail_port=/d" $INI_FILE

  CONFIRM_MSG="Mainsail successfully removed!"
}

remove_fluidd(){
  ### remove fluidd dir
  if [ -d $FLUIDD_DIR ]; then
    status_msg "Removing Fluidd directory ..."
    rm -rf $FLUIDD_DIR && ok_msg "Directory removed!"
  fi

  ### remove fluidd config for nginx
  if [ -e /etc/nginx/sites-available/fluidd ]; then
    status_msg "Removing Fluidd configuration for Nginx ..."
    sudo rm /etc/nginx/sites-available/fluidd && ok_msg "File removed!"
  fi

  ### remove fluidd symlink for nginx
  if [ -L /etc/nginx/sites-enabled/fluidd ]; then
    status_msg "Removing Fluidd Symlink for Nginx ..."
    sudo rm /etc/nginx/sites-enabled/fluidd && ok_msg "File removed!"
  fi

  ### remove mainsail nginx logs and log symlinks
  for log in $(find /var/log/nginx -name "fluidd*"); do
    sudo rm -f $log
  done
  for log in $(find ${HOME}/klipper_logs -name "fluidd*"); do
    rm -f $log
  done

  ### remove fluidd_port from ~/.kiauh.ini
  sed -i "/^fluidd_port=/d" $INI_FILE

  CONFIRM_MSG="Fluidd successfully removed!"
}

#############################################################
#############################################################

remove_octoprint(){
  ###remove all octoprint services
  if ls /etc/systemd/system/octoprint*.service 2>/dev/null 1>&2; then
    status_msg "Removing OctoPrint Services ..."
    for service in $(ls /etc/systemd/system/octoprint*.service | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "OctoPrint Service removed!"
    done
    ### reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
  fi

  ### remove sudoers file
  if [ -f /etc/sudoers.d/octoprint-shutdown ]; then
    sudo rm -rf /etc/sudoers.d/octoprint-shutdown
  fi

  ### remove OctoPrint directory
  if [ -d ${HOME}/OctoPrint ]; then
    status_msg "Removing OctoPrint directory ..."
    rm -rf ${HOME}/OctoPrint && ok_msg "Directory removed!"
  fi

  ###remove .octoprint directories
  if ls -d ${HOME}/.octoprint* 2>/dev/null 1>&2; then
    for folder in $(ls -d ${HOME}/.octoprint*)
    do
      status_msg "Removing $folder ..." && rm -rf $folder && ok_msg "Done!"
    done
  fi

  ### remove octoprint_port from ~/.kiauh.ini
  sed -i "/^octoprint_port=/d" $INI_FILE

  CONFIRM_MSG=" OctoPrint successfully removed!"
}

#############################################################
#############################################################

remove_nginx(){
  if ls /lib/systemd/system/nginx.service 2>/dev/null 1>&2; then
    status_msg "Stopping Nginx service ..."
    sudo systemctl stop nginx && sudo systemctl disable nginx
    ok_msg "Service stopped and disabled!"
    status_msg "Purging Nginx from system ..."
    sudo apt-get purge nginx nginx-common -y
    sudo update-rc.d -f nginx remove
    CONFIRM_MSG=" Nginx successfully removed!"
  else
    ERROR_MSG=" Looks like Nginx was already removed!\n Skipping..."
  fi
}

remove_mjpg-streamer(){
  ### remove MJPG-Streamer service
  if [ -e $SYSTEMDDIR/webcamd.service ]; then
    status_msg "Removing MJPG-Streamer service ..."
    sudo systemctl stop webcamd && sudo systemctl disable webcamd
    sudo rm -f $SYSTEMDDIR/webcamd.service
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
  if [ -d ${HOME}/mjpg-streamer ]; then
    status_msg "Removing MJPG-Streamer directory ..."
    rm -rf ${HOME}/mjpg-streamer
    ok_msg "MJPG-Streamer directory removed!"
  fi

  ### remove webcamd log and symlink
  [ -f "/var/log/webcamd.log" ] && sudo rm -f "/var/log/webcamd.log"
  [ -L "${HOME}/klipper_logs/webcamd.log" ] && rm -f "${HOME}/klipper_logs/webcamd.log"

  CONFIRM_MSG="MJPG-Streamer successfully removed!"
}

remove_prettygcode(){
  pgconf="/etc/nginx/sites-available/pgcode.local.conf"
  pgconfsl="/etc/nginx/sites-enabled/pgcode.local.conf"
  if [ -d ${HOME}/pgcode ] || [ -f $pgconf ] || [ -L $pgconfsl ]; then
    status_msg "Removing PrettyGCode for Klipper ..."
    rm -rf ${HOME}/pgcode
    sudo rm -f $pgconf
    sudo rm -f $pgconfsl
    sudo systemctl restart nginx
    CONFIRM_MSG="PrettyGCode for Klipper successfully removed!"
  else
    ERROR_MSG="PrettyGCode for Klipper not found!\n Skipping..."
  fi
}
