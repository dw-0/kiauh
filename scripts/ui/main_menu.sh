main_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~")     |"
  hr
  echo -e "|                      |                                |"
  echo -e "|  1) [Install]        |    Klipper: $KLIPPER_STATUS|"
  echo -e "|  2) [Update]         |     Branch: ${cyan}$PRINT_BRANCH${default}|"
  echo -e "|  3) [Remove]         |                                |"
  echo -e "|                      |       DWC2: $DWC2_STATUS|"
  echo -e "|  4) [Advanced]       |   Mainsail: $MAINSAIL_STATUS|"
  echo -e "|  5) [Backup]         |  Octoprint: $OCTOPRINT_STATUS|"
  echo -e "|                      |                                |"
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
    dwc2_status
    mainsail_status
    octoprint_status
    print_branch
  print_msg && clear_msg
  main_ui
  while true; do
    echo -e "${cyan}"
    read -p "Perform action: " action; echo
    echo -e "${default}"
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
        ERROR_MSG="Sorry this function is not implemented yet!"
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
