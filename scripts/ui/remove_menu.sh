remove_ui(){
  top_border
  echo -e "|     ${red}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~${default}     | "
  hr
  echo -e "|  Files and directories which remain untouched:        | "
  echo -e "|  --> ~/printer.cfg                                    | "
  echo -e "|  --> ~/klipper_config                                 | "
  echo -e "|  --> ~/kiauh-backups                                  | "
  echo -e "|  You need remove them manually if you wish so.        | "
  hr
  echo -e "|  Firmware:             |  Webinterface:               | "
  echo -e "|  1) [Klipper]          |  3) [DWC2]                   | "
  echo -e "|                        |  4) [Mainsail]               | "
  echo -e "|  Klipper API:          |  5) [Octoprint]              | "
  echo -e "|  2) [Moonraker]        |                              | "
  echo -e "|                        |  Webserver:                  | "
  echo -e "|                        |  6) [Nginx]                  | "
  quit_footer
}

remove_menu(){
  print_header
  remove_ui
  while true; do
    echo -e "${cyan}"
    read -p "Perform action: " action; echo
    echo -e "${default}"
    case "$action" in
      1)
        clear
        print_header
        remove_klipper
        print_msg && clear_msg
        remove_ui;;
      2)
        clear
        print_header
        remove_moonraker
        print_msg && clear_msg
        remove_ui;;
      3)
        clear
        print_header
        remove_dwc2
        print_msg && clear_msg
        remove_ui;;
      4)
        clear
        print_header
        remove_mainsail
        print_msg && clear_msg
        remove_ui;;
      5)
        clear
        print_header
        remove_octoprint
        print_msg && clear_msg
        remove_ui;;
      6)
        clear
        print_header
        remove_nginx
        print_msg && clear_msg
        remove_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        remove_ui;;
    esac
  done
  remove_menu
}
