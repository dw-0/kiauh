#!/bin/bash

service_menu(){
	#TODO Read service status
	#TODO use start/start restart and enable/disable to improve user exp
    	local menu_options=(
		"1" "Start Klipper"
		"2" "Stop Klipper"
        "3" "Restart Klipper"
        "4" "Start Moonraker"
        "5" "Stop Moonraker"
        "6" "Restart Moonraker"
        "7" "Start Duet Web Control"
        "8" "Stop Duet Web Control"
        "9" "Restart Duet Web Control"
        "10" "Start Octoprint"
        "11" "Stop Octoprint"
        "12" "Restart Octoprint"
		)

  local menu_str="Start/stop/restart services"

  while true; do
    local menu
    menu=$(whiptail --title "Service Menu" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
			case "$menu" in
				1) do_action_service "start" "klipper";;
				2) do_action_service "stop" "klipper";;
				3) do_action_service "restart" "klipper";;
				4) do_action_service "start" "moonraker";;
				5) do_action_service "stop" "moonraker";;
				6) do_action_service "restart" "moonraker";;
				7)do_action_service "start" "dwc";;
				8)do_action_service "stop" "dwc";;
				9)do_action_service "restart" "dwc";;
				10)do_action_service "start" "octoprint";;
				11)do_action_service "stop" "octoprint";;
				12)do_action_service "restart" "octoprint";;
			esac
		else
			# Unexpected event, no clue what happened
			exit 1
		fi
  done
}