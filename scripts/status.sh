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
    # add system updates to the update all array for the update all function in the updater
    SYS_UPDATE_AVAIL="true" && update_arr+=(update_system)
    DISPLAY_SYS_UPDATE="${yellow}System upgrade available!${default}"
  else
    SYS_UPDATE_AVAIL="false"
    DISPLAY_SYS_UPDATE="${green}System up to date!       ${default}"
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
    # add mainsail to the update all array for the update all function in the updater
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
    # add fluidd to the update all array for the update all function in the updater
    FLUIDD_UPDATE_AVAIL="true" && update_arr+=(update_fluidd)
  else
    FLUIDD_LOCAL_VER=$NONE
    FLUIDD_REMOTE_VER="${green}$(printf "%-12s" "$FLUIDD_REMOTE_VER")${default}"
    FLUIDD_UPDATE_AVAIL="false"
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
    # add PGC to the update all array for the update all function in the updater
    PGC_UPDATE_AVAIL="true" && update_arr+=(update_pgc_for_klipper)
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
#  compare_klipper_versions
#  compare_dwc2fk_versions
#  compare_dwc2_versions
#  compare_moonraker_versions
#  compare_mainsail_versions
#  compare_fluidd_versions
#  compare_klipperscreen_versions
#  compare_MoonrakerTelegramBot_versions
#  compare_pgc_versions
}
