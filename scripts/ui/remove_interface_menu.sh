#!/bin/bash
#
# Brief description of your script

remove_interface_menu(){

	local menu_options=(
		"$MAINSAIL" "lightweight & responsive web interface"
		"$FLUIDD" "Klipper web interface"
		"$KLIPPERSCREEN" "a touchscreen GUI"
		"$DWC" "web interface for RepRapFirmware"
		"$OCTOPRINT" "a snappy web interface"
	)
  local menu_str="Select an interface to install, you can install multiple interfaces."

  while true; do
    local menu
    menu=$(whiptail --title "Install Interface" --cancel-button "Back" --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
		case "$menu" in
        "$MAINSAIL") do_action "remove_mainsail";;
      	"$FLUIDD") do_action "remove_fluidd";;
      	"$KLIPPERSCREEN") do_action "remove_klipperscreen";;
      	"$DWC") do_action "remove_dwc2";;
      	"$OCTOPRINT") do_action "remove_octoprint";;
		esac
	else
		# Unexpected event, no clue what happened
		exit 1
	fi
  done
}
