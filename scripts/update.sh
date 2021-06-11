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
  ### migrate vanilla mainsailOS 0.4.0 and fluiddPI v1.13.0
  ### and older to be in sync with their newer releases
  if [ -f "/boot/$1.txt" ]; then
    status_msg "Starting migration... Please wait..."
    ### migrate webcam related stuff
    WEBCAMD_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/master/src/modules/mjpgstreamer/filesystem/root/usr/local/bin/webcamd"
    MJPG_SERV_SRC="${SRCDIR}/kiauh/resources/webcamd.service"
    MJPG_SERV_TARGET="$SYSTEMDDIR/webcamd.service"
    KL_SERV_SRC="https://raw.githubusercontent.com/raymondh2/MainsailOS/dev-klipper-serviced/src/modules/klipper/filesystem/root/etc/systemd/system/klipper.service"
    # stop webcam service
    sudo systemctl stop webcamd.service
    # replace old webcamd.service
    sudo rm -f "$SYSTEMDDIR/webcamd.service"
    # replace old webcamd
    sudo rm -f "/root/bin/webcamd"
    sudo cp $MJPG_SERV_SRC $MJPG_SERV_TARGET
    sudo sed -i "s|%USER%|pi|" $MJPG_SERV_TARGET
    sudo wget $WEBCAMD_SRC -O "/usr/local/bin/webcamd"
    sudo chmod +x /usr/local/bin/webcamd
    # copy mainsail.txt or fluidd.txt to klipper_config and rename it
    sudo mv "/boot/$1.txt" "${HOME}/klipper_config/webcam.txt"
    sudo chown pi:pi "${HOME}/klipper_config/webcam.txt"
    ### migrate klipper related stuff
    sudo service klipper stop
    # stop and remove init.d klipper service
    sudo update-rc.d -f klipper remove
    sudo rm -f /etc/init.d/klipper
    sudo rm -f /etc/default/klipper
    # create new systemd service
    sudo wget $KL_SERV_SRC -O "/etc/systemd/system/klipper.service"
    sudo systemctl enable klipper.service
    sudo systemctl daemon-reload
    ok_msg "Migration complete!"
  fi
}

update_klipper(){
  klipper_service "stop"
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

    ### get current klippy-requirements.txt md5sum
    KLIPPER_OLDREQ_MD5SUM="$(md5sum $KLIPPER_DIR/scripts/klippy-requirements.txt | cut -d " " -f1)"
    ### pull latest files from github
    git pull
    ### read PKGLIST and install possible new dependencies
    install_klipper_packages
    ### get possible new klippy-requirements.txt md5sum
    KLIPPER_NEWREQ_MD5SUM="$(md5sum $KLIPPER_DIR/scripts/klippy-requirements.txt | cut -d " " -f1)"

    ### check for possible new dependencies and install them
    if [[ $KLIPPER_NEWREQ_MD5SUM != $KLIPPER_OLDREQ_MD5SUM ]]; then
      PYTHONDIR="${HOME}/klippy-env"
      status_msg "New dependecies detected..."

      ### always rebuild the pythondir from scratch if new dependencies were detected
      rm -rf ${PYTHONDIR}
      virtualenv -p python2 ${PYTHONDIR}
      $PYTHONDIR/bin/pip install -r $KLIPPER_DIR/scripts/klippy-requirements.txt
      ok_msg "Dependencies have been installed!"
    fi
  fi
  migrate_custompios "mainsail"
  migrate_custompios "fluiddpi"
  update_log_paths "klipper"
  ok_msg "Update complete!"
  klipper_service "restart"
}

update_dwc2fk(){
  dwc_service "stop"
  bb4u "dwc2"
  if [ ! -d $DWC2FK_DIR ]; then
    cd ${HOME} && git clone $DWC2FK_REPO
  else
    cd $DWC2FK_DIR && git pull
  fi
  dwc_service "start"
}

update_dwc2(){
  bb4u "dwc2"
  download_dwc_webui
}

update_mainsail(){
  bb4u "mainsail"
  status_msg "Updating Mainsail ..."
  mainsail_setup
  symlink_webui_nginx_log "mainsail"
}

update_fluidd(){
  bb4u "fluidd"
  status_msg "Updating Fluidd ..."
  fluidd_setup
  symlink_webui_nginx_log "fluidd"
}

update_moonraker(){
  moonraker_service "stop"
  bb4u "moonraker"
  status_msg "Updating Moonraker ..."
  cd $MOONRAKER_DIR

  ### get current moonraker-requirements.txt md5sum
  MOONRAKER_OLDREQ_MD5SUM=$(md5sum $MOONRAKER_DIR/scripts/moonraker-requirements.txt | cut -d " " -f1)
  ### pull latest files from github
  git pull
  ### read PKGLIST and install possible new dependencies
  install_moonraker_packages
  ### get possible new moonraker-requirements.txt md5sum
  MOONRAKER_NEWREQ_MD5SUM=$(md5sum $MOONRAKER_DIR/scripts/moonraker-requirements.txt | cut -d " " -f1)

  ### check for possible new dependencies and install them
  if [[ $MOONRAKER_NEWREQ_MD5SUM != $MOONRAKER_OLDREQ_MD5SUM ]]; then
    PYTHONDIR="${HOME}/moonraker-env"
    status_msg "New dependecies detected..."
    ### always rebuild the pythondir from scratch if new dependencies were detected
    rm -rf ${PYTHONDIR}
    virtualenv -p /usr/bin/python3 ${PYTHONDIR}
    ln -s /usr/lib/python3/dist-packages/gpiod* ${PYTHONDIR}/lib/python*/site-packages
    ${PYTHONDIR}/bin/pip install -r $MOONRAKER_DIR/scripts/moonraker-requirements.txt
    ok_msg "Dependencies have been installed!"
  fi
  update_log_paths "moonraker"
  ok_msg "Update complete!"
  moonraker_service "restart"
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

update_system(){
  status_msg "Updating System ..."
  sudo apt-get update && sudo apt-get upgrade -y
  ok_msg "Update complete! Check the log above!"
  ok_msg "KIAUH won't do any dist-upgrades!\n"
}