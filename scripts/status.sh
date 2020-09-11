kiauh_status(){
  if [ -d "${HOME}/kiauh/.git" ]; then
    cd ${HOME}/kiauh
    git fetch --all -q
    if git branch -a | grep "* master" -q; then
      CURR_KIAUH_BRANCH="master" #needed to display branch in UI
      if [[ "$(git rev-parse --short=8 origin/master)" != "$(git rev-parse --short=8 HEAD)" ]]; then
        KIAUH_UPDATE_AVAIL="true"
      fi
    elif git branch -a | grep "* dev-2.0" -q; then
      CURR_KIAUH_BRANCH="dev-2.0" #needed to display branch in UI
      if [[ "$(git rev-parse --short=8 origin/dev-2.0)" != "$(git rev-parse --short=8 HEAD)" ]]; then
        KIAUH_UPDATE_AVAIL="true"
      fi
    fi
  fi
}

klipper_status(){
  kcount=0
  klipper_data=(
    $KLIPPER_DIR
    $KLIPPY_ENV_DIR
    $KLIPPER_SERVICE1
    $KLIPPER_SERVICE2
  )
  #count+1 for each found data-item from array
  for kd in "${klipper_data[@]}"
  do
    if [ -e $kd ]; then
      kcount=$(expr $kcount + 1)
    fi
  done
  if [ "$kcount" == "${#klipper_data[*]}" ]; then
    KLIPPER_STATUS="${green}Installed!${default}         "
  elif [ "$kcount" == 0 ]; then
    KLIPPER_STATUS="${red}Not installed!${default}     "
  else
    KLIPPER_STATUS="${yellow}Incomplete!${default}        "
  fi
}

dwc2_status(){
  dcount=0
  dwc2_data=(
    $DWC2FK_DIR
    $WEB_DWC2
    $DWC2_DIR
  )
  #count+1 for each found data-item from array
  for dd in "${dwc2_data[@]}"
  do
    if [ -e $dd ]; then
      dcount=$(expr $dcount + 1)
    fi
  done
  if [ "$dcount" == "${#dwc2_data[*]}" ]; then
    DWC2_STATUS="${green}Installed!${default}         "
  elif [ "$dcount" == 0 ]; then
    DWC2_STATUS="${red}Not installed!${default}     "
  else
    DWC2_STATUS="${yellow}Incomplete!${default}        "
  fi
}

mainsail_status(){
  mcount=0
  mainsail_data=(
    $MOONRAKER_SERVICE1
    $MOONRAKER_SERVICE2
    $MAINSAIL_DIR
    $MOONRAKER_ENV_DIR
    /etc/nginx/sites-available/mainsail
    /etc/nginx/sites-enabled/mainsail
  )
  #count+1 for each found data-item from array
  for md in "${mainsail_data[@]}"
  do
    if [ -e $md ]; then
      mcount=$(expr $mcount + 1)
    fi
  done
  if [ "$mcount" == "${#mainsail_data[*]}" ]; then
    MAINSAIL_STATUS="${green}Installed!${default}         "
  elif [ "$mcount" == 0 ]; then
    MAINSAIL_STATUS="${red}Not installed!${default}     "
  else
    MAINSAIL_STATUS="${yellow}Incomplete!${default}        "
  fi
}

octoprint_status(){
  ocount=0
  octoprint_data=(
    $OCTOPRINT_DIR
    $OCTOPRINT_CFG_DIR
    $OCTOPRINT_SERVICE1
    $OCTOPRINT_SERVICE2
  )
  #count+1 for each found data-item from array
  for op in "${octoprint_data[@]}"
  do
    if [ -e $op ]; then
      ocount=$(expr $ocount + 1)
    fi
  done
  if [ "$ocount" == "${#octoprint_data[*]}" ]; then
    OCTOPRINT_STATUS="${green}Installed!${default}         "
  elif [ "$ocount" == 0 ]; then
    OCTOPRINT_STATUS="${red}Not installed!${default}     "
  else
    OCTOPRINT_STATUS="${yellow}Incomplete!${default}        "
  fi
}

#reading the log for the last branch that got checked out assuming that this is also the currently active branch.
read_branch(){
  if [ -d $KLIPPER_DIR/.git ]; then
    GET_BRANCH=$(cat ~/klipper/.git/logs/HEAD | grep "checkout" | tail -1 | sed "s/^.*to //")
    #if the log file is empty, we can assume that klipper just got cloned and therefore is still on origin/master
    if [[ -z "$GET_BRANCH" ]]; then
      GET_BRANCH="origin/master"
    fi
  else
    GET_BRANCH=""
  fi
}

#prints the current klipper branch in the main menu
print_branch(){
  read_branch
  if [ "$GET_BRANCH" == "origin/master" ]; then
    PRINT_BRANCH="$GET_BRANCH      "
  elif [ "$GET_BRANCH" == "origin" ]; then
    PRINT_BRANCH="origin/master      "
  elif [ "$GET_BRANCH" == "master" ]; then
    PRINT_BRANCH="origin/master      "
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-shaping" ]; then
    PRINT_BRANCH="scurve-shaping     "
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-smoothing" ]; then
    PRINT_BRANCH="scurve-smoothing   "
  elif [ "$GET_BRANCH" == "Arksine/dev-moonraker-testing" ]; then
    PRINT_BRANCH="moonraker          "
  else
    PRINT_BRANCH="${red}----${default}               "
  fi
}

read_local_klipper_commit(){
  if [ -d $KLIPPER_DIR ] && [ -d $KLIPPER_DIR/.git ]; then
    cd $KLIPPER_DIR
    LOCAL_COMMIT=$(git rev-parse --short=8 HEAD)
  else
    LOCAL_COMMIT="${red}--------${default}"
  fi
}

read_remote_klipper_commit(){
  read_branch
  if [ ! -z "$GET_BRANCH" ];then
    if [ "$GET_BRANCH" = "origin/master" ] || [ "$GET_BRANCH" = "master" ]; then
      git fetch origin -q
      REMOTE_COMMIT=$(git rev-parse --short=8 origin)
    else
      git fetch $(echo "$GET_BRANCH" | cut -d"/" -f1) -q
      REMOTE_COMMIT=$(git rev-parse --short=8 $GET_BRANCH)
    fi
  else
    REMOTE_COMMIT="${red}--------${default}"
  fi
}

compare_klipper_versions(){
  read_local_klipper_commit
  read_remote_klipper_commit
  #echo "Local: $LOCAL_COMMIT"
  #echo "Remote: $REMOTE_COMMIT"
  if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    LOCAL_COMMIT="${yellow}$LOCAL_COMMIT${default}"
    REMOTE_COMMIT="${green}$REMOTE_COMMIT${default}"
  else
    LOCAL_COMMIT="${green}$LOCAL_COMMIT${default}"
    REMOTE_COMMIT="${green}$REMOTE_COMMIT${default}"
  fi
}

read_dwc2fk_versions(){
  if [ -d $DWC2FK_DIR ] && [ -d $DWC2FK_DIR/.git ]; then
    cd $DWC2FK_DIR
    git fetch origin master -q
    LOCAL_DWC2FK_COMMIT=$(git rev-parse --short=8 HEAD)
    REMOTE_DWC2FK_COMMIT=$(git rev-parse --short=8 origin/master)
  else
    LOCAL_DWC2FK_COMMIT="${red}--------${default}"
    REMOTE_DWC2FK_COMMIT="${red}--------${default}"
  fi
}

compare_dwc2fk_versions(){
  read_dwc2fk_versions
  #echo "Local: $LOCAL_DWC2FK_COMMIT"
  #echo "Remote: $REMOTE_DWC2FK_COMMIT"
  if [ "$LOCAL_DWC2FK_COMMIT" != "$REMOTE_DWC2FK_COMMIT" ]; then
    LOCAL_DWC2FK_COMMIT="${yellow}$LOCAL_DWC2FK_COMMIT${default}"
    REMOTE_DWC2FK_COMMIT="${green}$REMOTE_DWC2FK_COMMIT${default}"
  else
    LOCAL_DWC2FK_COMMIT="${green}$LOCAL_DWC2FK_COMMIT${default}"
    REMOTE_DWC2FK_COMMIT="${green}$REMOTE_DWC2FK_COMMIT${default}"
  fi
}

read_local_dwc2_version(){
  if [ -e $DWC2_DIR/web/version ]; then
    DWC2_LOCAL_VER=$(head -n 1 $DWC2_DIR/web/version)
  else
    DWC2_LOCAL_VER="${red}-----${default}"
  fi
}

read_remote_dwc2_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    DWC2_REMOTE_VER="${red}-----${default}"
  else
    DWC2_REMOTE_VER=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep tag_name | cut -d'"' -f4)
  fi
}

compare_dwc2_versions(){
  read_local_dwc2_version
  read_remote_dwc2_version
  #echo "Local: $DWC2_LOCAL_VER"
  #echo "Remote: $DWC2_REMOTE_VER"
  if [ "$DWC2_LOCAL_VER" != "$DWC2_REMOTE_VER" ]; then
    DWC2_LOCAL_VER="${yellow}$DWC2_LOCAL_VER${default}"
    DWC2_REMOTE_VER="${green}$DWC2_REMOTE_VER${default}"
  else
    DWC2_LOCAL_VER="${green}$DWC2_LOCAL_VER${default}"
    DWC2_REMOTE_VER="${green}$DWC2_REMOTE_VER${default}"
  fi
}

read_local_mainsail_version(){
  if [ -e $MAINSAIL_DIR/version ]; then
    MAINSAIL_LOCAL_VER=$(head -n 1 $MAINSAIL_DIR/version)
  else
    MAINSAIL_LOCAL_VER="${red}-----${default}"
  fi
}

read_remote_mainsail_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    MAINSAIL_REMOTE_VER="${red}-----${default}"
  else
    get_mainsail_ver
    MAINSAIL_REMOTE_VER=$MAINSAIL_VERSION
  fi
}

compare_mainsail_versions(){
  read_local_mainsail_version
  read_remote_mainsail_version
  #echo "Local: $MAINSAIL_LOCAL_VER"
  #echo "Remote: $MAINSAIL_REMOTE_VER"
  if [ "$MAINSAIL_LOCAL_VER" != "$MAINSAIL_REMOTE_VER" ]; then
    MAINSAIL_LOCAL_VER="${yellow}$MAINSAIL_LOCAL_VER${default}"
    MAINSAIL_REMOTE_VER="${green}$MAINSAIL_REMOTE_VER${default}"
  else
    MAINSAIL_LOCAL_VER="${green}$MAINSAIL_LOCAL_VER${default}"
    MAINSAIL_REMOTE_VER="${green}$MAINSAIL_REMOTE_VER${default}"
  fi
}

read_moonraker_versions(){
  if [ -d $MOONRAKER_DIR ] && [ -d $MOONRAKER_DIR/.git ]; then
    cd $MOONRAKER_DIR
    git fetch origin master -q
    LOCAL_MOONRAKER_COMMIT=$(git rev-parse --short=8 HEAD)
    REMOTE_MOONRAKER_COMMIT=$(git rev-parse --short=8 origin/master)
  else
    LOCAL_MOONRAKER_COMMIT="${red}--------${default}"
    REMOTE_MOONRAKER_COMMIT="${red}--------${default}"
  fi
}

compare_moonraker_versions(){
  read_moonraker_versions
  #echo "Local: $LOCAL_MOONRAKER_COMMIT"
  #echo "Remote: $REMOTE_MOONRAKER_COMMIT"
  if [ "$LOCAL_MOONRAKER_COMMIT" != "$REMOTE_MOONRAKER_COMMIT" ]; then
    LOCAL_MOONRAKER_COMMIT="${yellow}$LOCAL_MOONRAKER_COMMIT${default}"
    REMOTE_MOONRAKER_COMMIT="${green}$REMOTE_MOONRAKER_COMMIT${default}"
  else
    LOCAL_MOONRAKER_COMMIT="${green}$LOCAL_MOONRAKER_COMMIT${default}"
    REMOTE_MOONRAKER_COMMIT="${green}$REMOTE_MOONRAKER_COMMIT${default}"
  fi
}

ui_print_versions(){
  compare_klipper_versions
  compare_dwc2fk_versions
  compare_dwc2_versions
  compare_moonraker_versions
  compare_mainsail_versions
}
