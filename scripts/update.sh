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
    status_msg "Checking out $FETCH_BRANCH"
    git checkout $FETCH_BRANCH -q && ok_msg "Checkout successfull!"
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
  stop_moonraker
  bb4u "moonraker"
  status_msg "Updating Moonraker ..."
  if [ ! -d $MOONRAKER_DIR ]; then
    cd ${HOME} && git clone $MOONRAKER_REPO
  else
    cd $MOONRAKER_DIR && git pull
    #check for possible new dependencies and install them
    status_msg "Checking for possible new dependencies ..."
    PKGLIST="$(grep "PKGLIST=" ~/moonraker/scripts/install-moonraker.sh | cut -d'"' -f2- | cut -d'"' -f1)"
    PYTHONDIR="${HOME}/moonraker-env"
    sudo apt-get update && sudo apt-get install --yes $PKGLIST
    $PYTHONDIR/bin/pip install -r ~/moonraker/scripts/moonraker-requirements.txt
    ok_msg "Dependencies already met or have been installed!"
  fi
  #read default printer.cfg location for the patch function
  locate_printer_cfg
  #patch /etc/default/klipper if entries don't match
  patch_klipper_sysfile
  ok_msg "Update complete!"
  start_moonraker
}
