advanced_ui(){
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~${default}     | "
  hr
  if [ ! "$OPRINT_SERVICE_STATUS" == "" ]; then
    echo -e "|  0) $OPRINT_SERVICE_STATUS| "
    hr
    echo -e "|                           |                           | "
  fi
  echo -e "|  Klipper:                 |  Mainsail:                | "
  echo -e "|  1) [Switch Branch]       |  7) [Theme installer]     | "
  echo -e "|  2) [Rollback]            |                           | "
  echo -e "|                           |  System:                  | "
  echo -e "|  Firmware:                |  8) [Change hostname]     | "
  echo -e "|  3) [Build only]          |                           | "
  echo -e "|  4) [Flash only]          |  Extensions:              | "
  echo -e "|  5) [Build + Flash]       |  9) [Shell Command]       | "
  echo -e "|  6) [Get MCU ID]          |                           | "
  echo -e "|                           |  CustomPiOS:              | "
  echo -e "|                           |  10) [Migration Helper]   | "
back_footer
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
        do_action "switch_menu";;
      2)
        do_action "load_klipper_state" "advanced_ui";;
      3)
        do_action "build_fw" "advanced_ui";;
      4)
        do_action "select_flash_method" "advanced_ui";;
      5)
        clear && print_header
        status_msg "Please wait..."
        build_fw
        select_flash_method
        print_msg && clear_msg
        advanced_ui;;
      6)
        do_action "select_mcu_connection" "advanced_ui";;
      7)
        do_action "ms_theme_menu";;
      8)
        clear
        print_header
        create_custom_hostname && set_hostname
        print_msg && clear_msg
        advanced_ui;;
      9)
        do_action "setup_gcode_shell_command" "advanced_ui";;
      10)
        do_action "migration_menu";;
      B|b)
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
  back_footer
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

#############################################################
#############################################################

migration_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~ [ CustomPiOS Migration ] ~~~~~~~~~~")     | "
  hr
  echo -e "|  This function will help you to migrate a vanilla     | "
  echo -e "|  MainsailOS or FluiddPi image to a newer state.       | "
  blank_line
  echo -e "|  Only use this function if you use MainsailOS 0.4.0   | "
  echo -e "|  or lower, or FluiddPi v1.13.0 or lower.              | "
  blank_line
  echo -e "|  Please have a look at the KIAUH changelog for more   | "
  echo -e "|  details on what this function will do.               | "
  hr
  echo -e "|                                                       | "
  echo -e "|  1) [Migrate MainsailOS]                              | "
  echo -e "|  2) [Migrate FluiddPi]                                | "
  echo -e "|                                                       | "
  back_footer
}

migration_menu(){
  print_msg && clear_msg
  migration_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1) migrate_custompios "mainsail"; migration_menu;;
      2) migrate_custompios "fluiddpi"; migration_menu;;
      B|b) clear; advanced_menu; break;;
      *) print_unkown_cmd; migration_menu;;
    esac
  done
}
