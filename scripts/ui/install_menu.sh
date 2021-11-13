#!/bin/bash

install_menu(){
	local menu_options=(
		"1" "Klipper"
		"2" "Klipper API(Moonraker)"
		"3" "Interfaces"
		"4" "Other"
	)
  local menu_str="You need this menu usually only for installing all necessary dependencies for the various functions on a completely fresh system."

  while true; do
    local menu
    menu=$(whiptail --title "Install" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) do_action "klipper_setup_dialog";;
      	2) do_action "moonraker_setup_dialog";;
      	3) install_interface_menu;;
      	4) install_other_menu;;
				esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
