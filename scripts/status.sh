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
    $TORNADO_DIR1
    $TORNADO_DIR2
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
    $MAINSAIL_SERVICE1
    $MAINSAIL_SERVICE2
    $MAINSAIL_DIR
    #${HOME}/.klippy_api_key
    #${HOME}/.moonraker_api_key
    #${HOME}/moonraker-env
    /etc/nginx/sites-available/mainsail
    /etc/nginx/sites-enabled/mainsail
    /etc/init.d/nginx
    /etc/default/nginx
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

read_branch(){
  if [ -d $KLIPPER_DIR ] && [ -d $KLIPPER_DIR/.git ]; then
    cd $KLIPPER_DIR
    GET_BRANCH=$(git branch -a | head -1 | cut -d " " -f5 | cut -d ")" -f1)
    #if reading the branch gives an empty string
    #we are on non-detached HEAD state on origin/master
    #and need to set GET_BRANCH to make a non-empty string
    if [ -z $GET_BRANCH ]; then
      GET_BRANCH="origin/master"
    fi
  else
    GET_BRANCH=""
  fi
}

print_branch(){
  read_branch
  if [ "$GET_BRANCH" == "origin/master" ]; then
    PRINT_BRANCH="${cyan}$GET_BRANCH${default}      "
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-shaping" ]; then
    PRINT_BRANCH="${cyan}scurve-shaping${default}     "
  elif [ "$GET_BRANCH" == "dmbutyugin/scurve-smoothing" ]; then
    PRINT_BRANCH="${cyan}scurve-smoothing${default}   "
  elif [ "$GET_BRANCH" == "Arksine/work-web_server-20200131" ]; then
    PRINT_BRANCH="${cyan}moonraker${default}          "
  elif [ "$GET_BRANCH" == "Arksine/dev-moonraker-testing" ]; then
    PRINT_BRANCH="${cyan}dev-moonraker${default}      "
  else
    PRINT_BRANCH="${red}----${default}               "
  fi
}

read_local_klipper_commit(){
  if [ -d $KLIPPER_DIR ] && [ -d $KLIPPER_DIR/.git ]; then
    cd $KLIPPER_DIR
    LOCAL_COMMIT=$(git rev-parse --short=8 HEAD)
  else
    LOCAL_COMMIT=""
  fi
}

read_remote_klipper_commit(){
  read_branch
  if [ ! -z $GET_BRANCH ];then
    REMOTE_COMMIT=$(git rev-parse --short=8 $GET_BRANCH)
  else
    REMOTE_COMMIT=""
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
    LOCAL_DWC2FK_COMMIT=$(git rev-parse --short=8 HEAD)
    REMOTE_DWC2FK_COMMIT=$(git rev-parse --short=8 origin/master)
  else
    LOCAL_DWC2FK_COMMIT=""
    REMOTE_DWC2FK_COMMIT=""
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
    DWC2_LOCAL_VER=""
  fi
}

read_remote_dwc2_version(){
  DWC2_REMOTE_VER=$(curl -s https://api.github.com/repositories/28820678/releases/latest | grep tag_name | cut -d'"' -f4)
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
    MAINSAIL_LOCAL_VER=""
  fi
}

read_remote_mainsail_version(){
  get_mainsail_ver
  MAINSAIL_REMOTE_VER=$MAINSAIL_VERSION
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

ui_print_versions(){
  compare_klipper_versions
  compare_dwc2fk_versions
  compare_dwc2_versions
  compare_mainsail_versions
}