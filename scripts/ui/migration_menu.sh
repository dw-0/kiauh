#!/bin/bash

migration_menu(){
	local menu_options=(
		"1" "Migrate MainsailOS"
		"2" "Migrate FluiddPi"
	)
  local menu_str="This function will help you to migrate a vanilla MainsailOS or FluiddPi image to a newer state.
Only use this function if you use MainsailOS 0.4.0 or lower, or FluiddPi v1.13.0 or lower.
Please have a look at the KIAUH changelog for more details on what this function will do."

  while true; do
    local menu
    menu=$(whiptail --title "CustomPiOS Migration" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) migrate_custompios "mainsail";;
      	2) migrate_custompios "fluiddpi";;
			esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
