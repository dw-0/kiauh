#!/bin/bash

remove_menu(){
	#TODO Currently it's a "dumb" remove page, looking for a "smart" one
	local menu_options=(
		"1" "Klipper"
		"2" "Klipper API(Moonraker)"
		"3" "Interfaces"
		"4" "Other"
	)
  local menu_str="Directories which remain untouched:

Your printer configuration directory
~/kiauh-backups

You need remove them manually if you wish so."

  while true; do
    local menu
    menu=$(whiptail --title "Remove Menu" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) do_action "remove_klipper";;
      	2) do_action "remove_moonraker";;
      	3) remove_interface_menu;;
      	4) remove_other_menu;;
				esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
