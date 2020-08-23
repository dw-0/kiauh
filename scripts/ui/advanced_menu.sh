advanced_ui(){
  top_border
  echo -e "|     ${yellow}~~~~~~~~~~~~~ [ Advanced Menu ] ~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  0) $OPRINT_SERVICE_STATUS| "
  hr
  echo -e "|                           |                           | "
  echo -e "|  Klipper:                 |  System:                  | "
  echo -e "|  1) [Switch Version]      |  8) [Change hostname]     | "
  echo -e "|  2) [Rollback]            |                           | "
  echo -e "|                           |  Mainsail:                | "
  echo -e "|  Firmware:                |  9) [Remove branding]     | "
  echo -e "|  3) [Build Firmware]      |                           | "
  echo -e "|  4) [Flash MCU]           |  Extensions:              | "
  echo -e "|  5) [Get Printer-USB]     |  10) [Shell Command]      | "
  echo -e "|  6) [Write Printer-USB]   |                           | "
  echo -e "|  7) [Write DWC2 config]   |                           | "
  echo -e "|                           |                           | "
quit_footer
}

advanced_menu(){
  print_header
  print_msg && clear_msg
  read_octoprint_service_status
  advanced_ui
  while true; do
    echo -e "${cyan}"
    read -p "Perform action: " action; echo
    echo -e "${default}"
    case "$action" in
      0)
        clear
        print_header
        toggle_octoprint_service
        read_octoprint_service_status
        print_msg && clear_msg
        advanced_ui;;
      1)
        clear
        print_header
        switch_menu
        print_msg && clear_msg
        advanced_ui;;
      2)
        clear
        print_header
        load_klipper_state
        print_msg && clear_msg
        advanced_ui;;
      3)
        clear
        print_header
        build_fw
        print_msg && clear_msg
        advanced_ui;;
      4)
        clear
        print_header
        flash_routine
        print_msg && clear_msg
        advanced_ui;;
      5)
        clear
        print_header
        get_printer_usb
        print_msg && clear_msg
        advanced_ui;;
      6)
        clear
        print_header
        get_printer_usb && write_printer_usb
        print_msg && clear_msg
        advanced_ui;;
      7)
        clear
        print_header
        create_dwc2fk_cfg
        print_msg && clear_msg
        advanced_ui;;
      8)
        clear
        print_header
        create_custom_hostname
        print_msg && clear_msg
        advanced_ui;;
      9)
        clear
        print_header
        remove_branding
        print_msg && clear_msg
        advanced_ui;;
      10)
        clear
        print_header
        install_extension_shell_command
        print_msg && clear_msg
        advanced_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        advanced_ui;;
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
  echo -e "|  1) [--> origin/master]                               | "
  echo -e "|                                                       | "
  echo -e "|  2) [--> scurve-shaping]                              | "
  echo -e "|  3) [--> scurve-smoothing]                            | "
  echo -e "|                                                       | "
  echo -e "|  4) [--> moonraker]                                   | "
  quit_footer
}

switch_menu(){
  if [ -d $KLIPPER_DIR ]; then
    read_branch
    print_msg && clear_msg
    switch_ui
    while true; do
      echo -e "${cyan}"
      read -p "Perform action: " action; echo
      echo -e "${default}"
      case "$action" in
        1)
          clear
          print_header
          switch_to_origin
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
          clear
          print_header
          print_unkown_cmd
          print_msg && clear_msg
          switch_ui;;
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
  echo -e "|  Active branch: ${green}$PRINT_BRANCH${default}                   | "
  hr
  echo -e "|  Currently on commit:                                 | "
  echo -e "|  $CURR_UI                             | "
  hr
  echo -e "|  Commit last updated from:                            | "
  echo -e "|  $PREV_UI                             | "
  quit_footer
}
