#!/bin/bash

install_menu() {
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
  )
  local menu_str="You need this menu usually only for installing all necessary dependencies for the various functions on a completely fresh system."

  while true; do
    local menu
    menu=$(whiptail --title "Install" --cancel-button "Back" --menu "$menu_str\n\nPerform Action:" \
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 14 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
    if [ $out -eq 1 ]; then
      break
    elif [ $out -eq 0 ]; then
      case "$menu" in
        "${READABLE_NAMES["$KLIPPER"]}") do_action "klipper_setup_dialog" ;;
        "${READABLE_NAMES["$MOONRAKER"]}") do_action "moonraker_setup_dialog" ;;
        "${READABLE_NAMES["$MAINSAIL"]}") do_action "install_webui mainsail" ;;
        "${READABLE_NAMES["$FLUIDD"]}") do_action "install_webui fluidd" ;;
        "${READABLE_NAMES["$KLIPPERSCREEN"]}") do_action "install_klipperscreen" ;;
        "${READABLE_NAMES["$DWC"]}") do_action "dwc_setup_dialog" ;;
        "${READABLE_NAMES["$OCTOPRINT"]}") do_action "octoprint_setup_yesno" ;;
				"${READABLE_NAMES["$PGC"]}") do_action "install_pgc_for_klipper";;
      	"${READABLE_NAMES["$MOONRAKER_TELEGRAM_BOT"]}") do_action "install_MoonrakerTelegramBot";;
      	"${READABLE_NAMES["$MJPG_STREAMER"]}") do_action "install_mjpg-streamer";;
      esac
    else
      # Unexpected event, no clue what happened
      exit 1
    fi
  done
}
