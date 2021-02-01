advanced_ui(){
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  0) $OPRINT_SERVICE_STATUS| "
  hr
  echo -e "|                           |                           | "
  echo -e "|  Klipper:                 |  System:                  | "
  echo -e "|  1) [Switch Version]      |  6) [Change hostname]     | "
  echo -e "|  2) [Rollback]            |                           | "
  echo -e "|                           |  Extensions:              | "
  echo -e "|  Firmware:                |  7) [Shell Command]       | "
  echo -e "|  3) [Build only]          |                           | "
  echo -e "|  4) [Build + Flash MCU]   |                           | "
  echo -e "|  5) [Get MCU ID]          |                           | "
  echo -e "|                           |                           | "
quit_footer
}

advanced_menu(){
  read_octoprint_service_status
  do_action "" "advanced_ui"
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      0)
        clear
        print_header
        toggle_octoprint_service
        read_octoprint_service_status
        print_msg && clear_msg
        advanced_ui;;
      1)
        do_action "switch_menu" "advanced_ui";;
      2)
        do_action "load_klipper_state" "advanced_ui";;
      3)
        do_action "build_fw" "advanced_ui";;
      4)
        clear
        print_header
        flash_routine
        if [ $FLASH_FIRMWARE = "true" ]; then
          ### build in a sleep to give the user a chance to have a look at the
          ### MCU IDs before directly starting to build the klipper firmware
          status_msg "Please wait..." && sleep 10 && build_fw
          flash_mcu
        fi
        print_msg && clear_msg
        advanced_ui;;
      5)
        do_action "get_mcu_id" "advanced_ui";;
      6)
        clear
        print_header
        create_custom_hostname && set_hostname
        print_msg && clear_msg
        advanced_ui;;
      7)
        do_action "setup_gcode_shell_command" "advanced_ui";;
      Q|q)
        clear; main_menu; break;;
      *)
        deny_action "advanced_ui";;
    esac
  done
  advanced_menu
}

#############################################################
#############################################################

switch_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~ [ Switch Klipper Branch ] ~~~~~~~~~")     |"
  bottom_border
  echo
  echo -e " $(title_msg "Active Branch: ")${green}$GET_BRANCH${default}"
  echo
  top_border
  echo -e "|                                                       | "
  echo -e "|  KevinOConnor:                                        | "
  echo -e "|  1) [--> master]                                      | "
  echo -e "|                                                       | "
  echo -e "|  dmbutyugin:                                          | "
  echo -e "|  2) [--> scurve-shaping]                              | "
  echo -e "|  3) [--> scurve-smoothing]                            | "
  quit_footer
}

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
        Q|q)
          clear; advanced_menu; break;;
        *)
          deny_action "switch_ui";;
      esac
    done
  else
    ERROR_MSG="No Klipper directory found! Download Klipper first!"
  fi
}

#############################################################
#############################################################

rollback_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~ [ Rollback Menu ] ~~~~~~~~~~~~~")     | "
  hr
  echo -e "|  If serious errors occured after updating Klipper,    | "
  echo -e "|  you can use this menu to return to the previously    | "
  echo -e "|  used commit from which you have updated.             | "
  bottom_border
  top_border
  echo -e "|  Active branch: ${green}$PRINT_BRANCH${default}                      | "
  hr
  echo -e "|  Currently on commit:                                 | "
  echo -e "|  $CURR_UI                             | "
  hr
  echo -e "|  Commit last updated from:                            | "
  echo -e "|  $PREV_UI                             | "
  quit_footer
}
