update_kiauh(){
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    status_msg "Updating KIAUH ..."
    cd ${HOME}/kiauh
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
    KLIPPER_OLDREQ_MD5SUM="$(md5sum $KLIPPER_DIR/scripts/klippy-requirements.txt | cut -d " " -f1)"

    if [ "$DETACHED_HEAD" == "true" ]; then
      git checkout $GET_BRANCH
      unset DETACHED_HEAD
    fi

    ### pull latest files from github
    git pull && ok_msg "Update successfull!"

    ### check for possible new dependencies and install them
    if [[ $(md5sum $KLIPPER_DIR/scripts/klippy-requirements.txt | cut -d " " -f1) != $KLIPPER_OLDREQ_MD5SUM ]]; then
      PYTHONDIR="${HOME}/klippy-env"
      status_msg "New dependecies detected..."

      ### always rebuild the pythondir from scratch if new dependencies were detected
      rm -rf ${PYTHONDIR}
      virtualenv -p python2 ${PYTHONDIR}
      $PYTHONDIR/bin/pip install -r $KLIPPER_DIR/scripts/klippy-requirements.txt
      ok_msg "Dependencies have been installed!"
    fi

    ok_msg "Update complete!"
  fi
  klipper_service "restart"
}

update_dwc2fk(){
  stop_dwc
  bb4u "dwc2"
  if [ ! -d $DWC2FK_DIR ]; then
    cd ${HOME} && git clone $DWC2FK_REPO
  else
    cd $DWC2FK_DIR && git pull
  fi
  start_dwc
}

update_dwc2(){
  bb4u "dwc2"
  download_dwc2_webui
}

update_mainsail(){
  bb4u "mainsail"
  status_msg "Updating Mainsail ..."
  mainsail_setup
}

update_fluidd(){
  bb4u "fluidd"
  status_msg "Updating Fluidd ..."
  fluidd_setup
}

update_moonraker(){
  bb4u "moonraker"
  status_msg "Updating Moonraker ..."
  moonraker_service "stop"; echo
  cd $MOONRAKER_DIR
  MOONRAKER_OLDREQ_MD5SUM=$(md5sum $MOONRAKER_DIR/scripts/moonraker-requirements.txt | cut -d " " -f1)

  ### pull latest files from github
  git pull && ok_msg "Update successfull!"

  ### check for possible new dependencies and install them
  if [[ $(md5sum $MOONRAKER_DIR/scripts/moonraker-requirements.txt | cut -d " " -f1) != $MOONRAKER_OLDREQ_MD5SUM ]]; then
    PYTHONDIR="${HOME}/moonraker-env"
    status_msg "New dependecies detected..."
    ### always rebuild the pythondir from scratch if new dependencies were detected
    rm -rf ${PYTHONDIR}
    virtualenv -p /usr/bin/python3 ${PYTHONDIR}
    ln -s /usr/lib/python3/dist-packages/gpiod* ${PYTHONDIR}/lib/python*/site-packages
    ${PYTHONDIR}/bin/pip install -r $MOONRAKER_DIR/scripts/moonraker-requirements.txt
    ok_msg "Dependencies have been installed!"
  fi

  ok_msg "Update complete!"
  moonraker_service "restart"
}

update_klipperscreen(){
  stop_klipperscreen
  cd $KLIPPERSCREEN_DIR
  KLIPPERSCREEN_OLDREQ_MD5SUM=$(md5sum $KLIPPERSCREEN_DIR/scripts/KlipperScreen-requirements.txt | cut -d " " -f1)
  git pull origin master -q && ok_msg "Fetch successfull!"
  git checkout -f origin/master && ok_msg "Checkout successfull"
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
