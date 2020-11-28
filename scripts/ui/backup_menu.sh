backup_ui(){
  top_border
  echo -e "|     $(title_msg "~~~~~~~~~~~~~~ [ Backup Menu ] ~~~~~~~~~~~~~~")     | "
  hr
  echo -e "|           ${yellow}Backup location: ~/kiauh-backups${default}            | "
  hr
  echo -e "|  Firmware:                                            | "
  echo -e "|  1) [Klipper]                                         | "
  echo -e "|                                                       | "
  echo -e "|  Webinterface:                                        | "
  echo -e "|  2) [DWC2 Web UI]                                     | "
  echo -e "|                                                       | "
  echo -e "|  3) [Mainsail]                                        | "
  echo -e "|  4) [Moonraker]                                       | "
  echo -e "|                                                       | "
  echo -e "|  5) [OctoPrint]                                       | "
  echo -e "|                                                       | "
  echo -e "|  HDMI Screen:                                         | "
  echo -e "|  6) [KlipperScreen]                                   | "
  echo -e "|                                                       | "
  quit_footer
}

backup_menu(){
  print_header
  print_msg && clear_msg
  backup_ui
  while true; do
    read -p "${cyan}Perform action:${default} " action; echo
    case "$action" in
      1)
        clear
        print_header
        backup_klipper
        print_msg && clear_msg
        backup_ui;;
      2)
        clear
        print_header
        backup_dwc2
        print_msg && clear_msg
        backup_ui;;
      3)
        clear
        print_header
        backup_mainsail
        print_msg && clear_msg
        backup_ui;;
      4)
        clear
        print_header
        backup_moonraker
        print_msg && clear_msg
        backup_ui;;
      5)
        clear
        print_header
        backup_octoprint
        print_msg && clear_msg
        backup_ui;;
      6)
        clear
        print_header
        backup_klipperscreen
        print_msg && clear_msg
        backup_ui;;
      Q|q)
        clear; main_menu; break;;
      *)
        clear
        print_header
        print_unkown_cmd
        print_msg && clear_msg
        backup_ui;;
    esac
  done
  backup_menu
}
