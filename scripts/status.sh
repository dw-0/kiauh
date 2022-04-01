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

#############################################################
#############################################################

#display this as placeholder if no version/commit could be fetched
NONE="${red}$(printf "%-12s" "--------")${default}"

ui_print_versions(){
  unset update_arr
  check_system_updates
#  compare_klipper_versions
#  compare_moonraker_versions
#  compare_mainsail_versions
#  compare_fluidd_versions
#  compare_klipperscreen_versions
#  compare_MoonrakerTelegramBot_versions
#  compare_pgc_versions
}
