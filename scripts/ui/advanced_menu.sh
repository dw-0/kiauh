#!/bin/bash

advanced_menu(){

	local menu_options=(
			"1" " "
			"2" "Switch Klipper Branch"
			"3" "Rollback Klipper"
			"4" "Build Firmware"
			"5" "Flash Firmware"
			"6" "Build and Flash Firmware"
			"7" "Get MCU ID"
			"8" "Install Mainsail Theme"
			"9" "Change System Hostname"
			"10" "Run Shell Command"
			"11" "CustomPiOS Migration Helper"
			)

  while true; do
		read_octoprint_service_status
		menu_options[2]="Current OctoPrint Status: $OPRINT_SERVICE_STATUS"

  	if [ ! "$OPRINT_SERVICE_STATUS" == "" ]; then
			local menu
			menu=$(whiptail --title "Advanced Menu" --cancel-button "Back" --notags --menu "Perform Action:"\
			"$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
		else
			local menu
			menu=$(whiptail --title "Advanced Menu" --cancel-button "Back" --notags --menu "Perform Action:"\
			"$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]:2}" 3>&1 1>&2 2>&3)
		fi

		local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
			1) clear
					print_header
					toggle_octoprint_service
					read_octoprint_service_status
					print_msg && clear_msg;;
			2) do_action "switch_menu" ;;
			3) do_action "load_klipper_state";;
			4) do_action "build_fw" ;;
			5) do_action "select_flash_method" ;;
			6) clear && print_header
					status_msg "Please wait..."
					build_fw
					select_flash_method
					print_msg && clear_msg;;
			7) do_action "select_mcu_connection" ;;
			8) do_action "select_flash_method" ;;
			9) do_action "ms_theme_menu";;
			10) do_action "setup_gcode_shell_command" ;;
			11) migration_menu;;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
