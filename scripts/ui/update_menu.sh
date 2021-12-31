#!/bin/bash


update_menu(){
  check_updates
  while true; do
    read_bb4u_stat
    local menu_options=(
      "*" "$BB4U_STATUS"
      "Update All" ""
      "${READABLE_NAMES[$KLIPPER]}" "${update_message[$KLIPPER]}"
      "${READABLE_NAMES[$MOONRAKER]}" "${update_message[$MOONRAKER]}"
      "${READABLE_NAMES[$MAINSAIL]}" "${update_message[$MAINSAIL]}"
      "${READABLE_NAMES[$FLUIDD]}" "${update_message[$FLUIDD]}"
      "${READABLE_NAMES[$KLIPPERSCREEN]}" "${update_message[$KLIPPERSCREEN]}"
      "${READABLE_NAMES[$DWC2FK]}" "${update_message[$DWC2FK]}"
      "${READABLE_NAMES[$DWC2]}" "${update_message[$DWC2]}"
      "${READABLE_NAMES[$PGC]}" "${update_message[$PGC]}"
      "${READABLE_NAMES[$MOONRAKER_TELEGRAM_BOT]}" "${update_message[$MOONRAKER_TELEGRAM_BOT]}"
      "${READABLE_NAMES[$SYSTEM]}" "$DISPLAY_SYS_UPDATE"
    )
    local menu_str=""
    menu=$(whiptail --title "Update Menu" --cancel-button "Back" --menu "$menu_str\n\nPerform Action:"\
			"$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 12 "${menu_options[@]}" 3>&1 1>&2 2>&3)

		local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
      "*") do_action "toggle_backups";;
      "Update All") update_all_yesno;;
      "${READABLE_NAMES[$KLIPPER]}") do_action "update_klipper" && check_updates;;
      "${READABLE_NAMES[$MOONRAKER]}") do_action "update_moonraker" && check_updates;;
      "${READABLE_NAMES[$MAINSAIL]}") do_action "update_mainsail" && check_updates;;
      "${READABLE_NAMES[$FLUIDD]}") do_action "update_fluidd" && check_updates;;
      "${READABLE_NAMES[$KLIPPERSCREEN]}") do_action "update_klipperscreen" && check_updates;;
      "${READABLE_NAMES[$DWC2FK]}") do_action "update_dwc2fk" && check_updates;;
      "${READABLE_NAMES[$DWC2]}") do_action "update_dwc2" && check_updates;;
      "${READABLE_NAMES[$PGC]}")do_action "update_pgc_for_klipper" && check_updates;;
      "${READABLE_NAMES[$MOONRAKER_TELEGRAM_BOT]}") do_action "update_MoonrakerTelegramBot" && check_updates;;
      "${READABLE_NAMES[$SYSTEM]}") do_action "update_system" && check_updates;;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
