#!/bin/bash
octoprint_setup_yesno(){
  status_msg "Initializing OctoPrint installation ..."

  ### count amount of klipper services
  count_klipper_services

  whiptail --title "Install OctoPrint" --no-button --yesno "$SERVICE_COUNT Klipper instances were found!

You need one OctoPrint instance per Klipper instance.

Create $SERVICE_COUNT OctoPrint instances?" \
  "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
  	status_msg "Creating $SERVICE_COUNT OctoPrint instances ..."
    octoprint_setup
  fi
}
