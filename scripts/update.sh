update_kiauh(){
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    status_msg "Updating KIAUH ..."
    cd ${SRCDIR}/kiauh
    ### force reset kiauh before updating
    git reset --hard
    git pull && ok_msg "Update complete! Please restart KIAUH."
    exit -1
  fi
}

update_all(){
  while true; do
    if [ "${#update_arr[@]}" = "0" ]; then
      CONFIRM_MSG="Everything is already up to date!"
      echo; break
    fi
    echo
    top_border
    echo -e "|  The following installations will be updated:         |"
    if [ "$KLIPPER_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Klipper${default}                                            |"
    fi
    if [ "$DWC2FK_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● DWC2-for-Klipper-Socket${default}                            |"
    fi
    if [ "$DWC2_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Duet Web Control${default}                                   |"
    fi
    if [ "$MOONRAKER_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Moonraker${default}                                          |"
    fi
    if [ "$MAINSAIL_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Mainsail${default}                                           |"
    fi
    if [ "$FLUIDD_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● Fluidd${default}                                             |"
    fi
    if [ "$KLIPPERSCREEN_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● KlipperScreen${default}                                      |"
    fi
    if [ "$PGC_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● PrettyGCode for Klipper${default}                            |"
    fi
    if [ "$MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● MoonrakerTelegramBot${default}                               |"
    fi
    if [ "$SYS_UPDATE_AVAIL" = "true" ]; then
      echo -e "|  ${cyan}● System${default}                                             |"
    fi
    bottom_border
    if [ "${#update_arr[@]}" != "0" ]; then
      read -p "${cyan}###### Do you want to proceed? (Y/n):${default} " yn
      case "$yn" in
        Y|y|Yes|yes|"")
          for update in ${update_arr[@]}
          do
            $update
          done
          break;;
        N|n|No|no)
          break;;
        *)
          print_unkown_cmd
          print_msg && clear_msg;;
      esac
    fi
  done
}

update_log_paths(){
  ### update services to make use of moonrakers new log_path option
  ### https://github.com/Arksine/moonraker/commit/829b3a4ee80579af35dd64a37ccc092a1f67682a
  shopt -s extglob # enable extended globbing
  source_kiauh_ini
  LPATH="${HOME}/klipper_logs"
  [ ! -d "$LPATH" ] && mkdir -p "$LPATH"
  FILE="$SYSTEMDDIR/$1?(-*([0-9])).service"
  for file in $(ls $FILE); do
    [ "$1" == "klipper" ] && LOG="klippy"
    [ "$1" == "moonraker" ] && LOG="moonraker"
    if [ ! "$(grep "\-l" $file)" ]; then
      status_msg "Updating $file ..."
      sudo sed -i -r "/ExecStart=/ s|$| -l $LPATH/$LOG.log|" $file
      ok_msg "$file updated!"
    elif [ "$(grep "\-l \/tmp\/$LOG" $file)" ]; then
      status_msg "Updating $file ..."
      sudo sed -i -r "/ExecStart=/ s|-l \/tmp\/$LOG|-l $LPATH/$LOG|" $file
      ok_msg "$file updated!"
    fi
  done
  sudo systemctl daemon-reload

  # patch log_path entry if not found
  dir1="$klipper_cfg_loc"
  dir2="$klipper_cfg_loc/printer_*"
  for conf in $(find $dir1 $dir2 -name "moonraker.conf" 2> /dev/null); do
    if ! grep -q "log_path" $conf; then
      status_msg "Patching $conf"
      sed -i "/^config_path/a log_path: $LPATH" $conf
      ok_msg "OK!"
    fi
  done

  # create symlink for mainsail and fluidd nginx logs
  symlink_webui_nginx_log "mainsail"
  symlink_webui_nginx_log "fluidd"

  # create symlink for webcamd log
  if [ -f "/var/log/webcamd.log" ] && [ ! -L "$LPATH/webcamd.log" ]; then
    status_msg "Creating symlink for '/var/log/webcamd.log' ..."
    ln -s "/var/log/webcamd.log" "$LPATH"
    ok_msg "OK!"
  fi

  shopt -u extglob # disable extended globbing
}

migrate_custompios(){
  ### migrate vanilla mainsailOS 0.4.0 / fluiddPI v1.13.0
  ### and older to be in sync with newer releases
  WEBCAMD_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/usr/local/bin/webcamd"
  MJPG_SERV_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/etc/systemd/system/webcamd.service"
  KL_SERV_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/klipper/filesystem/root/etc/systemd/system/klipper.service"
  NGINX_CFG1="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mainsail/filesystem/root/etc/nginx/conf.d/upstreams.conf"
  NGINX_CFG2="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mainsail/filesystem/root/etc/nginx/sites-available/mainsail"
  LOG_ROTATE_KLIPPER="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/klipper/filesystem/root/etc/logrotate.d/klipper"
  LOG_ROTATE_MOONRAKER="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/moonraker/filesystem/root/etc/logrotate.d/moonraker"
  LOG_ROTATE_WEBCAMD="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/etc/logrotate.d/webcamd"

  if [ "$1" == "mainsail" ]; then
    OS_VER="MainsailOS"
    MACRO_CFG="mainsail.cfg"
  fi
  if [ "$1" == "fluiddpi" ]; then
    OS_VER="FluiddPi"
    MACRO_CFG="client_macros.cfg"
  fi
  if [ ! -f "/boot/$1.txt" ] || [ ! -f "/etc/init.d/klipper" ]; then
    # abort function if there is no sign of an old CustomPiOS anymore
    ERROR_MSG="No vanilla $OS_VER found. Aborting..." && return 0
  fi
  status_msg "Starting migration of $OS_VER... Please wait..."
  if [ -d "${HOME}/klipper_logs" ]; then
    # delete an existing klipper_logs directory
    # shouldn't be there in the first place if its a true vanilla CustomPiOS
    status_msg "Recreate '~/klipper_logs' directory..."
    rm -rf "${HOME}/klipper_logs" && mkdir "${HOME}/klipper_logs"
    ok_msg "OK!"
  fi
  if [ -f "/boot/$1.txt" ]; then
    # replace old webcamd.service and webcamd
    status_msg "Migrating MJPG-Streamer..."
    sudo systemctl stop webcamd
    sudo rm -f "/etc/systemd/system/webcamd.service"
    sudo rm -f "/root/bin/webcamd"
    sudo wget $WEBCAMD_SRC -O "/usr/local/bin/webcamd"
    sudo wget $MJPG_SERV_SRC -O "/etc/systemd/system/webcamd.service"
    sudo sed -i "s/MainsailOS/$OS_VER/" "/etc/systemd/system/webcamd.service"
    sudo chmod +x "/usr/local/bin/webcamd"
    # move mainsail.txt/fluiddpi.txt from boot to klipper_config and rename it
    sudo mv "/boot/$1.txt" "${HOME}/klipper_config/webcam.txt"
    sudo chown pi:pi "${HOME}/klipper_config/webcam.txt"
    sudo systemctl daemon-reload
    sudo systemctl restart webcamd
    ok_msg "OK!"
  fi
  if [ -f "/etc/init.d/klipper" ] && [ ! -f "/etc/systemd/system/klipper.service" ]; then
    # replace klipper SysVinit service with systemd service
    status_msg "Migrating Klipper Service..."
    sudo systemctl stop klipper
    sudo update-rc.d -f klipper remove
    sudo rm -f "/etc/init.d/klipper"
    sudo rm -f "/etc/default/klipper"
    sudo wget $KL_SERV_SRC -O "/etc/systemd/system/klipper.service"
    sudo systemctl enable klipper.service
    sudo systemctl daemon-reload
    sudo systemctl restart klipper
    ok_msg "OK!"
  fi
  if [ -f "/etc/systemd/system/moonraker.service" ]; then
    # update new log path in existing moonraker service
    status_msg "Updating Moonraker Service..."
    sudo systemctl stop moonraker
    update_log_paths "moonraker"
    sudo systemctl restart moonraker
    ok_msg "OK!"
  fi
  if [ -f "/etc/nginx/conf.d/upstreams.conf" ]; then
    [ "$1" == "mainsail" ] && cfg="mainsail"
    [ "$1" == "fluiddpi" ] && cfg="fluidd"
    # update nginx upstreams.conf and mainsail/fluidd config file
    status_msg "Updating NGINX configurations..."
    sudo systemctl stop nginx
    sudo rm -f "/etc/nginx/conf.d/upstreams.conf"
    sudo rm -f "/etc/nginx/sites-available/$cfg"
    sudo wget $NGINX_CFG1 -O "/etc/nginx/conf.d/upstreams.conf"
    sudo wget $NGINX_CFG2 -O "/etc/nginx/sites-available/$cfg"
    sudo sed -i "s/mainsail/$cfg/g" "/etc/nginx/sites-available/$cfg"
    sudo systemctl restart nginx
    ok_msg "OK!"
  fi
  if [ -f "${HOME}/klipper_config/$MACRO_CFG" ]; then
    # update macro files
    status_msg "Updating $MACRO_CFG ..."
    MACRO_CFG_PATH="${HOME}/klipper_config/$MACRO_CFG"
    sed -i "/SAVE_GCODE_STATE NAME=PAUSE_state/d" $MACRO_CFG_PATH
    sed -i "/RESTORE_GCODE_STATE NAME=PAUSE_state/d" $MACRO_CFG_PATH
    ok_msg "OK!"
  fi
  if [ -d "/etc/logrotate.d" ]; then
    # download logrotate configs
    status_msg "Setting up logrotations..."
    sudo wget $LOG_ROTATE_KLIPPER -O "/etc/logrotate.d/klipper"
    sudo wget $LOG_ROTATE_MOONRAKER -O "/etc/logrotate.d/moonraker"
    sudo wget $LOG_ROTATE_WEBCAMD -O "/etc/logrotate.d/webcamd"
    ok_msg "OK!"
  fi
  ok_msg "Migration done!"
}

update_klipper(){
  do_action_service "stop" "klipper"
  if [ ! -d $KLIPPER_DIR ]; then
    cd ${HOME} && git clone $KLIPPER_REPO
  else
    bb4u "klipper"
    read_branch
    save_klipper_state
    status_msg "Updating $GET_BRANCH"
    cd $KLIPPER_DIR
    if [ "$DETACHED_HEAD" == "true" ]; then
      git checkout $GET_BRANCH
      unset DETACHED_HEAD
    fi
    ### pull latest files from github
    git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages
    ### install possible new python dependencies
    KLIPPER_REQ_TXT="$KLIPPER_DIR/scripts/klippy-requirements.txt"
    $KLIPPY_ENV/bin/pip install -r $KLIPPER_REQ_TXT
  fi
  update_log_paths "klipper"
  ok_msg "Update complete!"
  do_action_service "restart" "klipper"
}

update_dwc2fk(){
  do_action_service "stop" "dwc"
  bb4u "dwc2"
  if [ ! -d $DWC2FK_DIR ]; then
    cd ${HOME} && git clone $DWC2FK_REPO
  else
    cd $DWC2FK_DIR && git pull
  fi
  do_action_service "start" "dwc"
}

update_dwc2(){
  bb4u "dwc2"
  download_dwc_webui
}

update_mainsail(){
  bb4u "mainsail"
  status_msg "Updating Mainsail ..."
  mainsail_setup
  match_nginx_configs
  symlink_webui_nginx_log "mainsail"
}

update_fluidd(){
  bb4u "fluidd"
  status_msg "Updating Fluidd ..."
  fluidd_setup
  match_nginx_configs
  symlink_webui_nginx_log "fluidd"
}

update_moonraker(){
  do_action_service "stop" "moonraker"
  bb4u "moonraker"
  status_msg "Updating Moonraker ..."
  ### pull latest files from github
  cd $MOONRAKER_DIR && git pull
  ### read PKGLIST and install possible new dependencies
  install_moonraker_packages
  ### install possible new python dependencies
  MR_REQ_TXT="$MOONRAKER_DIR/scripts/moonraker-requirements.txt"
  $MOONRAKER_ENV/bin/pip install -r $MR_REQ_TXT
  update_log_paths "moonraker"
  ok_msg "Update complete!"
  do_action_service "restart" "moonraker"
}

update_klipperscreen(){
  stop_klipperscreen
  cd $KLIPPERSCREEN_DIR
  KLIPPERSCREEN_OLDREQ_MD5SUM=$(md5sum $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt | cut -d " " -f1)
  git pull origin master -q && ok_msg "Fetch successfull!"
  git checkout -f master && ok_msg "Checkout successfull"
  #KLIPPERSCREEN_NEWREQ_MD5SUM=$(md5sum $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt)
  if [[ $(md5sum $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt | cut -d " " -f1) != $KLIPPERSCREEN_OLDREQ_MD5SUM ]]; then
    status_msg "New dependecies detected..."
    PYTHONDIR="${HOME}/.KlipperScreen-env"
    $PYTHONDIR/bin/pip install -r $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt
    ok_msg "Dependencies have been installed!"
  fi
  ok_msg "Update complete!"
  start_klipperscreen
}

update_pgc_for_klipper(){
  PGC_DIR="${HOME}/pgcode"
  status_msg "Updating PrettyGCode for Klipper ..."
  cd $PGC_DIR && git pull
  ok_msg "Update complete!"
}

update_MoonrakerTelegramBot(){
  source_kiauh_ini
  export klipper_cfg_loc
  stop_MoonrakerTelegramBot
  cd $MOONRAKER_TELEGRAM_BOT_DIR
  git pull
  ./scripts/install.sh
  ok_msg "Update complete!"
  start_MoonrakerTelegramBot
}

update_system(){
  status_msg "Updating System ..."
  sudo apt-get update --allow-releaseinfo-change && sudo apt-get upgrade -y
  ok_msg "Update complete! Check the log above!"
  ok_msg "KIAUH won't do any dist-upgrades!\n"
}