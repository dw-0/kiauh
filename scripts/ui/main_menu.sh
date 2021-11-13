#!/bin/bash

main_menu() {
  #print KIAUH update msg if update available
  local menu_options=(
			"1" "Install"
			"2" "Update"
			"3" "Remove"
			"4" "Advanced Settings"
			"5" "Backup"
			"6" "Settings"
			"7" "Upload Log"
			"8" "Service"
			)

	# Ask for update only once
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    kiauh_update_yesno
  fi

	while true; do
		#check install status
		#TODO it is install status, introduce a "service status" for service menu is probably a good idea, refactor required
		check_kiauh_version
		klipper_status
		moonraker_status
		dwc2_status
		fluidd_status
		mainsail_status
		octoprint_status
		klipperscreen_status
		update_moonraker_telegram_bot_status
		get_branch
		print_msg && clear_msg

    local menu_str="Klipper: $KLIPPER_STATUS Branch: $PRINT_BRANCH\n
Moonraker: $MOONRAKER_STATUS\n
Mainsail: $MAINSAIL_STATUS Fluidd: $FLUIDD_STATUS
KlipperScreen: $KLIPPERSCREEN_STATUS Telegram Bot: $MOONRAKER_TELEGRAM_BOT_STATUS
DWC2: $DWC2_STATUS OctoPrint: $OCTOPRINT_STATUS"

    local menu
    menu=$(whiptail --title "$KIAUH_TITLE $KIAUH_VER" --cancel-button "Finish" --notags --menu "$menu_str\n\nChoose an option:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) install_menu ;;
				2) update_menu ;;
				3) remove_menu ;;
				4) advanced_menu ;;
				5) backup_menu ;;
				6) settings_menu ;;
				7) upload_selection ;;
				8) service_menu;;
			esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
	echo -e "${green}###### Happy printing! ######${default}"; echo
}
