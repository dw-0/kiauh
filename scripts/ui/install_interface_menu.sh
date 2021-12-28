#!/bin/bash
#
# Brief description of your script

install_interface_menu(){

	local menu_options=(
		"1" "Mainsail - lightweight & responsive web interface"
		"2" "Fluidd - Klipper web interface"
		"3" "KlipperScreen - a touchscreen GUI"
		"4" "Duet Web Control - Duet web interface"
		"5" "OctoPrint - a snappy web interface"
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
