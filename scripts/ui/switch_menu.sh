#!/bin/bash

switch_menu(){
  if [ -d $KLIPPER_DIR ]; then
    read_branch
    while true; do
      local menu_str="Active Branch: $GET_BRANCH"
      local menu_options=(
        "1" "Klipper3D - Official Klipper3D"
        "2" "dmbutyugin - dmbutyugin S-Curve Acceleration"
        "3" "Custom - Pick a custom branch"

      )
      local menu
      menu=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$menu_str\n\nSelect an option:"\
        "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
      local out=$?
      if [ $out -eq 1 ]; then
          break
      elif [ $out -eq 0 ]; then
        case "$menu" in
        1) switch_klipper3d_menu;;
        2) switch_dmbutyugin_menu ;;
        3) switch_custom_menu ;;
        esac
      else
          # Unexpected event, no clue what happened
        exit 1
      fi
    done
  else
    RROR_MSG="No Klipper directory found! Download Klipper first!"
  fi
}

switch_klipper3d_menu(){
  while true; do
    local menu_str="Active Branch: $GET_BRANCH"
    local menu_options=(
      "1" "Master"
      "2" "Custom"
    )
    local menu
    menu=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$menu_str\n\nSelect an option:"\
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
			1) switch_to_master
          read_branch
          print_msg && clear_msg;;
      2) echo "Not implemented" ;;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
  done
}

switch_dmbutyugin_menu(){
    while true; do
    local menu_str="Active Branch: $GET_BRANCH"
    local menu_options=(
      "1" "scurve_shaping - S-Curve Shaping"
      "2" "scurve_smoothing - S-Curve Smoothing"
    )
    local menu
    menu=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$menu_str\n\nSelect an option:"\
      "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8 "${menu_options[@]}" 3>&1 1>&2 2>&3)
    local out=$?
		if [ $out -eq 1 ]; then
				break
		elif [ $out -eq 0 ]; then
			case "$menu" in
			1) switch_to_scurve_shaping
          read_branch
          print_msg && clear_msg;;
      2) switch_to_scurve_smoothing
          read_branch
          print_msg && clear_msg;;
			esac
		else
				# Unexpected event, no clue what happened
			exit 1
		fi
  done
}
