#!/bin/bash

update_menu(){
  while true; do
    read_bb4u_stat
    compare_klipper_versions
    local menu_options=(
      "*" "$BB4U_STATUS"
      "Update All" ""
      "Klipper" "$LOCAL_COMMIT | $REMOTE_COMMIT"
      "Moonraker" "$LOCAL_MOONRAKER_COMMIT | $REMOTE_MOONRAKER_COMMIT"
      "Mainsail" "$MAINSAIL_LOCAL_VER | $MAINSAIL_REMOTE_VER"
      "Fliudd" "$FLUIDD_LOCAL_VER | $FLUIDD_REMOTE_VER"
      "KlipperScreen" "$LOCAL_KLIPPERSCREEN_COMMIT | $REMOTE_KLIPPERSCREEN_COMMIT"
      "DWC-for-Klipper" "$LOCAL_DWC2FK_COMMIT | $REMOTE_DWC2FK_COMMIT"
      "DWC2 Web UI" "$DWC2_LOCAL_VER | $DWC2_REMOTE_VER"
      "PrettyGCode" "$LOCAL_PGC_COMMIT | $REMOTE_PGC_COMMIT"
      "Telegram Bot" "$LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT | $REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT"
      "System" "$DISPLAY_SYS_UPDATE"
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
      "Klipper") do_action "update_klipper";;
      "Mooonraker") do_action "update_moonraker";;
      "Mainsail") do_action "update_mainsail";;
      "Fluidd") do_action "update_fluidd";;
      "KlipperScreen") do_action "update_klipperscreen";;
      "DWC-for-Klipper") do_action "update_dwc2fk";;
      "DWC2 Web UI") do_action "update_dwc2";;
      "PrettyGCode")do_action "update_pgc_for_klipper";;
      "Telegram Bot") do_action "update_MoonrakerTelegramBot";;
      "System") do_action "update_system";;
      "Update All") do_action "update_all";;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
