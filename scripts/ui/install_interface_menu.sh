#!/bin/bash
#
# Brief description of your script

install_interface_menu(){

	local menu_options=(
		"1" "Mainsail - lightweight & responsive web interface for Klipper"
		"2" "Fluidd - a free and open-source Klipper web interface for managing your 3d printer"
		"3" "KlipperScreen - a touchscreen GUI that interfaces with Klipper via Moonraker"
		"4" "Duet Web Control - a fully-responsive HTML5-based web interface for RepRapFirmware"
		"5" "OctoPrint - a snappy web interface for controlling consumer 3D printers."
	)
  local menu_str="Select an interface to install, you can install multiple interfaces."

  while true; do
    local menu
    menu=$(whiptail --title "Install Interface" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
        1) do_action "install_webui mainsail";;
      	2) do_action "install_webui fluidd";;
      	3) do_action "install_klipperscreen";;
      	4) do_action "dwc_setup_dialog";;
      	5) do_action "octoprint_setup_dialog";;
				esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
