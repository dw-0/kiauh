update_kiauh(){
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    status_msg "Updating KIAUH ..."
    cd ${HOME}/kiauh
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
  stop_klipper
  if [ ! -d $KLIPPER_DIR ]; then
    cd ${HOME} && git clone $KLIPPER_REPO
  else
    bb4u "klipper"
    read_branch
    save_klipper_state
    status_msg "Updating $GET_BRANCH"
    #fetching origin/master -> error
    #rewriting origin/master to origin
    if [ "$GET_BRANCH" = "origin/master" ]; then
      FETCH_BRANCH="origin"
    else
      FETCH_BRANCH=$(echo "$GET_BRANCH" | cut -d "/" -f1)
    fi
    status_msg "Fetching from $FETCH_BRANCH"
    cd $KLIPPER_DIR
    git fetch $FETCH_BRANCH -q && ok_msg "Fetch successfull!"
    status_msg "Checking out $GET_BRANCH"
    git checkout $GET_BRANCH -q && ok_msg "Checkout successfull!"
    #check for possible new dependencies and install them
    status_msg "Checking for possible new dependencies ..."
    PKGLIST=$(grep "PKGLIST=" ~/klipper/scripts/install-octopi.sh | cut -d'"' -f2- | cut -d'"' -f1 | cut -d"}" -f2)
    PYTHONDIR="${HOME}/klippy-env"
    sudo apt-get update && sudo apt-get install --yes $PKGLIST
    $PYTHONDIR/bin/pip install -r ~/klipper/scripts/klippy-requirements.txt
    ok_msg "Dependencies already met or have been installed!"
    ok_msg "Update complete!"
  fi
  start_klipper
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
  while true; do
    echo
    top_border
    echo -e "| You can now choose how you want to update Moonraker.  |"
    blank_line
    echo -e "| Changes made to the Moonraker code and/or its depen-  |"
    echo -e "| dencies might require a rebuild of the python virtual |"
    echo -e "| environment or downloading of additional packages.    |"
    blank_line
    echo -e "| ${red}Check the docs in the Moonraker repository to see if${default}  |"
    echo -e "| ${red}rebuilding is necessary (user_changes.md)!${default}            |"
    blank_line
    echo -e "| 1) Update Moonraker (default)                         |"
    echo -e "| 2) Update Moonraker + rebuild virtualenv/dependencies |"
    quit_footer
    read -p "${cyan}###### Please choose:${default} " action
    case "$action" in
      1|"")
        echo -e "###### > Update Moonraker"
        update_mr="true" && rebuild_env="false"
        break;;
      2)
        echo -e "###### > Update Moonraker + rebuild virtualenv/dependencies"
        update_mr="true" && rebuild_env="true"
        break;;
      Q|q)
        clear; update_menu; break;;
      *)
        print_unkown_cmd
        print_msg && clear_msg;;
    esac
  done
  stop_moonraker; echo
  if [[ $update_mr = "true" ]] && [[ $rebuild_env = "false" ]]; then
    unset update_mr && unset rebuild_env
    cd $MOONRAKER_DIR && git pull
  fi
  if [[ $update_mr = "true" ]] && [[ $rebuild_env = "true" ]]; then
    unset update_mr && unset rebuild_env
    cd $MOONRAKER_DIR && git pull && ./scripts/install-moonraker.sh -r
  fi
  #read printer.cfg location and patch /etc/default/klipper if entries don't match
  locate_printer_cfg && patch_klipper_sysfile
  ok_msg "Update complete!"
  restart_moonraker
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
