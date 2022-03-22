### base variables
SYSTEMDDIR="/etc/systemd/system"

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
