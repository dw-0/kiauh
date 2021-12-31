#!/bin/bash
settings_menu(){
  source_kiauh_ini
  if [ -z $klipper_cfg_loc ]; then
    local warn="Install Klipper with KIAUH first to unlock!"
    local ok="Back"
    local go_back="true"
  else
    local warn="When you change the config folder, be aware that ALL Klipper and Moonraker \
services will be STOPPED, \
reconfigured and then restarted again.

DO NOT change the folder during printing!

Current Klipper config folder:
$klipper_cfg_loc"
    local ok="I understand"
    local go_back="false"
  fi

  whiptail --title "WARNING:" --ok-button "$ok" --msgbox "$warn" 12 $KIAUH_WHIPTAIL_NORMAL_WIDTH
  if [ $go_back == "false" ]; then
    while true; do
      source_kiauh_ini
      local menu=( "1" "Change config folder" )

      menu=$(whiptail --title "Kiauh Settings" --cancel-button "Back" --ok-button "$ok" --notags --menu "$warn" \
        20 "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 6 "${menu[@]}" 3>&1 1>&2 2>&3)

      local out=$?

      if [ $out -eq 1 ]; then
        break
      elif [ $out -eq 0 ]; then
        case "$menu" in
          "1") do_action "change_klipper_cfg_path";;
        esac
      else
          # Unexpected event, no clue what happened
        exit 1
      fi
    done
  fi
}
