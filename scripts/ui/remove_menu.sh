#!/bin/bash

remove_menu(){
  local menu_options=(
    "${READABLE_NAMES["$KLIPPER"]}" "PLACEHOLDER"
    "API:" "============================="
    "${READABLE_NAMES["$MOONRAKER"]}" "PLACEHOLDER"
    "Interfaces:" "============================="
    "${READABLE_NAMES["$MAINSAIL"]}" "lightweight & responsive web interface"
    "${READABLE_NAMES["$FLUIDD"]}" "Klipper web interface"
    "${READABLE_NAMES["$KLIPPERSCREEN"]}" "a touchscreen GUI"
    "${READABLE_NAMES["$DWC"]}" "web interface for RepRapFirmware"
    "${READABLE_NAMES["$OCTOPRINT"]}" "a snappy web interface"
    "Add-Ons:" "============================="
    "${READABLE_NAMES["$PGC"]}" "PLACEHOLDER"
    "${READABLE_NAMES["$MOONRAKER_TELEGRAM_BOT"]}" "PLACEHOLDER"
    "${READABLE_NAMES["$MJPG_STREAMER"]}" "Use webcam in Fluidd and Mainsail"
    "${READABLE_NAMES["$NGINX"]}" "PLACEHOLDER"
  )
  local menu_str="Directories which remain untouched:

Your printer configuration directory
~/kiauh-backups

You need remove them manually if you wish so."

  while true; do
    local menu
    menu=$(whiptail --title "Remove Menu" --cancel-button "Back" --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 14 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
    	break
    elif [ $out -eq 0 ]; then
		case "$menu" in
      "${READABLE_NAMES["$KLIPPER"]}") do_action "remove_klipper" ;;
      "${READABLE_NAMES["$MOONRAKER"]}") do_action "remove_moonraker" ;;
      "${READABLE_NAMES["$MAINSAIL"]}") do_action "remove_mainsail";;
      "${READABLE_NAMES["$FLUIDD"]}") do_action "remove_fluidd";;
      "${READABLE_NAMES["$KLIPPERSCREEN"]}") do_action "remove_klipperscreen";;
      "${READABLE_NAMES["$DWC"]}") do_action "remove_dwc2";;
      "${READABLE_NAMES["$OCTOPRINT"]}") do_action "remove_octoprint";;
			"${READABLE_NAMES["$PGC"]}") do_action "remove_pgc_for_klipper";;
      "${READABLE_NAMES["$MOONRAKER_TELEGRAM_BOT"]}") do_action "remove_MoonrakerTelegramBot";;
      "${READABLE_NAMES["$MJPG_STREAMER"]}") do_action "remove_mjpg-streamer";;
    	"${READABLE_NAMES["$NGINX"]}") do_action "remove_nginx";;
		esac
	else
		# Unexpected event, no clue what happened
		exit 1
	fi
  done
}
