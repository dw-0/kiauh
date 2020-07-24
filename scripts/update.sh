#TODO
# - update the correct branch
# - version checks before updating

#WIP
update_check(){
  read_local_commit
  read_remote_commit
}

update_klipper(){
  stop_klipper
  bb4u "klipper"
  if [ ! -d $KLIPPER_DIR ]; then
    cd ${HOME} && git clone $KLIPPER_REPO
  else
    read_branch
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
  #check dependencies
  dep=(wget gzip tar curl)
  dep_check
  #execute operation
  GET_DWC2_URL=`curl -s https://api.github.com/repositories/28820678/releases/latest | grep browser_download_url | cut -d'"' -f4`
  if [ ! -d $DWC2_DIR/web ]; then
    mkdir -p $DWC2_DIR/web
  fi
  cd $DWC2_DIR/web
  status_msg "Downloading DWC2 Web UI ..."
  wget -q $GET_DWC2_URL && ok_msg "Download complete!"
  status_msg "Unzipping archive ..."
  unzip -q -o *.zip && for f_ in $(find . | grep '.gz');do gunzip -f ${f_};done && ok_msg "Done!"
  status_msg "Writing version to file ..."
  echo $GET_DWC2_URL | cut -d/ -f8 > $DWC2_DIR/web/version && ok_msg "Done!"
  status_msg "Do a little cleanup ..."
  rm -rf DuetWebControl-SD.zip && ok_msg "Done!"
}

update_mainsail(){
  stop_klipper
  bb4u "mainsail"
  status_msg "Updating Mainsail ..."
  install_mainsail
  start_klipper
}