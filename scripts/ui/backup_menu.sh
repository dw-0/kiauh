#!/bin/bash

backup_menu(){

	local menu_options=(
			"1" "Klipper configs"
			"2" "Klipper"
			"3" "Moonraker"
			"4" "Moonraker DB"
			"5" "Mainsail"
			"6" "KlipperScreen"
			"7" "Duet Web Control"
			"8" "OctoPrint"
			"9" "MoonrakerTelegramBot"
			)

	local menu_str="Backup location: ~/kiauh-backups"
  while true; do
			local menu
			menu=$(whiptail --title "Backup Menu" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:"\
			"$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)

		local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
				0) do_action "backup_klipper_config_dir";;
				1) do_action "backup_klipper";;
				2) do_action "backup_moonraker";;
				3) do_action "backup_moonraker_database";;
				4) do_action "backup_mainsail";;
				5) do_action "backup_fluidd";;
				6) do_action "backup_klipperscreen";;
				7) do_action "backup_dwc2";;
				8) do_action "backup_octoprint";;
				9) do_action "backup_MoonrakerTelegramBot";;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
