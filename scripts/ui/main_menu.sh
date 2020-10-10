main_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|  0) [Upload Log]     |    Klipper: $KLIPPER_STATUS|"
  echo -e "|                      |     Branch: ${cyan}$PRINT_BRANCH${default}|"
  echo -e "|  1) [Install]        |                                |"
  echo -e "|  2) [Update]         |  Moonraker: $MOONRAKER_STATUS|"
  echo -e "|  3) [Remove]         |                                |"
  echo -e "|                      |       DWC2: $DWC2_STATUS|"
  echo -e "|  4) [Advanced]       |     Fluidd: $FLUIDD_STATUS|"
  echo -e "|  5) [Backup]         |   Mainsail: $MAINSAIL_STATUS|"
  echo -e "|                      |  Octoprint: $OCTOPRINT_STATUS|"
  quit_footer
}

main_menu(){
  print_header
  #print KIAUH update msg if update available
    if [ "$KIAUH_UPDATE_AVAIL" = "true" ]; then
      kiauh_update_msg
    fi
  #check install status
    klipper_status
    moonraker_status
    dwc2_status
    fluidd_status
    mainsail_status
    octoprint_status
    print_branch
  print_msg && clear_msg
  main_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      update)
        clear
        print_header
        update_kiauh
        print_msg && clear_msg
        main_ui;;
      0)
        clear
        print_header
        upload_selection
        print_msg && clear_msg
        main_ui;;
      1)
        clear
        install_menu
        break;;
      2)
        clear
        update_menu
        break;;
      3)
        clear
        remove_menu
        break;;
      4)
        clear
        advanced_menu
        break;;
      5)
        clear
        backup_menu
        break;;
      Q|q)
        echo -e "${green}###### Happy printing! ######${default}"; echo
        exit -1;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        main_ui;;
    esac
  done
  clear; main_menu
}
