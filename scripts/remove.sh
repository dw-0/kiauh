### base variables
SYSTEMDDIR="/etc/systemd/system"

remove_klipper(){
  ### ask the user if he wants to uninstall moonraker too.
  ###? currently usefull if the user wants to switch from single-instance to multi-instance
  if ls /etc/systemd/system/moonraker*.service 2>/dev/null 1>&2; then
    while true; do
      unset REM_MR
      top_border
      echo -e "| Do you want to remove Moonraker afterwards?           |"
      echo -e "|                                                       |"
      echo -e "| This is useful in case you want to switch from a      |"
      echo -e "| single-instance to a multi-instance installation,     |"
      echo -e "| which makes a re-installation of Moonraker necessary. |"
      echo -e "|                                                       |"
      echo -e "| If for any other reason you only want to uninstall    |"
      echo -e "| Klipper, please select 'No' and continue.             |"
      bottom_border
      read -p "${cyan}###### Remove Moonraker afterwards? (y/N):${default} " yn
      case "$yn" in
        Y|y|Yes|yes)
          echo -e "###### > Yes"
          REM_MR="true"
          break;;
        N|n|No|no|"")
          echo -e "###### > No"
          REM_MR="false"
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
    esac
    done
  fi

  ### remove "legacy" klipper init.d service
  if [ -e /etc/init.d/klipper ]; then
    status_msg "Removing Klipper Service ..."
    sudo systemctl stop klipper
    sudo update-rc.d -f klipper remove
    sudo rm -f /etc/init.d/klipper
    sudo rm -f /etc/default/klipper
    ok_msg "Klipper Service removed!"
  fi

  ### remove all klipper services
  if ls /etc/systemd/system/klipper*.service 2>/dev/null 1>&2; then
    status_msg "Removing Klipper Services ..."
    for service in $(ls /etc/systemd/system/klipper*.service | cut -d"/" -f5)
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
    ok_msg "Klipper Service removed!"
  fi

  ### remove all logfiles
  if ls /tmp/klippy*.log 2>/dev/null 1>&2; then
    for logfile in $(ls /tmp/klippy*.log)
    do
      status_msg "Removing $logfile ..."
      rm -f $logfile
      ok_msg "File '$logfile' removed!"
    done
  fi

  ### remove all UDS
  if ls /tmp/klippy_uds* 2>/dev/null 1>&2; then
    for uds in $(ls /tmp/klippy_uds*)
    do
      status_msg "Removing $uds ..."
      rm -f $uds
      ok_msg "File '$uds' removed!"
    done
  fi

  ### remove all tmp-printer
  if ls /tmp/printer* 2>/dev/null 1>&2; then
    for tmp_printer in $(ls /tmp/printer*)
    do
      status_msg "Removing $tmp_printer ..."
      rm -f $tmp_printer
      ok_msg "File '$tmp_printer' removed!"
    done
  fi

  ### removing klipper and klippy-env folders
  if [ -d $KLIPPER_DIR ]; then
    status_msg "Removing Klipper directory ..."
    rm -rf $KLIPPER_DIR && ok_msg "Directory removed!"
  fi
  if [ -d $KLIPPY_ENV ]; then
    status_msg "Removing klippy-env directory ..."
    rm -rf $KLIPPY_ENV && ok_msg "Directory removed!"
  fi

  CONFIRM_MSG=" Klipper was successfully removed!" && print_msg && clear_msg

  if [ "$REM_MR" == "true" ]; then
    remove_moonraker && unset REM_MR
  fi
}

#############################################################
#############################################################

remove_moonraker(){
  ### remove "legacy" moonraker init.d service
  if [ -f /etc/init.d/moonraker ]; then
    status_msg "Removing Moonraker Service ..."
    sudo systemctl stop moonraker
    sudo update-rc.d -f moonraker remove
    sudo rm -f /etc/init.d/moonraker
    sudo rm -f /etc/default/moonraker
    ok_msg "Moonraker Service removed!"
  fi

  ### remove all moonraker services
  if ls /etc/systemd/system/moonraker*.service 2>/dev/null 1>&2; then
    status_msg "Removing Moonraker Services ..."
    for service in $(ls /etc/systemd/system/moonraker*.service | cut -d"/" -f5)
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
    ok_msg "Moonraker Service removed!"
  fi

  ### remove all logfiles
  if ls /tmp/moonraker*.log 2>/dev/null 1>&2; then
    for logfile in $(ls /tmp/moonraker*.log)
    do
      status_msg "Removing $logfile ..."
      rm -f $logfile
      ok_msg "File '$logfile' removed!"
    done
  fi

  ### remove moonraker nginx config
  if [[ -e $NGINX_CONFD/upstreams.conf || -e $NGINX_CONFD/common_vars.conf ]]; then
    status_msg "Removing Moonraker NGINX configuration ..."
    sudo rm -f $NGINX_CONFD/upstreams.conf $NGINX_CONFD/common_vars.conf && ok_msg "Moonraker NGINX configuration removed!"
  fi

  ### remove legacy api key
  if [ -e ${HOME}/.klippy_api_key ]; then
    status_msg "Removing legacy API Key ..." && rm ${HOME}/.klippy_api_key && ok_msg "Done!"
  fi

  ### remove api key
  if [ -e ${HOME}/.moonraker_api_key ]; then
    status_msg "Removing API Key ..." && rm ${HOME}/.moonraker_api_key && ok_msg "Done!"
  fi

  ### removing moonraker and moonraker-env folder
  if [ -d $MOONRAKER_DIR ]; then
    status_msg "Removing Moonraker directory ..."
    rm -rf $MOONRAKER_DIR && ok_msg "Directory removed!"
  fi
  if [ -d $MOONRAKER_ENV ]; then
    status_msg "Removing moonraker-env directory ..."
    rm -rf $MOONRAKER_ENV && ok_msg "Directory removed!"
  fi

  CONFIRM_MSG=" Moonraker was successfully removed!"
}

#############################################################
#############################################################

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

  CONFIRM_MSG=" OctoPrint successfully removed!"
}

#############################################################
#############################################################

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

remove_klipperscreen(){
  source_kiauh_ini

  ### remove KlipperScreen dir
  if [ -d $KLIPPERSCREEN_DIR ]; then
    status_msg "Removing KlipperScreen directory ..."
    rm -rf $KLIPPERSCREEN_DIR && ok_msg "Directory removed!"
  fi

  ### remove KlipperScreen VENV dir
  if [ -d $KLIPPERSCREEN_ENV_DIR ]; then
    status_msg "Removing KlipperScreen VENV directory ..."
    rm -rf $KLIPPERSCREEN_ENV_DIR && ok_msg "Directory removed!"
  fi

  ### remove KlipperScreen service
  if [ -e /etc/systemd/system/KlipperScreen.service ]; then
    status_msg "Removing KlipperScreen service ..."
    sudo systemctl stop KlipperScreen
    sudo systemctl disable moonraker
    sudo rm -f $SYSTEMDDIR/KlipperScreen.service
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "KlipperScreen Service removed!"
  fi

  ### remove KlipperScreen log
  if [ -e /tmp/KlipperScreen.log ]; then
    status_msg "Removing KlipperScreen log file ..."
    rm -f /tmp/KlipperScreen.log && ok_msg "File removed!"
  fi

  ### remove KlipperScreen log symlink in config dir

  if [ -e $klipper_cfg_loc/KlipperScreen.log ]; then
    status_msg "Removing KlipperScreen log symlink ..."
    rm -f $klipper_cfg_loc/KlipperScreen.log && ok_msg "File removed!"
  fi

  CONFIRM_MSG="KlipperScreen successfully removed!"
}

remove_moonraker-telegram-bot(){
  source_kiauh_ini

  ### remove moonraker-telegram-bot dir
  if [ -d $MOONRAKERTELEGRAMBOT_DIR ]; then
    status_msg "Removing moonraker-telegram-bot directory ..."
    rm -rf $MOONRAKERTELEGRAMBOT_DIR && ok_msg "Directory removed!"
  fi

  ### remove moonraker-telegram-bot VENV dir
  if [ -d $MOONRAKERTELEGRAMBOT_ENV_DIR ]; then
    status_msg "Removing moonraker-telegram-bot VENV directory ..."
    rm -rf $MOONRAKERTELEGRAMBOT_ENV_DIR && ok_msg "Directory removed!"
  fi

  ### remove moonraker-telegram-bot service
  if [ -e /etc/systemd/system/moonraker-telegram-bot.service ]; then
    status_msg "Removing moonraker-telegram-bot service ..."
    sudo systemctl stop moonraker-telegram-bot
    sudo systemctl disable moonraker
    sudo rm -f $SYSTEMDDIR/moonraker-telegram-bot.service
    ###reloading units
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
    ok_msg "moonraker-telegram-bot Service removed!"
  fi

  ### remove moonraker-telegram-bot log
  if [ -e /tmp/telegram.log ]; then
    status_msg "Removing moonraker-telegram-bot log file ..."
    rm -f /tmp/telegram.log && ok_msg "File removed!"
  fi

  ### remove moonraker-telegram-bot log symlink in config dir

  if [ -e $klipper_cfg_loc/telegram.log ]; then
    status_msg "Removing moonraker-telegram-bot log symlink ..."
    rm -f $klipper_cfg_loc/telegram.log && ok_msg "File removed!"
  fi

  CONFIRM_MSG="moonraker-telegram-bot successfully removed!"
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

  ### remove MJPG-Streamer directory
  if [ -d ${HOME}/mjpg-streamer ]; then
    status_msg "Removing MJPG-Streamer directory ..."
    rm -rf ${HOME}/mjpg-streamer
    ok_msg "MJPG-Streamer directory removed!"
  fi

  CONFIRM_MSG="MJPG-Streamer successfully removed!"
}