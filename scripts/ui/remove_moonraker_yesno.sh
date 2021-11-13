#!/bin/bash
remove_moonraker_yesno(){
	  whiptail --title "Remove" \
    --yesno \
    "Do you want to remove Moonraker afterwards?

    This is useful in case you want to switch from a single-instance to a multi-instance installation, which makes a re-installation of Moonraker necessary.

    If for any other reason you only want to uninstall Klipper, please select 'No' and continue." \
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
    REM_MR="true"
  else
    REM_MR="false"
}