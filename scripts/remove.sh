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
  $DWC2FK_DIR
  $TORNADO_DIR1
  $TORNADO_DIR2
  $WEB_DWC2
  $DWC2_DIR
  )
  print_error "DWC2-for-Klipper &\n DWC2 Web UI" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    if [ -d $DWC2FK_DIR ]; then
      status_msg "Removing DWC2-for-Klipper directory ..."
      rm -rf $DWC2FK_DIR && ok_msg "Directory removed!"
    fi
    if [ -d $TORNADO_DIR1 ]; then
      status_msg "Removing Tornado from klippy-env ..."
      rm -rf $TORNADO_DIR1 $TORNADO_DIR2 && ok_msg "Tornado removed!"
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

remove_mainsail(){
  data_arr=(
  $MOONRAKER_SERVICE1
  $MOONRAKER_SERVICE2
  $MAINSAIL_DIR
  ${HOME}/moonraker.log
  ${HOME}/.klippy_api_key
  ${HOME}/.moonraker_api_key
  ${HOME}/moonraker-env
  /etc/nginx/sites-available/mainsail
  /etc/nginx/sites-enabled/mainsail
  )
  print_error "Mainsail" && data_count=()
  if [ "$ERROR_MSG" = "" ]; then
    stop_moonraker
    #remove moonraker services
    if [[ -e /etc/init.d/moonraker || -e /etc/default/moonraker ]]; then
      status_msg "Removing Moonraker Service ..."
      sudo update-rc.d -f moonraker remove
      sudo rm -rf /etc/init.d/moonraker /etc/default/moonraker && ok_msg "Moonraker Service removed!"
    fi
    #remove mainsail dir
    if [ -d $MAINSAIL_DIR ]; then
      status_msg "Removing Mainsail directory ..."
      rm -rf $MAINSAIL_DIR && ok_msg "Directory removed!"
    fi
    #remove moonraker-env
    if [ -d ${HOME}/moonraker-env ]; then
      status_msg "Removing Moonraker virtualenv ..."
      rm -rf ${HOME}/moonraker-env && ok_msg "Directory removed!"
    fi
    #remove moonraker.log symlink
    if [[ -L ${HOME}/moonraker.log || -e /tmp/moonraker.log ]]; then
      status_msg "Removing moonraker.log Symlink ..."
      rm -rf ${HOME}/moonraker.log /tmp/moonraker.log && ok_msg "Symlink removed!"
    fi
    #remove mainsail cfg
    if [ -e /etc/nginx/sites-available/mainsail ]; then
      status_msg "Removing Mainsail configuration for Nginx ..."
      sudo rm /etc/nginx/sites-available/mainsail && ok_msg "File removed!"
    fi
    #remove mainsail symlink
    if [ -L /etc/nginx/sites-enabled/mainsail ]; then
      status_msg "Removing Mainsail Symlink for Nginx ..."
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
    CONFIRM_MSG=" Mainsail successfully removed!"
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