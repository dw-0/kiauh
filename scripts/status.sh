kiauh_status(){
  if [ -d "${SRCDIR}/kiauh/.git" ]; then
    cd ${SRCDIR}/kiauh
    if git branch -a | grep "* master" -q; then
      git fetch -q
      if [[ "$(git rev-parse --short=8 origin/master)" != "$(git rev-parse --short=8 HEAD)" ]]; then
        KIAUH_UPDATE_AVAIL="true"
      fi
    fi
  fi
}

check_system_updates(){
  SYS_UPDATE=$(apt list --upgradeable 2>/dev/null | sed "1d")
  if [ ! -z "$SYS_UPDATE" ]; then
    SYS_UPDATE_AVAIL="true"
    DISPLAY_SYS_UPDATE="${yellow}System upgrade available!${default}"
  else
    SYS_UPDATE_AVAIL="false"
    DISPLAY_SYS_UPDATE="${green}System up to date!       ${default}"
  fi
}

klipper_status(){
  kcount=0
  klipper_data=(
    SERVICE
    $KLIPPER_DIR
    $KLIPPY_ENV_DIR
  )

  ### count amount of klipper service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "^klipper(\-[[:digit:]]+)?\.service$" | wc -l)

  ### a fix to detect an existing "legacy" klipper init.d installation
  if [ -f /etc/init.d/klipper ] && [ -f /etc/init.d/klipper ]; then
    SERVICE_FILE_COUNT=1
  fi

  ### remove the "SERVICE" entry from the klipper_data array if a klipper service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset klipper_data[0]

  ### count+1 for each found data-item from array
  for kd in "${klipper_data[@]}"
  do
    if [ -e $kd ]; then
      kcount=$(expr $kcount + 1)
    fi
  done

  ### display status
  if [ "$kcount" == "${#klipper_data[*]}" ]; then
    KLIPPER_STATUS="$(printf "${green}Installed: %-5s${default}" $SERVICE_FILE_COUNT)"
  elif [ "$kcount" == 0 ]; then
    KLIPPER_STATUS="${red}Not installed!${default}  "
  else
    KLIPPER_STATUS="${yellow}Incomplete!${default}     "
  fi
}

dwc2_status(){
  dcount=0
  dwc_data=(
    SERVICE
    $DWC2_DIR
    $DWC2FK_DIR
    $DWC_ENV_DIR
  )

  ### count amount of dwc service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "^dwc(\-[[:digit:]]+)?\.service$" | wc -l)

  ### remove the "SERVICE" entry from the dwc_data array if a dwc service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset dwc_data[0]

  #count+1 for each found data-item from array
  for dd in "${dwc_data[@]}"
  do
    if [ -e $dd ]; then
      dcount=$(expr $dcount + 1)
    fi
  done

  if [ "$dcount" == "${#dwc_data[*]}" ]; then
    DWC2_STATUS="$(printf "${green}Installed: %-5s${default}" $SERVICE_FILE_COUNT)"
  elif [ "$dcount" == 0 ]; then
    DWC2_STATUS="${red}Not installed!${default}  "
  else
    DWC2_STATUS="${yellow}Incomplete!${default}     "
  fi
}

moonraker_status(){
  mrcount=0
  moonraker_data=(
    SERVICE
    $MOONRAKER_DIR
    $MOONRAKER_ENV_DIR
  )

  ### count amount of moonraker service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "^moonraker(\-[[:digit:]]+)?\.service$" | wc -l)

  ### remove the "SERVICE" entry from the moonraker_data array if a moonraker service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset moonraker_data[0]

  ### count+1 for each found data-item from array
  for mrd in "${moonraker_data[@]}"
  do
    if [ -e $mrd ]; then
      mrcount=$(expr $mrcount + 1)
    fi
  done

  ### display status
  if [ "$mrcount" == "${#moonraker_data[*]}" ]; then
    MOONRAKER_STATUS="$(printf "${green}Installed: %-5s${default}" $SERVICE_FILE_COUNT)"
  elif [ "$mrcount" == 0 ]; then
    MOONRAKER_STATUS="${red}Not installed!${default}  "
  else
    MOONRAKER_STATUS="${yellow}Incomplete!${default}     "
  fi
}

mainsail_status(){
  mcount=0
  mainsail_data=(
    $MAINSAIL_DIR
    $NGINX_SA/mainsail
    $NGINX_SE/mainsail
  )
  #count+1 for each found data-item from array
  for md in "${mainsail_data[@]}"
  do
    if [ -e $md ]; then
      mcount=$(expr $mcount + 1)
    fi
  done
  if [ "$mcount" == "${#mainsail_data[*]}" ]; then
    MAINSAIL_STATUS="${green}Installed!${default}      "
  elif [ "$mcount" == 0 ]; then
    MAINSAIL_STATUS="${red}Not installed!${default}  "
  else
    MAINSAIL_STATUS="${yellow}Incomplete!${default}     "
  fi
}

fluidd_status(){
  fcount=0
  fluidd_data=(
    $FLUIDD_DIR
    $NGINX_SA/fluidd
    $NGINX_SE/fluidd
  )
  #count+1 for each found data-item from array
  for fd in "${fluidd_data[@]}"
  do
    if [ -e $fd ]; then
      fcount=$(expr $fcount + 1)
    fi
  done
  if [ "$fcount" == "${#fluidd_data[*]}" ]; then
    FLUIDD_STATUS="${green}Installed!${default}      "
  elif [ "$fcount" == 0 ]; then
    FLUIDD_STATUS="${red}Not installed!${default}  "
  else
    FLUIDD_STATUS="${yellow}Incomplete!${default}     "
  fi
}

octoprint_status(){
  ocount=0
  octoprint_data=(
    SERVICE
    $OCTOPRINT_DIR
  )
  ### count amount of octoprint service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "^octoprint(\-[[:digit:]]+)?\.service$" | wc -l)

  ### remove the "SERVICE" entry from the octoprint_data array if a octoprint service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset octoprint_data[0]

  #count+1 for each found data-item from array
  for op in "${octoprint_data[@]}"
  do
    if [ -e $op ]; then
      ocount=$(expr $ocount + 1)
    fi
  done

  ### display status
  if [ "$ocount" == "${#octoprint_data[*]}" ]; then
    OCTOPRINT_STATUS="$(printf "${green}Installed: %-5s${default}" $SERVICE_FILE_COUNT)"
  elif [ "$ocount" == 0 ]; then
    OCTOPRINT_STATUS="${red}Not installed!${default}  "
  else
    OCTOPRINT_STATUS="${yellow}Incomplete!${default}     "
  fi
}

klipperscreen_status(){
  klsccount=0
  klipperscreen_data=(
    SERVICE
    $KLIPPERSCREEN_DIR
    $KLIPPERSCREEN_ENV_DIR
  )

  ### count amount of klipperscreen_data service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "KlipperScreen" | wc -l)

  ### remove the "SERVICE" entry from the klipperscreen_data array if a KlipperScreen service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset klipperscreen_data[0]

  #count+1 for each found data-item from array
  for klscd in "${klipperscreen_data[@]}"
  do
    if [ -e $klscd ]; then
      klsccount=$(expr $klsccount + 1)
    fi
  done
  if [ "$klsccount" == "${#klipperscreen_data[*]}" ]; then
    KLIPPERSCREEN_STATUS="${green}Installed!${default}      "
  elif [ "$klsccount" == 0 ]; then
    KLIPPERSCREEN_STATUS="${red}Not installed!${default}  "
  else
    KLIPPERSCREEN_STATUS="${yellow}Incomplete!${default}     "
  fi
}

MoonrakerTelegramBot_status(){
  mtbcount=0
  MoonrakerTelegramBot_data=(
    SERVICE
    $MOONRAKER_TELEGRAM_BOT_DIR
    $MOONRAKER_TELEGRAM_BOT_ENV_DIR
  )

  ### count amount of MoonrakerTelegramBot_data service files in /etc/systemd/system
  SERVICE_FILE_COUNT=$(ls /etc/systemd/system | grep -E "moonraker-telegram-bot" | wc -l)

  ### remove the "SERVICE" entry from the MoonrakerTelegramBot_data array if a MoonrakerTelegramBot service is installed
  [ $SERVICE_FILE_COUNT -gt 0 ] && unset MoonrakerTelegramBot_data[0]

  #count+1 for each found data-item from array
  for mtbd in "${MoonrakerTelegramBot_data[@]}"
  do
    if [ -e $mtbd ]; then
      mtbcount=$(expr $mtbcount + 1)
    fi
  done
  if [ "$mtbcount" == "${#MoonrakerTelegramBot_data[*]}" ]; then
    MOONRAKER_TELEGRAM_BOT_STATUS="${green}Installed!${default}      "
  elif [ "$mtbcount" == 0 ]; then
    MOONRAKER_TELEGRAM_BOT_STATUS="${red}Not installed!${default}  "
  else
    MOONRAKER_TELEGRAM_BOT_STATUS="${yellow}Incomplete!${default}     "
  fi
}

#############################################################
#############################################################

### reading the klipper branch the user is currently on
read_branch(){
  if [ -d $KLIPPER_DIR/.git ]; then
    cd $KLIPPER_DIR
    GET_BRANCH="$(git branch | grep "*" | cut -d"*" -f2 | cut -d" " -f2)"
    ### try to fix a detached HEAD state and read the correct branch from the output you get
    if [ "$(echo $GET_BRANCH | grep "HEAD" )" ]; then
      DETACHED_HEAD="true"
      GET_BRANCH=$(git branch | grep "HEAD" | rev | cut -d" " -f1 | rev | cut -d")" -f1 | cut -d"/" -f2)
      ### try to identify the branch when the HEAD was detached at a single commit
      ### will only work if its either master, scurve-shaping or scurve-smoothing branch
      if [[ $GET_BRANCH =~ [[:alnum:]] ]]; then
        if [ "$(git branch -r --contains $GET_BRANCH | grep "master")" ]; then
          GET_BRANCH="master"
        elif [ "$(git branch -r --contains $GET_BRANCH | grep "scurve-shaping")" ]; then
          GET_BRANCH="scurve-shaping"
        elif [ "$(git branch -r --contains $GET_BRANCH | grep "scurve-smoothing")" ]; then
          GET_BRANCH="scurve-smoothing"
        fi
      fi
    fi
  else
    GET_BRANCH=""
  fi
}

#prints the current klipper branch in the main menu
print_branch(){
  read_branch
  if [ ! -z "$GET_BRANCH" ]; then
    PRINT_BRANCH="$(printf "%-16s" "$GET_BRANCH")"
  else
    PRINT_BRANCH="${red}--------------${default}  "
  fi
}

read_local_klipper_commit(){
  if [ -d $KLIPPER_DIR ] && [ -d $KLIPPER_DIR/.git ]; then
    cd $KLIPPER_DIR
    LOCAL_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_COMMIT=$NONE
  fi
}

read_remote_klipper_commit(){
  read_branch
  if [ ! -z "$GET_BRANCH" ];then
    if [ "$GET_BRANCH" = "origin/master" ] || [ "$GET_BRANCH" = "master" ]; then
      git fetch origin -q
      REMOTE_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
    elif [ "$GET_BRANCH" = "scurve-shaping" ]; then
      git fetch dmbutyugin scurve-shaping -q
      REMOTE_COMMIT=$(git describe dmbutyugin/scurve-shaping --always --tags | cut -d "-" -f 1,2)
    elif [ "$GET_BRANCH" = "scurve-smoothing" ]; then
      git fetch dmbutyugin scurve-smoothing -q
      REMOTE_COMMIT=$(git describe dmbutyugin/scurve-smoothing --always --tags | cut -d "-" -f 1,2)
    fi
  else
    REMOTE_COMMIT=$NONE
  fi
}

compare_klipper_versions(){
  unset KLIPPER_UPDATE_AVAIL
  read_local_klipper_commit && read_remote_klipper_commit
  if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    LOCAL_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_COMMIT")${default}"
    REMOTE_COMMIT="${green}$(printf "%-12s" "$REMOTE_COMMIT")${default}"
    KLIPPER_UPDATE_AVAIL="true"
    update_arr+=(update_klipper)
  else
    LOCAL_COMMIT="${green}$(printf "%-12s" "$LOCAL_COMMIT")${default}"
    REMOTE_COMMIT="${green}$(printf "%-12s" "$REMOTE_COMMIT")${default}"
    KLIPPER_UPDATE_AVAIL="false"
  fi
  #if detached head was found, force the user with warn message to update klipper
  if [ "$DETACHED_HEAD" == "true" ]; then
    LOCAL_COMMIT="${red}$(printf "%-12s" "Need update!")${default}"
  fi
}

#############################################################
#############################################################

read_dwc2fk_versions(){
  if [ -d $DWC2FK_DIR ] && [ -d $DWC2FK_DIR/.git ]; then
    cd $DWC2FK_DIR
    git fetch origin master -q
    LOCAL_DWC2FK_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_DWC2FK_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_DWC2FK_COMMIT=$NONE
    REMOTE_DWC2FK_COMMIT=$NONE
  fi
}

compare_dwc2fk_versions(){
  unset DWC2FK_UPDATE_AVAIL
  read_dwc2fk_versions
  if [ "$LOCAL_DWC2FK_COMMIT" != "$REMOTE_DWC2FK_COMMIT" ]; then
    LOCAL_DWC2FK_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_DWC2FK_COMMIT")${default}"
    REMOTE_DWC2FK_COMMIT="${green}$(printf "%-12s" "$REMOTE_DWC2FK_COMMIT")${default}"
    DWC2FK_UPDATE_AVAIL="true"
    update_arr+=(update_dwc2fk)
  else
    LOCAL_DWC2FK_COMMIT="${green}$(printf "%-12s" "$LOCAL_DWC2FK_COMMIT")${default}"
    REMOTE_DWC2FK_COMMIT="${green}$(printf "%-12s" "$REMOTE_DWC2FK_COMMIT")${default}"
    DWC2FK_UPDATE_AVAIL="false"
  fi
}

read_local_dwc2_version(){
  unset DWC2_VER_FOUND
  if [ -e $DWC2_DIR/.version ]; then
    DWC2_VER_FOUND="true"
    DWC2_LOCAL_VER=$(head -n 1 $DWC2_DIR/.version)
  else
    DWC2_VER_FOUND="false" && unset DWC2_LOCAL_VER
  fi
}

read_remote_dwc2_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    DWC2_REMOTE_VER=$NONE
  else
    get_dwc_ver
    DWC2_REMOTE_VER=$DWC2_VERSION
  fi
}

compare_dwc2_versions(){
  unset DWC2_UPDATE_AVAIL
  read_local_dwc2_version && read_remote_dwc2_version
  if [[ $DWC2_VER_FOUND = "true" ]] && [[ $DWC2_LOCAL_VER == $DWC2_REMOTE_VER ]]; then
    #printf fits the string for displaying it in the ui to a total char length of 12
    DWC2_LOCAL_VER="${green}$(printf "%-12s" "$DWC2_LOCAL_VER")${default}"
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
  elif [[ $DWC2_VER_FOUND = "true" ]] && [[ $DWC2_LOCAL_VER != $DWC2_REMOTE_VER ]]; then
    DWC2_LOCAL_VER="${yellow}$(printf "%-12s" "$DWC2_LOCAL_VER")${default}"
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
    # set flag for the multi update function
    DWC2_UPDATE_AVAIL="true" && update_arr+=(update_dwc2)
  else
    DWC2_LOCAL_VER=$NONE
    DWC2_REMOTE_VER="${green}$(printf "%-12s" "$DWC2_REMOTE_VER")${default}"
    DWC2_UPDATE_AVAIL="false"
  fi
}

#############################################################
#############################################################

read_moonraker_versions(){
  if [ -d $MOONRAKER_DIR ] && [ -d $MOONRAKER_DIR/.git ]; then
    cd $MOONRAKER_DIR
    git fetch origin master -q
    LOCAL_MOONRAKER_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_MOONRAKER_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_MOONRAKER_COMMIT=$NONE
    REMOTE_MOONRAKER_COMMIT=$NONE
  fi
}

compare_moonraker_versions(){
  unset MOONRAKER_UPDATE_AVAIL
  read_moonraker_versions
  if [ "$LOCAL_MOONRAKER_COMMIT" != "$REMOTE_MOONRAKER_COMMIT" ]; then
    LOCAL_MOONRAKER_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_MOONRAKER_COMMIT")${default}"
    REMOTE_MOONRAKER_COMMIT="${green}$(printf "%-12s" "$REMOTE_MOONRAKER_COMMIT")${default}"
    MOONRAKER_UPDATE_AVAIL="true"
    update_arr+=(update_moonraker)
  else
    LOCAL_MOONRAKER_COMMIT="${green}$(printf "%-12s" "$LOCAL_MOONRAKER_COMMIT")${default}"
    REMOTE_MOONRAKER_COMMIT="${green}$(printf "%-12s" "$REMOTE_MOONRAKER_COMMIT")${default}"
    MOONRAKER_UPDATE_AVAIL="false"
  fi
}

read_local_mainsail_version(){
  unset MAINSAIL_VER_FOUND
  if [ -e $MAINSAIL_DIR/.version ]; then
    MAINSAIL_VER_FOUND="true"
    MAINSAIL_LOCAL_VER=$(head -n 1 $MAINSAIL_DIR/.version)
  else
    MAINSAIL_VER_FOUND="false" && unset MAINSAIL_LOCAL_VER
  fi
}

read_remote_mainsail_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    MAINSAIL_REMOTE_VER=$NONE
  else
    get_mainsail_ver
    MAINSAIL_REMOTE_VER=$MAINSAIL_VERSION
  fi
}

compare_mainsail_versions(){
  unset MAINSAIL_UPDATE_AVAIL
  read_local_mainsail_version && read_remote_mainsail_version
  if [[ $MAINSAIL_VER_FOUND = "true" ]] && [[ $MAINSAIL_LOCAL_VER == $MAINSAIL_REMOTE_VER ]]; then
    #printf fits the string for displaying it in the ui to a total char length of 12
    MAINSAIL_LOCAL_VER="${green}$(printf "%-12s" "$MAINSAIL_LOCAL_VER")${default}"
    MAINSAIL_REMOTE_VER="${green}$(printf "%-12s" "$MAINSAIL_REMOTE_VER")${default}"
  elif [[ $MAINSAIL_VER_FOUND = "true" ]] && [[ $MAINSAIL_LOCAL_VER != $MAINSAIL_REMOTE_VER ]]; then
    MAINSAIL_LOCAL_VER="${yellow}$(printf "%-12s" "$MAINSAIL_LOCAL_VER")${default}"
    MAINSAIL_REMOTE_VER="${green}$(printf "%-12s" "$MAINSAIL_REMOTE_VER")${default}"
    # set flag for the multi update function
    MAINSAIL_UPDATE_AVAIL="true" && update_arr+=(update_mainsail)
  else
    MAINSAIL_LOCAL_VER=$NONE
    MAINSAIL_REMOTE_VER="${green}$(printf "%-12s" "$MAINSAIL_REMOTE_VER")${default}"
    MAINSAIL_UPDATE_AVAIL="false"
  fi
}

read_local_fluidd_version(){
  unset FLUIDD_VER_FOUND
  if [ -e $FLUIDD_DIR/.version ]; then
    FLUIDD_VER_FOUND="true"
    FLUIDD_LOCAL_VER=$(head -n 1 $FLUIDD_DIR/.version)
  else
    FLUIDD_VER_FOUND="false" && unset FLUIDD_LOCAL_VER
  fi
}

read_remote_fluidd_version(){
  #remote checks don't work without curl installed!
  if [[ ! $(dpkg-query -f'${Status}' --show curl 2>/dev/null) = *\ installed ]]; then
    FLUIDD_REMOTE_VER=$NONE
  else
    get_fluidd_ver
    FLUIDD_REMOTE_VER=$FLUIDD_VERSION
  fi
}

compare_fluidd_versions(){
  unset FLUIDD_UPDATE_AVAIL
  read_local_fluidd_version && read_remote_fluidd_version
  if [[ $FLUIDD_VER_FOUND = "true" ]] && [[ $FLUIDD_LOCAL_VER == $FLUIDD_REMOTE_VER ]]; then
    #printf fits the string for displaying it in the ui to a total char length of 12
    FLUIDD_LOCAL_VER="${green}$(printf "%-12s" "$FLUIDD_LOCAL_VER")${default}"
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
  elif [[ $FLUIDD_VER_FOUND = "true" ]] && [[ $FLUIDD_LOCAL_VER != $FLUIDD_REMOTE_VER ]]; then
    FLUIDD_LOCAL_VER="${yellow}$(printf "%-12s" "$FLUIDD_LOCAL_VER")${default}"
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
    # set flag for the multi update function
    FLUIDD_UPDATE_AVAIL="true" && update_arr+=(update_fluidd)
  else
    FLUIDD_LOCAL_VER=$NONE
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
    FLUIDD_UPDATE_AVAIL="false"
  fi
}

read_klipperscreen_versions(){
  if [ -d $KLIPPERSCREEN_DIR ] && [ -d $KLIPPERSCREEN_DIR/.git ]; then
    cd $KLIPPERSCREEN_DIR
    git fetch origin master -q
    LOCAL_KLIPPERSCREEN_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_KLIPPERSCREEN_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_KLIPPERSCREEN_COMMIT=$NONE
    REMOTE_KLIPPERSCREEN_COMMIT=$NONE
  fi
}

compare_klipperscreen_versions(){
  unset KLIPPERSCREEN_UPDATE_AVAIL
  read_klipperscreen_versions
  if [ "$LOCAL_KLIPPERSCREEN_COMMIT" != "$REMOTE_KLIPPERSCREEN_COMMIT" ]; then
    LOCAL_KLIPPERSCREEN_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_KLIPPERSCREEN_COMMIT")${default}"
    REMOTE_KLIPPERSCREEN_COMMIT="${green}$(printf "%-12s" "$REMOTE_KLIPPERSCREEN_COMMIT")${default}"
    KLIPPERSCREEN_UPDATE_AVAIL="true"
    update_arr+=(update_klipperscreen)
  else
    LOCAL_KLIPPERSCREEN_COMMIT="${green}$(printf "%-12s" "$LOCAL_KLIPPERSCREEN_COMMIT")${default}"
    REMOTE_KLIPPERSCREEN_COMMIT="${green}$(printf "%-12s" "$REMOTE_KLIPPERSCREEN_COMMIT")${default}"
    KLIPPERSCREEN_UPDATE_AVAIL="false"
  fi
}

read_MoonrakerTelegramBot_versions(){
  if [ -d $MOONRAKER_TELEGRAM_BOT_DIR ] && [ -d $MOONRAKER_TELEGRAM_BOT_DIR/.git ]; then
    cd $MOONRAKER_TELEGRAM_BOT_DIR
    git fetch origin master -q
    LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT=$(git describe origin/master --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT=$NONE
    REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT=$NONE
  fi
}

compare_MoonrakerTelegramBot_versions(){
  unset MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL
  read_MoonrakerTelegramBot_versions
  if [ "$LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT" != "$REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT" ]; then
    LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT")${default}"
    REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT="${green}$(printf "%-12s" "$REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT")${default}"
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="true"
    update_arr+=(update_MoonrakerTelegramBot)
  else
    LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT="${green}$(printf "%-12s" "$LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT")${default}"
    REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT="${green}$(printf "%-12s" "$REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT")${default}"
    MOONRAKER_TELEGRAM_BOT_UPDATE_AVAIL="false"
  fi
}


#############################################################
#############################################################

read_pgc_versions(){
  PGC_DIR="${HOME}/pgcode"
  if [ -d $PGC_DIR ] && [ -d $PGC_DIR/.git ]; then
    cd $PGC_DIR
    git fetch origin main -q
    LOCAL_PGC_COMMIT=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
    REMOTE_PGC_COMMIT=$(git describe origin/main --always --tags | cut -d "-" -f 1,2)
  else
    LOCAL_PGC_COMMIT=$NONE
    REMOTE_PGC_COMMIT=$NONE
  fi
}

compare_pgc_versions(){
  unset PGC_UPDATE_AVAIL
  read_pgc_versions
  if [ "$LOCAL_PGC_COMMIT" != "$REMOTE_PGC_COMMIT" ]; then
    LOCAL_PGC_COMMIT="${yellow}$(printf "%-12s" "$LOCAL_PGC_COMMIT")${default}"
    REMOTE_PGC_COMMIT="${green}$(printf "%-12s" "$REMOTE_PGC_COMMIT")${default}"
    PGC_UPDATE_AVAIL="true"
    update_arr+=(update_pgc_for_klipper)
  else
    LOCAL_PGC_COMMIT="${green}$(printf "%-12s" "$LOCAL_PGC_COMMIT")${default}"
    REMOTE_PGC_COMMIT="${green}$(printf "%-12s" "$REMOTE_PGC_COMMIT")${default}"
    PGC_UPDATE_AVAIL="false"
  fi
}

#############################################################
#############################################################

#display this as placeholder if no version/commit could be fetched
NONE="${red}$(printf "%-12s" "--------")${default}"

ui_print_versions(){
  unset update_arr
  check_system_updates
  compare_klipper_versions
  compare_dwc2fk_versions
  compare_dwc2_versions
  compare_moonraker_versions
  compare_mainsail_versions
  compare_fluidd_versions
  compare_klipperscreen_versions
  compare_MoonrakerTelegramBot_versions
  compare_pgc_versions
}
