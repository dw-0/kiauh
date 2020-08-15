update_kiauh(){
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    status_msg "Updating KIAUH ..."
    cd ${HOME}/kiauh
    git pull && ok_msg "Update complete! Please restart KIAUH."
    exit -1
  fi
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
    if [ "$GET_BRANCH" == "origin/master" ]; then
      FETCH_BRANCH="origin"
    else
      FETCH_BRANCH=$(echo "$GET_BRANCH" | cut -d "/" -f1)
    fi
    status_msg "Fetching from $FETCH_BRANCH"
    git fetch $FETCH_BRANCH -q && ok_msg "Fetch successfull!"
    status_msg "Checking out $GET_BRANCH"
    git checkout $GET_BRANCH -q && ok_msg "Checkout successfull!" && echo; ok_msg "Update complete!"
  fi
  start_klipper; echo
}

update_dwc2fk(){
  stop_klipper
  bb4u "dwc2"
  if [ ! -d $DWC2FK_DIR ]; then
    cd ${HOME} && git clone $DWC2FK_REPO
  else
    cd $DWC2FK_DIR && git pull
    #create a web_dwc2.py symlink if not already existing
    if [ -d $KLIPPER_DIR/klippy/extras ] && [ ! -e $WEB_DWC2 ]; then
      status_msg "Creating web_dwc2.py Symlink ..."
      ln -s $DWC2FK_DIR/web_dwc2.py $WEB_DWC2 && ok_msg "Symlink created!"
    fi
  fi
  start_klipper
}

update_dwc2(){
  bb4u "dwc2"
  install_dwc2
}

update_mainsail(){
  stop_klipper
  bb4u "mainsail"
  status_msg "Updating Mainsail ..."
  install_mainsail
  start_klipper
}

update_moonraker(){
  stop_klipper && sleep 2 && stop_moonraker
  bb4u "moonraker"
  status_msg "Updating Moonraker ..."
  if [ ! -d $MOONRAKER_DIR ]; then
    cd ${HOME} && git clone $MOONRAKER_REPO
  else
    cd $MOONRAKER_DIR && git pull
  fi
  ok_msg "Update complete!"
  start_moonraker && sleep 2 && start_klipper
}
