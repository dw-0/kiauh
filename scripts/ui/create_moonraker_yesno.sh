#!/bin/bash
create_moonraker_yesno(){
  whiptail --title "Confirm Instance Count" --yesno \
"$SERVICE_COUNT Klipper instances were found!

You need one Moonraker instance per Klipper instance. 

Create $SERVICE_COUNT Moonraker instances?" \
  "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
    status_msg "Creating $SERVICE_COUNT Moonraker instances ..."
    moonraker_setup
  else
    warn_msg "Exiting Moonraker setup ..."
  fi
}