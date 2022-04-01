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
