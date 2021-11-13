#!/bin/bash
#
# Brief description of your script

install_other_menu(){

	local menu_options=(
		#TODO WIP
		"1" "PrettyGCode - "
		"2" "Klipper Telegram Bot - "
		"3" "Webcam MJPG-Streamer - Use MJPG-Streamer with webcam"
	)
  local menu_str="Select an option to install."

  while true; do
    local menu
    menu=$(whiptail --title "Install Other" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
        1) do_action "install_pgc_for_klipper";;
      	2) do_action "install_MoonrakerTelegramBot";;
      	3) do_action "install_mjpg-streamer";;
				esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
