#!/bin/bash

update_menu(){
  while true; do
    read_bb4u_stat
		#TODO Update the commit message
		#TODO Align all the local/remote versions
    local menu_options=(
      "0" "$BB4U_STATUS"
      "a" "Update All"
      "1" "Klipper - $LOCAL_COMMIT | $REMOTE_COMMIT"
      "2" "Moonraker - $LOCAL_MOONRAKER_COMMIT | $REMOTE_MOONRAKER_COMMIT"
      "3" "Mainsail $MAINSAIL_LOCAL_VER | $MAINSAIL_REMOTE_VER"
      "4" "Fliuidd $FLUIDD_LOCAL_VER | $FLUIDD_REMOTE_VER"
      "5" "KlipperScreen $LOCAL_KLIPPERSCREEN_COMMIT | $REMOTE_KLIPPERSCREEN_COMMIT"
      "6" "DWC-for-Klipper $LOCAL_DWC2FK_COMMIT | $REMOTE_DWC2FK_COMMIT"
      "7" "DWC2 Web UI - $DWC2_LOCAL_VER | $DWC2_REMOTE_VER"
      "8" "PrettyGCode - $LOCAL_PGC_COMMIT | $REMOTE_PGC_COMMIT"
      "9" "Telegram Bot - $LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT | $REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT"
      "10" "System - $DISPLAY_SYS_UPDATE"
    )
    local menu_str=""
    menu=$(whiptail --title "Update Menu" --cancel-button "Back" --notags --menu "$menu_str\n\nPerform Action:"\
			"$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 12 "${menu_options[@]}" 3>&1 1>&2 2>&3)

		local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
      0) do_action "toggle_backups";;
      1) do_action "update_klipper";;
      2) do_action "update_moonraker";;
      3) do_action "update_mainsail";;
      4) do_action "update_fluidd";;
      5) do_action "update_klipperscreen";;
      6) do_action "update_dwc2fk";;
      7) do_action "update_dwc2";;
      8) do_action "update_pgc_for_klipper";;
      9) do_action "update_MoonrakerTelegramBot";;
      10) do_action "update_system";;
      a) do_action "update_all";;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
