#!/bin/bash

switch_ui(){
  SWITCH_MENU_STR="Active Branch: $GET_BRANCH"
  SWITCH_MENU=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$SWITCH_MENU_STR\n\nSelect a Branch Owner:"\
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8\
    "1 Klipper3D" "Official Klipper3D"\
    "2 dmbutyugin" "dmbutyugin S-Curve Acceleration"\
    "3 Custom" "Pick a custom branch" 3>&1 1>&2 2>&3)

  OUT=$SWITCH_MENU
  case "$OUT" in
    1\ *) Something;;
    2\ *) install_menu ;;
    3\ *) echo "Custom Branch" ;;
  esac

  KILPPER3D_MENU_STR="Active Branch: $GET_BRANCH"
  KILPPER3D_MENU=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$KILPPER3D_MENU_STR\n\nSelect a Branch:"\
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8\
    "1 master" "Official Klipper with rolling update")

  OUT=$KILPPER3D_MENU
  case "$OUT" in
    1\ *) Something;;
  esac

  DMBUTYUGIN_MENU_STR="Active Branch: $GET_BRANCH"
  DMBUTYUGIN_MENU=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --menu "$DMBUTYUGIN_MENU\n\nSelect a Branch:"\
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" 8\
    "1 scurve-shaping" "Official Klipper with rolling update"\
    "2 scurve-smoothing" "Pick a custom branch/tag" 3>&1 1>&2 2>&3)

  OUT=$DMBUTYUGIN_MENU
  case "$OUT" in
    1\ *) Something;;
    2\ *) install_menu ;;
  esac


  CUSTOM_BRANCH_MENU_MENU=$(whiptail --title "Switch Klipper Branch" --cancel-button "Back" --inputbox "Paste the link of a Klipper Git repository:"\
    "$KIAUH_WHIPTAIL_NORMAL_HEIGHT" "$KIAUH_WHIPTAIL_NORMAL_WIDTH" "github.com/Klipper3d/klipper" 3>&1 1>&2 2>&3)

  OUT=$CUSTOM_BRANCH_MENU_MENU
  case "$OUT" in
    1\ *) Something;;
    2\ *) install_menu ;;
  esac
}
# TODO Automatically list the available branches of an account or allow type in custom

switch_menu(){
  if [ -d $KLIPPER_DIR ]; then
    read_branch
    do_action "" "switch_ui"
    while true; do
      read -p "${cyan}Perform action:${default} " action; echo
      case "$action" in
        1)
          clear
          print_header
          switch_to_master
          read_branch
          print_msg && clear_msg
          switch_ui;;
        2)
          clear
          print_header
          switch_to_scurve_shaping
          read_branch
          print_msg && clear_msg
          switch_ui;;
        3)
          clear
          print_header
          switch_to_scurve_smoothing
          read_branch
          print_msg && clear_msg
          switch_ui;;
        4)
          clear
          print_header
          switch_to_moonraker
          read_branch
          print_msg && clear_msg
          switch_ui;;
        B|b)
          clear; advanced_menu; break;;
        *)
          deny_action "switch_ui";;
      esac
    done
  else
    ERROR_MSG="No Klipper directory found! Download Klipper first!"
  fi
}
