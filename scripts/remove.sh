remove_klipper(){
  ### ask the user if he wants to uninstall moonraker too.
  ###? currently usefull if the user wants to switch from single-instance to multi-instance
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "moonraker*.")" ]; then
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
  if [[ -e /etc/init.d/klipper || -e /etc/default/klipper ]]; then
    status_msg "Removing Klipper Service ..."
    sudo systemctl stop klipper
    sudo systemctl disable klipper
    sudo rm -rf /etc/init.d/klipper /etc/default/klipper
    sudo update-rc.d -f klipper remove
    sudo systemctl daemon-reload
    ok_msg "Klipper Service removed!"
  fi

  ###remove single instance
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    status_msg "Removing Klipper Service ..."
    sudo systemctl stop klipper
    sudo systemctl disable klipper
    sudo rm -f $SYSTEMDDIR/klipper.service
    ok_msg "Klipper Service removed!"
  fi
  if [ -f /tmp/klippy.log ]; then
    status_msg "Removing /tmp/klippy.log ..." && rm -f /tmp/klippy.log && ok_msg "Done!"
  fi
  if [ -e /tmp/klippy_uds ]; then
    status_msg "Removing /tmp/klippy_uds ..." && rm -f /tmp/klippy_uds && ok_msg "Done!"
  fi
  if [ -h /tmp/printer ]; then
    status_msg "Removing /tmp/printer ..." && rm -f /tmp/printer && ok_msg "Done!"
  fi

  ###remove multi instance services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service")" ]; then
    status_msg "Removing Klipper Services ..."
    for service in $(find $SYSTEMDDIR -maxdepth 1 -name "klipper-*.service" | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "Done!"
    done
  fi

  ###remove multi instance logfiles
  if [ "$(find /tmp -maxdepth 1 -name "klippy-*.log")" ]; then
    for logfile in $(find /tmp -maxdepth 1 -name "klippy-*.log")
    do
      status_msg "Removing $logfile ..." && rm -f $logfile && ok_msg "Done!"
    done
  fi

  ###remove multi instance UDS
  if [ "$(find /tmp -maxdepth 1 -name "klippy_uds-*")" ]; then
    for uds in $(find /tmp -maxdepth 1 -name "klippy_uds-*")
    do
      status_msg "Removing $uds ..." && rm -f $uds && ok_msg "Done!"
    done
  fi

  ###remove multi instance tmp-printer
  if [ "$(find /tmp -maxdepth 1 -name "printer-*")" ]; then
    for tmp_printer in $(find /tmp -maxdepth 1 -name "printer-*")
    do
      status_msg "Removing $tmp_printer ..." && rm -f $tmp_printer && ok_msg "Done!"
    done
  fi

  ###reloading units
  sudo systemctl daemon-reload

  ###removing klipper and klippy-env folders
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
    remove_moonraker
  fi
}

#############################################################
#############################################################

remove_dwc2(){
  ### remove "legacy" init.d service
  if [[ -e /etc/init.d/dwc || -e /etc/default/dwc ]]; then
    status_msg "Removing DWC2-for-Klipper-Socket Service ..."
    sudo systemctl stop dwc
    sudo systemctl disable dwc
    sudo rm -rf /etc/init.d/dwc /etc/default/dwc
    sudo update-rc.d -f dwc remove
    sudo systemctl daemon-reload
    ok_msg "DWC2-for-Klipper-Socket Service removed!"
  fi

  ### remove single instance
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "dwc.service")" ]; then
    status_msg "Removing DWC2-for-Klipper-Socket Service ..."
    sudo systemctl stop dwc
    sudo systemctl disable dwc
    sudo rm -f $SYSTEMDDIR/dwc.service
    ok_msg "DWC2-for-Klipper-Socket Service removed!"
  fi
  if [ -f /tmp/dwc.log ]; then
    status_msg "Removing /tmp/dwc.log ..." && rm -f /tmp/dwc.log && ok_msg "Done!"
  fi

  ### remove multi instance services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "dwc-[[:digit:]].service")" ]; then
    status_msg "Removing DWC2-for-Klipper-Socket Services ..."
    for service in $(find $SYSTEMDDIR -maxdepth 1 -name "dwc-*.service" | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "Done!"
    done
  fi

  ### remove multi instance logfiles
  if [ "$(find /tmp -maxdepth 1 -name "dwc-*.log")" ]; then
    for logfile in $(find /tmp -maxdepth 1 -name "dwc-*.log")
    do
      status_msg "Removing $logfile ..." && rm -f $logfile && ok_msg "Done!"
    done
  fi

  ### reloading units
  sudo systemctl daemon-reload

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

remove_moonraker(){
  ### remove "legacy" moonraker init.d service
  if [[ -e /etc/init.d/moonraker || -e /etc/default/moonraker ]]; then
    status_msg "Removing Moonraker Service ..."
    sudo systemctl stop moonraker
    sudo systemctl disable moonraker
    sudo rm -rf /etc/init.d/moonraker /etc/default/moonraker
    sudo update-rc.d -f moonraker remove
    sudo systemctl daemon-reload
    ok_msg "Moonraker Service removed!"
  fi

  ###remove single instance
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "moonraker.service")" ]; then
    status_msg "Removing Moonraker Service ..."
    sudo systemctl stop moonraker
    sudo systemctl disable moonraker
    sudo rm -f $SYSTEMDDIR/moonraker.service
    ok_msg "Moonraker Service removed!"
  fi
  if [ -f /tmp/moonraker.log ]; then
    status_msg "Removing /tmp/moonraker.log ..." && rm -f /tmp/moonraker.log && ok_msg "Done!"
  fi

  ###remove multi instance services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -E "moonraker-[[:digit:]].service")" ]; then
    status_msg "Removing Moonraker Services ..."
    for service in $(find $SYSTEMDDIR -maxdepth 1 -name "moonraker-*.service" | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "Done!"
    done
  fi
  ###remove multi instance logfiles
  if [ "$(find /tmp -maxdepth 1 -name "moonraker-*.log")" ]; then
    for logfile in $(find /tmp -maxdepth 1 -name "moonraker-*.log")
    do
      status_msg "Removing $logfile ..." && rm -f $logfile && ok_msg "Done!"
    done
  fi

  ###reloading units
  sudo systemctl daemon-reload

  #remove moonraker nginx config
  if [[ -e $NGINX_CONFD/upstreams.conf || -e $NGINX_CONFD/common_vars.conf ]]; then
    status_msg "Removing Moonraker NGINX configuration ..."
    sudo rm -f $NGINX_CONFD/upstreams.conf $NGINX_CONFD/common_vars.conf && ok_msg "Moonraker NGINX configuration removed!"
  fi

  #remove legacy api key
  if [ -e ${HOME}/.klippy_api_key ]; then
    status_msg "Removing legacy API Key ..." && rm ${HOME}/.klippy_api_key && ok_msg "Done!"
  fi
  #remove api key
  if [ -e ${HOME}/.moonraker_api_key ]; then
    status_msg "Removing API Key ..." && rm ${HOME}/.moonraker_api_key && ok_msg "Done!"
  fi

  ###removing moonraker and moonraker-env folder
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
  ###remove single instance
  if [ "$(systemctl list-unit-files | grep -F "octoprint.service")" ]; then
    status_msg "Removing OctoPrint Service ..."
    sudo systemctl stop octoprint
    sudo systemctl disable octoprint
    sudo rm -f $SYSTEMDDIR/octoprint.service
    ok_msg "OctoPrint Service removed!"
  fi

  ###remove multi instance services
  if [ "$(systemctl list-unit-files | grep -E "octoprint-[[:digit:]].service")" ]; then
    status_msg "Removing OctoPrint Services ..."
    for service in $(find $SYSTEMDDIR -maxdepth 1 -name "octoprint-*.service" | cut -d"/" -f5)
    do
      status_msg "Removing $service ..."
      sudo systemctl stop $service
      sudo systemctl disable $service
      sudo rm -f $SYSTEMDDIR/$service
      ok_msg "OctoPrint Service removed!"
    done
  fi

  ###reloading units
  sudo systemctl daemon-reload

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
  if [ "$(find ${HOME} -maxdepth 1 -name ".octoprint*")" ]; then
    for folder in $(find ${HOME} -maxdepth 1 -name ".octoprint*")
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

  ### remove KlipperScreen systemd file
  if [ -e /etc/systemd/system/KlipperScreen.service ]; then
    status_msg "Removing KlipperScreen Service ..."
    sudo rm /etc/systemd/system/KlipperScreen.service && ok_msg "File removed!"
  fi

  CONFIRM_MSG="KlipperScreen successfully removed!"
}
