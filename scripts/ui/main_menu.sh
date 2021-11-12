#!/bin/bash

print_kiauh_version() {
  cd ${SRCDIR}/kiauh
  KIAUH_VER=$(git describe HEAD --always --tags | cut -d "-" -f 1,2)
  KIAUH_VER="$(printf "%-20s" "$KIAUH_VER")"
}

#######################################
# description Advise user to update KIAUH
# Globals:
#   KIAUH_WHIPTAIL_NORMAL_HEIGHT
#   KIAUH_WHIPTAIL_NORMAL_WIDTH
#   RET
# Arguments:
#  None
#######################################
kiauh_update_dialog() {
  whiptail --title "New KIAUH update available!" \
    --yesno \
    "View Changelog: https://git.io/JnmlX

It is recommended to keep KIAUH up to date. Updates usually contain bugfixes, \
important changes or new features. Please consider updating!

Do you want to update now?" \
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH"

  local out=$?
  if [ $out -eq 0 ]; then
    do_action "update_kiauh"
  else
    deny_action "kiauh_update_dialog"
  fi
}

main_menu() {
  #print KIAUH update msg if update available
  if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
    kiauh_update_dialog
  fi
  #check install status
  print_kiauh_version
  klipper_status
  moonraker_status
  dwc2_status
  fluidd_status
  mainsail_status
  octoprint_status
  klipperscreen_status
  MoonrakerTelegramBot_status
  print_branch
  print_msg && clear_msg

  while true; do
    local menu_str="Klipper: $KLIPPER_STATUS Branch: $PRINT_BRANCH\n
Moonraker: $MOONRAKER_STATUS\n
Mainsail: $MAINSAIL_STATUS Fluidd: $FLUIDD_STATUS
KlipperScreen: $KLIPPERSCREEN_STATUS Telegram Bot: $MOONRAKER_TELEGRAM_BOT_STATUS
DWC2: $DWC2_STATUS OctoPrint: $OCTOPRINT_STATUS"
    local menu_choices=("1" "Install" "2" "Update" "3" "Remove" "4" "Advanced Settings" "5" "Backup" "6" "Settings" "7" "Upload Log" "8" "Service")
    local menu
    menu=$(whiptail --title "$KIAUH_TITLE $KIAUH_VER" --cancel-button "Finish" --notags --menu "$menu_str\n\nChoose an option:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_choices[@]}" 3>&1 1>&2 2>&3)
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
