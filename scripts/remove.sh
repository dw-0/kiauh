remove_klipper(){
  data_arr=(
  /etc/init.d/klipper
  /etc/default/klipper
  $KLIPPER_DIR
  $KLIPPY_ENV_DIR
  ${HOME}/klippy.log
  )
  print_error "Klipper" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    stop_klipper
    if [[ -e /etc/init.d/klipper || -e /etc/default/klipper ]]; then
      status_msg "Removing klipper service ..."
      sudo update-rc.d -f klipper remove
      sudo rm -rf /etc/init.d/klipper /etc/default/klipper && ok_msg "Klipper service removed!"
    fi
    if [[ -d $KLIPPER_DIR || -d $KLIPPY_ENV_DIR ]]; then
      status_msg "Removing klipper and klippy-env diretory ..."
      rm -rf $KLIPPER_DIR $KLIPPY_ENV_DIR && ok_msg "Directories removed!"
    fi
    if [[ -L ${HOME}/klippy.log || -e /tmp/klippy.log ]]; then
      status_msg "Removing klippy.log symlink ..."
      rm -rf ${HOME}/klippy.log /tmp/klippy.log && ok_msg "Symlink removed!"
    fi
    ok_msg "Klipper successfully removed!"
  fi
}

remove_dwc2(){
  data_arr=(
  $DWC2FK_DIR
  $TORNADO_DIR1
  $TORNADO_DIR2
  $WEB_DWC2
  $DWC2_DIR
  )
  print_error "DWC2-for-Klipper &\n DWC2 Web UI" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    if [ -d $DWC2FK_DIR ]; then
      status_msg "Removing dwc2-for-klipper directory ..."
      rm -rf $DWC2FK_DIR && ok_msg "Directory removed!"
    fi
    if [ -d $TORNADO_DIR1 ]; then
      status_msg "Removing tornado from klippy-env ..."
      rm -rf $TORNADO_DIR1 $TORNADO_DIR2 && ok_msg "Tornado removed!"
    fi
    if [ -e $WEB_DWC2 ]; then
      status_msg "Removing web_dwc2.py symlink from klippy ..."
      rm -rf $WEB_DWC2 && ok_msg "File removed!"
    fi
    if [ -d $DWC2_DIR ]; then
      status_msg "Removing dwc2 directory ..."
      rm -rf $DWC2_DIR && ok_msg "Directory removed!"
    fi
    ok_msg "DWC2-for-Klipper & DWC2 Web UI successfully removed!"
  fi
}

remove_mainsail(){
  data_arr=(
  $MAINSAIL_SERVICE1
  $MAINSAIL_SERVICE2
  $MAINSAIL_DIR
  ${HOME}/moonraker.log
  ${HOME}/.klippy_api_key
  ${HOME}/.moonraker_api_key
  ${HOME}/moonraker-env
  /etc/nginx/sites-available/mainsail
  /etc/nginx/sites-enabled/mainsail
  /etc/init.d/nginx
  /etc/default/nginx
  )
  print_error "Mainsail" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    stop_moonraker
    #remove moonraker services
    if [[ -e /etc/init.d/moonraker || -e /etc/default/moonraker ]]; then
      status_msg "Removing moonraker service ..."
      sudo update-rc.d -f moonraker remove
      sudo rm -rf /etc/init.d/moonraker /etc/default/moonraker && ok_msg "Moonraker service removed!"
    fi
    #remove mainsail dir
    if [ -d $MAINSAIL_DIR ]; then
      status_msg "Removing mainsail directory ..."
      rm -rf $MAINSAIL_DIR && ok_msg "Directory removed!"
    fi
    #remove moonraker-env
    if [ -d ${HOME}/moonraker-env ]; then
      status_msg "Removing moonraker virtualenv ..."
      rm -rf ${HOME}/moonraker-env && ok_msg "Directory removed!"
    fi
    #remove moonraker.log symlink
    if [[ -L ${HOME}/moonraker.log || -e /tmp/moonraker.log ]]; then
      status_msg "Removing moonraker.log symlink ..."
      rm -rf ${HOME}/moonraker.log /tmp/moonraker.log && ok_msg "Symlink removed!"
    fi
    #remove mainsail cfg
    if [ -e /etc/nginx/sites-available/mainsail ]; then
      status_msg "Removing mainsail configuration for nginx ..."
      sudo rm /etc/nginx/sites-available/mainsail && ok_msg "File removed!"
    fi
    #remove mainsail symlink
    if [ -L /etc/nginx/sites-enabled/mainsail ]; then
      status_msg "Removing mainsail symlink for nginx ..."
      sudo rm /etc/nginx/sites-enabled/mainsail && ok_msg "File removed!"
    fi
    #remove legacy api key
    if [ -e ${HOME}/.klippy_api_key ]; then
      status_msg "Removing legacy API Key ..."
      rm ${HOME}/.klippy_api_key && ok_msg "Done!"
    fi
    #remove api key
    if [ -e ${HOME}/.moonraker_api_key ]; then
      status_msg "Removing API Key ..."
      rm ${HOME}/.moonraker_api_key && ok_msg "Done!"
    fi
    remove_nginx
    ok_msg "Mainsail successfully removed!"
  fi
}

remove_nginx(){
  #ask for complete removal of nginx if installed
  if [[ $(dpkg-query -f'${Status}' --show nginx 2>/dev/null) = *\ installed ]]  ; then
    while true; do
      echo
      read -p "Do you want to completely remove (purge) nginx? (Y/n): " yn
      case "$yn" in
        Y|y|Yes|yes|"")
        status_msg "Stopping and removing nginx service ..."
        if [ -e /etc/init.d/nginx ]; then
          sudo /etc/init.d/nginx stop && ok_msg "Nginx service stopped!"
          sudo rm /etc/init.d/nginx && ok_msg "Nginx service removed!"
        fi
        if [ -e /etc/default/nginx ]; then
          sudo rm /etc/default/nginx
        fi
        status_msg "Purging nginx from system ..."
        sudo apt-get purge nginx nginx-common -y && ok_msg "Nginx removed!"
        break;;
        N|n|No|no) break;;
      esac
    done
  fi
}