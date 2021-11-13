#!/bin/bash
octoprint_setup_dialog(){
  status_msg "Initializing OctoPrint installation ..."

  ### count amount of klipper services
  if [ "$(systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
    INSTANCE_COUNT=1
  else
    INSTANCE_COUNT=$(systemctl list-units --full -all -t service --no-legend | grep -E "klipper-[[:digit:]].service" | wc -l)
  fi

    whiptail --title "Install OctoPrint" \
    --yesno \
    "$INSTANCE_COUNT Klipper instances were found!

You need one OctoPrint instance per Klipper instance.

Create $INSTANCE_COUNT OctoPrint instances?" \
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
  	status_msg "Creating $INSTANCE_COUNT OctoPrint instances ..."
    octoprint_setup
  else
    whiptail --title "$KIAUH_TITLE" --msgbox "Exiting OctoPrint Install" \
      "$KIAUH_WHIPTAIL_SINGLE_LINE_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"
    return
  fi
}
