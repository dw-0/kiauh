#!/bin/bash

update_menu(){
  while true; do
    read_bb4u_stat
    ui_print_versions
    local menu_options=(
      "*" "$BB4U_STATUS"
      "Update All" ""
      "$KLIPPER" "$LOCAL_COMMIT | $REMOTE_COMMIT"
      "$MOONRAKER" "$LOCAL_MOONRAKER_COMMIT | $REMOTE_MOONRAKER_COMMIT"
      "$MAINSAIL" "$MAINSAIL_LOCAL_VER | $MAINSAIL_REMOTE_VER"
      "$FLUIDD" "$FLUIDD_LOCAL_VER | $FLUIDD_REMOTE_VER"
      "$KLIPPERSCREEN" "$LOCAL_KLIPPERSCREEN_COMMIT | $REMOTE_KLIPPERSCREEN_COMMIT"
      "$DWC2FK" "$LOCAL_DWC2FK_COMMIT | $REMOTE_DWC2FK_COMMIT"
      "$DWC2" "$DWC2_LOCAL_VER | $DWC2_REMOTE_VER"
      "$PGC" "$LOCAL_PGC_COMMIT | $REMOTE_PGC_COMMIT"
      "$MOONRAKER_TELEGRAM_BOT" "$LOCAL_MOONRAKER_TELEGRAM_BOT_COMMIT | $REMOTE_MOONRAKER_TELEGRAM_BOT_COMMIT"
      "$SYSTEM" "$DISPLAY_SYS_UPDATE"
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
      "Update All") do_action "update_all";;
      "$KLIPPER") do_action "update_klipper";;
      "$MOONRAKER") do_action "update_moonraker";;
      "$MAINSAIL") do_action "update_mainsail";;
      "$FLUIDD") do_action "update_fluidd";;
      "$KLIPPERSCREEN") do_action "update_klipperscreen";;
      "$DWC2FK") do_action "update_dwc2fk";;
      "$DWC2") do_action "update_dwc2";;
      "$PGC")do_action "update_pgc_for_klipper";;
      "$MOONRAKER_TELEGRAM_BOT") do_action "update_MoonrakerTelegramBot";;
      "$SYSTEM") do_action "update_system";;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
	done
}
