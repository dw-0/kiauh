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
      status_msg "Removing Klipper Service ..."
      sudo update-rc.d -f klipper remove
      sudo rm -rf /etc/init.d/klipper /etc/default/klipper && ok_msg "Klipper Service removed!"
    fi
    if [[ -d $KLIPPER_DIR || -d $KLIPPY_ENV_DIR ]]; then
      status_msg "Removing Klipper and klippy-env directory ..."
      rm -rf $KLIPPER_DIR $KLIPPY_ENV_DIR && ok_msg "Directories removed!"
    fi
    if [[ -L ${HOME}/klippy.log || -e /tmp/klippy.log ]]; then
      status_msg "Removing klippy.log Symlink ..."
      rm -rf ${HOME}/klippy.log /tmp/klippy.log && ok_msg "Symlink removed!"
    fi
    CONFIRM_MSG=" Klipper successfully removed!"
  fi
}

remove_dwc2(){
  data_arr=(
  $TORNADO_DIR1
  $TORNADO_DIR2
  $DWC2FK_DIR
  $WEB_DWC2
  $DWC2_DIR
  )
  print_error "DWC2-for-Klipper &\n DWC2 Web UI" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    if [ -d $TORNADO_DIR1 ]; then
    status_msg "Removing Tornado from klippy-env ..."
    PYTHONDIR=$KLIPPY_ENV_DIR
    $PYTHONDIR/bin/pip uninstall tornado -y
    CONFIRM_MSG=" Tornado successfully removed!"
    fi
    if [ -d $DWC2FK_DIR ]; then
      status_msg "Removing DWC2-for-Klipper directory ..."
      rm -rf $DWC2FK_DIR && ok_msg "Directory removed!"
    fi
    if [ -e $WEB_DWC2 ]; then
      status_msg "Removing web_dwc2.py Symlink from klippy ..."
      rm -rf $WEB_DWC2 && ok_msg "File removed!"
    fi
    if [ -d $DWC2_DIR ]; then
      status_msg "Removing DWC2 directory ..."
      rm -rf $DWC2_DIR && ok_msg "Directory removed!"
    fi
    CONFIRM_MSG=" DWC2-for-Klipper & DWC2 Web UI successfully removed!"
  fi
}

remove_moonraker(){
  data_arr=(
  $MOONRAKER_SERVICE1
  $MOONRAKER_SERVICE2
  $MOONRAKER_DIR
  $MOONRAKER_ENV_DIR
  ${HOME}/moonraker.conf
  ${HOME}/moonraker.log
  ${HOME}/klipper_config/moonraker.log
  ${HOME}/klipper_config/klippy.log
  ${HOME}/.klippy_api_key
  ${HOME}/.moonraker_api_key
  )
  print_error "Moonraker" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    if [ -e ${HOME}/moonraker.conf ]; then
      unset REMOVE_MOONRAKER_CONF
      while true; do
        echo
        read -p "${cyan}###### Delete moonraker.conf? (Y/n):${default} " yn
        case "$yn" in
          Y|y|Yes|yes|"")
            echo -e "###### > Yes"
            REMOVE_MOONRAKER_CONF="true"
            break;;
          N|n|No|no)
            echo -e "###### > No"
            REMOVE_MOONRAKER_CONF="false"
            break;;
        esac
      done
    fi
    status_msg "Processing ..."
    stop_moonraker
    #remove moonraker services
    if [[ -e /etc/init.d/moonraker || -e /etc/default/moonraker ]]; then
      status_msg "Removing Moonraker Service ..."
      sudo update-rc.d -f moonraker remove
      sudo rm -rf /etc/init.d/moonraker /etc/default/moonraker && ok_msg "Moonraker Service removed!"
    fi
    #remove moonraker and moonraker-env dir
    if [[ -d $MOONRAKER_DIR || -d $MOONRAKER_ENV_DIR ]]; then
      status_msg "Removing Moonraker and moonraker-env directory ..."
      rm -rf $MOONRAKER_DIR $MOONRAKER_ENV_DIR && ok_msg "Directories removed!"
    fi
    #remove moonraker.conf
    if [ "$REMOVE_MOONRAKER_CONF" = "true" ]; then
      status_msg "Removing moonraker.conf ..."
      rm -rf ${HOME}/moonraker.conf && ok_msg "File removed!"
    fi
    #remove moonraker.log and symlink
    if [[ -L ${HOME}/moonraker.log || -L ${HOME}/klipper_config/moonraker.log || -L ${HOME}/klipper_config/klippy.log || -e /tmp/moonraker.log ]]; then
      status_msg "Removing Logs and Symlinks ..."
      rm -rf ${HOME}/moonraker.log ${HOME}/klipper_config/moonraker.log ${HOME}/klipper_config/klippy.log /tmp/moonraker.log
      ok_msg "Files removed!"
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
    CONFIRM_MSG="Moonraker successfully removed!"
  fi
}

remove_mainsail(){
  data_arr=(
  $MAINSAIL_DIR
  /etc/nginx/sites-available/mainsail
  /etc/nginx/sites-enabled/mainsail
  )
  print_error "Mainsail" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    #remove mainsail dir
    if [ -d $MAINSAIL_DIR ]; then
      status_msg "Removing Mainsail directory ..."
      rm -rf $MAINSAIL_DIR && ok_msg "Directory removed!"
    fi
    #remove mainsail config for nginx
    if [ -e /etc/nginx/sites-available/mainsail ]; then
      status_msg "Removing Mainsail configuration for Nginx ..."
      sudo rm /etc/nginx/sites-available/mainsail && ok_msg "File removed!"
    fi
    #remove mainsail symlink for nginx
    if [ -L /etc/nginx/sites-enabled/mainsail ]; then
      status_msg "Removing Mainsail Symlink for Nginx ..."
      sudo rm /etc/nginx/sites-enabled/mainsail && ok_msg "File removed!"
    fi
    CONFIRM_MSG="Mainsail successfully removed!"
  fi
}

remove_octoprint(){
  data_arr=(
  $OCTOPRINT_SERVICE1
  $OCTOPRINT_SERVICE2
  $OCTOPRINT_DIR
  $OCTOPRINT_CFG_DIR
  ${HOME}/octoprint.log
  /etc/sudoers.d/octoprint-shutdown
  /etc/nginx/sites-available/octoprint
  /etc/nginx/sites-enabled/octoprint
  )
  print_error "OctoPrint" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    stop_octoprint
    if [[ -e $OCTOPRINT_SERVICE1 || -e $OCTOPRINT_SERVICE2 ]]; then
      status_msg "Removing OctoPrint Service ..."
      sudo update-rc.d -f octoprint remove
      sudo rm -rf $OCTOPRINT_SERVICE1 $OCTOPRINT_SERVICE2 && ok_msg "OctoPrint Service removed!"
    fi
    if [[ -d $OCTOPRINT_DIR || -d $OCTOPRINT_CFG_DIR ]]; then
      status_msg "Removing OctoPrint and .octoprint directory ..."
      rm -rf $OCTOPRINT_DIR $OCTOPRINT_CFG_DIR && ok_msg "Directories removed!"
    fi
    if [ -f /etc/sudoers.d/octoprint-shutdown ]; then
      sudo rm -rf /etc/sudoers.d/octoprint-shutdown
    fi
    if [ -L ${HOME}/octoprint.log ]; then
      status_msg "Removing octoprint.log Symlink ..."
      rm -rf ${HOME}/octoprint.log && ok_msg "Symlink removed!"
    fi
    CONFIRM_MSG=" OctoPrint successfully removed!"
  fi
}

remove_nginx(){
  if [[ $(dpkg-query -f'${Status}' --show nginx 2>/dev/null) = *\ installed ]]  ; then
    if systemctl is-active nginx -q; then
      status_msg "Stopping Nginx service ..."
      sudo service nginx stop && sudo systemctl disable nginx
      ok_msg "Service stopped!"
    fi
    status_msg "Purging Nginx from system ..."
    sudo apt-get purge nginx nginx-common -y
    sudo update-rc.d -f nginx remove
    CONFIRM_MSG=" Nginx successfully removed!"
  else
    ERROR_MSG=" Looks like Nginx was already removed!\n Skipping..."
  fi
}